"""Read-only regional renderer for the current Noronha satellite and mask."""

from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
from typing import Any
import warnings

import numpy as np
from PIL import Image, ImageFilter

from .inspect import InspectionError, _color_aliases, _input_paths, _world_size, load_preset
from .parsers import parse_layers
from .preview import PreviewRequest
from .procedural import stable_seed, value_noise
from .safety import write_bytes_atomic


MAX_REAL_PIXELS = 2048 * 2048


class RealPreviewError(ValueError):
    """A real-preview request cannot be rendered safely."""


@dataclass(frozen=True)
class Recipe:
    name: str
    base_rgb: tuple[int, int, int]
    macro_strength: float
    medium_strength: float
    local_strength: float
    blend_strength: float


@dataclass(frozen=True)
class Variant:
    name: str
    structure_weight: float
    detail_weight: float
    recipe_weight: float


@dataclass(frozen=True)
class RealPreviewPreset:
    path: Path
    world_size_m: tuple[float, float]
    inputs: dict[str, Path]
    aliases: dict[tuple[int, int, int], str]
    surface_rgb: dict[tuple[int, int, int], str]
    recipes: dict[str, Recipe]
    variants: dict[str, Variant]
    world_seed: str
    structure_blur_radius_px: int


@dataclass(frozen=True)
class RealPreviewResult:
    original: np.ndarray
    structure: np.ndarray
    recipe: np.ndarray
    mask_resolved: np.ndarray
    combined: np.ndarray
    variant: str
    mask_mode: str


def _rgb(value: Any, *, label: str) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3 or any(
        not isinstance(channel, int) or channel < 0 or channel > 255 for channel in value
    ):
        raise RealPreviewError(f"{label} must be three RGB bytes")
    return tuple(value)  # type: ignore[return-value]


def _number(value: Any, *, label: str, minimum: float = 0) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < minimum:
        raise RealPreviewError(f"{label} must be a number >= {minimum:g}")
    return float(value)


def load_real_preview_preset(path: Path) -> RealPreviewPreset:
    """Load only the compact, explicit recipe model needed for real previews."""
    raw = load_preset(path)
    config = raw.get("real_preview")
    if not isinstance(config, dict):
        raise RealPreviewError("real-preview requires a [real_preview] table")
    allowed = {"world_seed", "structure_blur_radius_px", "variants", "recipes"}
    unexpected = sorted(set(config) - allowed)
    if unexpected:
        raise RealPreviewError("Unknown [real_preview] keys: " + ", ".join(unexpected))
    variants_raw = config.get("variants")
    recipes_raw = config.get("recipes")
    if not isinstance(variants_raw, dict) or not isinstance(recipes_raw, dict):
        raise RealPreviewError("real_preview requires [real_preview.variants] and [real_preview.recipes]")
    variants: dict[str, Variant] = {}
    for name in ("subtle", "balanced", "authored"):
        item = variants_raw.get(name)
        if not isinstance(item, dict):
            raise RealPreviewError(f"real_preview is missing variant {name}")
        weights = tuple(
            _number(item.get(key), label=f"variant {name} {key}")
            for key in ("structure_weight", "detail_weight", "recipe_weight")
        )
        if not np.isclose(sum(weights), 1.0):
            raise RealPreviewError(f"variant {name} weights must sum to 1")
        variants[name] = Variant(name, *weights)
    recipes: dict[str, Recipe] = {}
    for name, item in recipes_raw.items():
        if not isinstance(item, dict):
            raise RealPreviewError(f"recipe {name} must be a table")
        blend_strength = _number(item.get("blend_strength", 1.0), label=f"recipe {name} blend_strength")
        if blend_strength > 1:
            raise RealPreviewError(f"recipe {name} blend_strength must be <= 1")
        recipes[name] = Recipe(
            name,
            _rgb(item.get("base_rgb"), label=f"recipe {name} base_rgb"),
            _number(item.get("macro_strength"), label=f"recipe {name} macro_strength"),
            _number(item.get("medium_strength"), label=f"recipe {name} medium_strength"),
            _number(item.get("local_strength"), label=f"recipe {name} local_strength"),
            blend_strength,
        )
    surfaces = parse_layers(Path(raw["inputs"]["layers"]))
    aliases = _color_aliases(raw["mask"], surfaces)
    return RealPreviewPreset(
        path=path,
        world_size_m=_world_size(raw["world"]["size_m"]),
        inputs=_input_paths(raw),
        aliases=aliases,
        surface_rgb={surface.rgb: surface.name for surface in surfaces},
        recipes=recipes,
        variants=variants,
        world_seed=str(config.get("world_seed", "terrain-satgen-real-preview")),
        structure_blur_radius_px=int(_number(config.get("structure_blur_radius_px", 12), label="structure_blur_radius_px", minimum=1)),
    )


def _request_box(preset: RealPreviewPreset, request: PreviewRequest, satellite_size: tuple[int, int]) -> tuple[int, int, int, int]:
    if request.tile_size_px <= 0:
        raise RealPreviewError("tile size must be positive")
    if min(request.width_m, request.height_m, request.meters_per_pixel) <= 0:
        raise RealPreviewError("width, height and meters-per-pixel must be positive")
    source_mpp_x = preset.world_size_m[0] / satellite_size[0]
    source_mpp_y = preset.world_size_m[1] / satellite_size[1]
    if not np.isclose(source_mpp_x, source_mpp_y) or not np.isclose(request.meters_per_pixel, source_mpp_x):
        raise RealPreviewError("real-preview meters-per-pixel must match the registered source raster")
    width = round(request.width_m / request.meters_per_pixel)
    height = round(request.height_m / request.meters_per_pixel)
    left = round(request.x_m / request.meters_per_pixel)
    # Terrain Builder world Y starts at the lower edge; image rows start at the
    # upper edge. A regional world box [y, y + height) therefore maps to this
    # top-down raster interval without changing the registered world space.
    top = satellite_size[1] - round((request.y_m + request.height_m) / request.meters_per_pixel)
    if not np.isclose(left * request.meters_per_pixel, request.x_m) or not np.isclose(
        (satellite_size[1] - top - height) * request.meters_per_pixel, request.y_m
    ):
        raise RealPreviewError("real-preview origins must align to source pixels")
    if not np.isclose(width * request.meters_per_pixel, request.width_m) or not np.isclose(
        height * request.meters_per_pixel, request.height_m
    ):
        raise RealPreviewError("real-preview dimensions must align to source pixels")
    if width <= 0 or height <= 0 or width * height > MAX_REAL_PIXELS:
        raise RealPreviewError(f"real-preview exceeds the {MAX_REAL_PIXELS:,}-pixel safety limit")
    if left < 0 or top < 0 or left + width > satellite_size[0] or top + height > satellite_size[1]:
        raise RealPreviewError("real-preview region lies outside the registered source raster")
    return left, top, left + width, top + height


def _open_rgb_crop(path: Path, box: tuple[int, int, int, int]) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.mode != "RGB":
                raise RealPreviewError(f"{path.name} must be RGB, found {image.mode}")
            return np.asarray(image.crop(box), dtype=np.uint8).copy()


def _structure_crop(path: Path, box: tuple[int, int, int, int], radius: int) -> np.ndarray:
    """Blur a haloed source crop so overlapping regional requests agree exactly."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            left, top, right, bottom = box
            halo = max(2, radius * 3)
            expanded = (max(0, left - halo), max(0, top - halo), min(image.width, right + halo), min(image.height, bottom + halo))
            source = image.crop(expanded).convert("RGB")
            blurred = source.filter(ImageFilter.GaussianBlur(radius=radius))
            offset = (left - expanded[0], top - expanded[1])
            return np.asarray(blurred.crop((offset[0], offset[1], offset[0] + right - left, offset[1] + bottom - top)), dtype=np.uint8).copy()


def _resolve_surfaces(preset: RealPreviewPreset, pixels: np.ndarray, *, tb_compat: bool) -> tuple[np.ndarray, list[tuple[int, int, int]]]:
    packed = ((pixels[:, :, 0].astype(np.uint32) << 16) | (pixels[:, :, 1].astype(np.uint32) << 8) | pixels[:, :, 2].astype(np.uint32))
    result = np.full(packed.shape, -1, dtype=np.int16)
    names = list(preset.recipes)
    recipe_index = {name: index for index, name in enumerate(names)}
    mappings = dict(preset.surface_rgb)
    if tb_compat:
        mappings.update(preset.aliases)
    for rgb, surface in mappings.items():
        if surface not in recipe_index:
            continue
        value = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
        result[packed == value] = recipe_index[surface]
    values = np.unique(packed[result < 0])
    unknown = [(int(value >> 16), int((value >> 8) & 255), int(value & 255)) for value in values]
    return result, unknown


def _recipe_layer(preset: RealPreviewPreset, indices: np.ndarray, request: PreviewRequest) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    height, width = indices.shape
    result = np.empty((height, width, 3), dtype=np.float32)
    blend = np.empty((height, width, 1), dtype=np.float32)
    resolved = np.empty((height, width, 3), dtype=np.uint8)
    recipes = list(preset.recipes.values())
    for top in range(0, height, request.tile_size_px):
        for left in range(0, width, request.tile_size_px):
            bottom = min(top + request.tile_size_px, height)
            right = min(left + request.tile_size_px, width)
            xs = request.x_m + (np.arange(left, right, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
            # Rows are emitted top-down, while the registered world Y axis rises
            # from the lower edge. Sampling descending Y keeps nested world crops
            # bitwise consistent with the matching pixels of larger renders.
            ys = request.y_m + request.height_m - (np.arange(top, bottom, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
            tile_indices = indices[top:bottom, left:right]
            tile_result = result[top:bottom, left:right]
            tile_blend = blend[top:bottom, left:right]
            tile_resolved = resolved[top:bottom, left:right]
            for index, recipe in enumerate(recipes):
                selected = tile_indices == index
                if not np.any(selected):
                    continue
                variation = np.zeros(tile_indices.shape, dtype=np.float32)
                for band, scale, strength in (("macro", 320.0, recipe.macro_strength), ("medium", 72.0, recipe.medium_strength), ("local", 18.0, recipe.local_strength)):
                    noise = value_noise(xs, ys, cell_size_m=scale, seed=stable_seed(preset.world_seed, recipe.name, band))
                    variation += (noise - np.float32(0.5)) * np.float32(2 * strength)
                tile_result[selected] = np.asarray(recipe.base_rgb, dtype=np.float32) + variation[selected, None]
                tile_blend[selected] = recipe.blend_strength
                tile_resolved[selected] = np.asarray(recipe.base_rgb, dtype=np.uint8)
    return np.clip(result, 0, 255).astype(np.float32), blend, resolved


def render_real_preview(preset: RealPreviewPreset, request: PreviewRequest, *, variant: str, tb_compat: bool) -> RealPreviewResult:
    """Render one bounded, world-aligned read-only regional experiment."""
    if variant != "original" and variant not in preset.variants:
        raise RealPreviewError(f"unknown real-preview variant {variant!r}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(preset.inputs["satellite"]) as satellite, Image.open(preset.inputs["mask"]) as mask:
            if satellite.mode != "RGB":
                raise RealPreviewError("satellite must be RGB")
            if mask.mode != "RGB":
                raise RealPreviewError("mask must be RGB")
            if mask.size != satellite.size:
                raise RealPreviewError("mask dimensions must match satellite dimensions")
            box = _request_box(preset, request, satellite.size)
    original = _open_rgb_crop(preset.inputs["satellite"], box)
    mask = _open_rgb_crop(preset.inputs["mask"], box)
    indices, unknown = _resolve_surfaces(preset, mask, tb_compat=tb_compat)
    if unknown:
        mode = "TB_COMPAT" if tb_compat else "STRICT_RGB"
        raise RealPreviewError(f"{mode} has unknown mask RGB: {unknown[:8]}")
    structure = _structure_crop(preset.inputs["satellite"], box, preset.structure_blur_radius_px)
    recipe, recipe_blend, mask_resolved = _recipe_layer(preset, indices, request)
    if variant == "original":
        combined = original.copy()
    else:
        weights = preset.variants[variant]
        high = original.astype(np.float32) - structure.astype(np.float32)
        procedural_composite = np.clip(
            structure.astype(np.float32) * weights.structure_weight + high * weights.detail_weight + recipe * weights.recipe_weight,
            0,
            255,
        )
        combined = np.clip(
            original.astype(np.float32) * (1 - recipe_blend) + procedural_composite * recipe_blend,
            0,
            255,
        ).astype(np.uint8)
    return RealPreviewResult(
        original=original,
        structure=structure,
        recipe=recipe.astype(np.uint8),
        mask_resolved=mask_resolved,
        combined=combined,
        variant=variant,
        mask_mode="TB_COMPAT" if tb_compat else "STRICT_RGB",
    )


def write_bmp_atomic(path: Path, pixels: np.ndarray) -> None:
    buffer = io.BytesIO()
    Image.fromarray(pixels, mode="RGB").save(buffer, format="BMP")
    write_bytes_atomic(path, buffer.getvalue())
