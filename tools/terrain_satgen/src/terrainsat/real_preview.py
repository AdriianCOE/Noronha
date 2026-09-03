"""Read-only regional renderer for the current Noronha satellite and mask."""

from __future__ import annotations

from dataclasses import dataclass
import io
import math
from pathlib import Path
from typing import Any
import warnings

import numpy as np
from PIL import Image, ImageFilter

from .inspect import _color_aliases, _input_paths, _world_size, load_preset
from .parsers import AscStats, parse_asc, parse_layers
from .preview import PreviewRequest
from .procedural import stable_seed, value_noise
from .safety import write_bytes_atomic


MAX_REAL_PIXELS = 2048 * 2048
WATER = np.uint8(0)
COAST_TRANSITION = np.uint8(1)
LAND = np.uint8(2)
CONTEXT_NAMES = ("water", "coast_transition", "land")


class RealPreviewError(ValueError):
    """A real-preview request cannot be rendered safely."""


@dataclass(frozen=True)
class Recipe:
    """A small relative adjustment; it never names a replacement surface colour."""

    name: str
    brightness_offset: float
    saturation_adjustment: float
    warmth_bias: float
    channel_bias: tuple[float, float, float]
    macro_strength: float
    medium_strength: float
    local_strength: float
    preservation_strength: float
    feather_width_m: float


@dataclass(frozen=True)
class Variant:
    name: str
    detail_preservation: float
    modulation_strength: float


@dataclass(frozen=True)
class HeightContextConfig:
    world_x_origin_m: float
    world_y_origin_m: float
    water_level_m: float
    land_level_m: float
    water_original_preservation: float
    coast_original_preservation: float
    water_modulation_cap: float
    coast_modulation_cap: float


@dataclass(frozen=True)
class RealPreviewPreset:
    path: Path
    world_size_m: tuple[float, float]
    inputs: dict[str, Path]
    aliases: dict[tuple[int, int, int], str]
    surface_rgb: dict[tuple[int, int, int], str]
    recipes: dict[str, Recipe]
    variants: dict[str, Variant]
    context_preservation: dict[tuple[str, str], float]
    height_context: HeightContextConfig
    world_seed: str
    structure_blur_radius_px: int


@dataclass(frozen=True)
class RealPreviewResult:
    original: np.ndarray
    structure: np.ndarray
    recipe: np.ndarray
    mask_resolved: np.ndarray
    boundary: np.ndarray
    combined: np.ndarray
    variant: str
    mask_mode: str
    context_counts: dict[str, int]


def _number(value: Any, *, label: str, minimum: float | None = None, maximum: float | None = None) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise RealPreviewError(f"{label} must be a finite number")
    number = float(value)
    if minimum is not None and number < minimum:
        raise RealPreviewError(f"{label} must be >= {minimum:g}")
    if maximum is not None and number > maximum:
        raise RealPreviewError(f"{label} must be <= {maximum:g}")
    return number


def _unit(value: Any, *, label: str) -> float:
    return _number(value, label=label, minimum=0.0, maximum=1.0)


def _relative_recipe(name: str, item: Any) -> Recipe:
    if not isinstance(item, dict):
        raise RealPreviewError(f"recipe {name} must be a table")
    allowed = {
        "brightness_offset", "saturation_adjustment", "warmth_bias", "channel_bias",
        "macro_strength", "medium_strength", "local_strength", "preservation_strength",
        "feather_width_m",
    }
    unexpected = sorted(set(item) - allowed)
    if unexpected:
        raise RealPreviewError(f"recipe {name} has unknown keys: " + ", ".join(unexpected))
    bias = item.get("channel_bias")
    if not isinstance(bias, list) or len(bias) != 3:
        raise RealPreviewError(f"recipe {name} channel_bias must contain three numbers")
    return Recipe(
        name=name,
        brightness_offset=_number(item.get("brightness_offset"), label=f"recipe {name} brightness_offset", minimum=-0.25, maximum=0.25),
        saturation_adjustment=_number(item.get("saturation_adjustment"), label=f"recipe {name} saturation_adjustment", minimum=-0.5, maximum=0.5),
        warmth_bias=_number(item.get("warmth_bias"), label=f"recipe {name} warmth_bias", minimum=-0.25, maximum=0.25),
        channel_bias=tuple(_number(value, label=f"recipe {name} channel_bias", minimum=-0.25, maximum=0.25) for value in bias),  # type: ignore[arg-type]
        macro_strength=_unit(item.get("macro_strength"), label=f"recipe {name} macro_strength"),
        medium_strength=_unit(item.get("medium_strength"), label=f"recipe {name} medium_strength"),
        local_strength=_unit(item.get("local_strength"), label=f"recipe {name} local_strength"),
        preservation_strength=_unit(item.get("preservation_strength"), label=f"recipe {name} preservation_strength"),
        feather_width_m=_number(item.get("feather_width_m"), label=f"recipe {name} feather_width_m", minimum=0.0, maximum=64.0),
    )


def _height_context_config(config: Any) -> HeightContextConfig:
    if not isinstance(config, dict):
        raise RealPreviewError("real_preview requires a [real_preview.height_context] table")
    allowed = {
        "world_x_origin_m", "world_y_origin_m", "water_level_m", "land_level_m",
        "water_original_preservation", "coast_original_preservation", "water_modulation_cap", "coast_modulation_cap",
    }
    unexpected = sorted(set(config) - allowed)
    if unexpected:
        raise RealPreviewError("height_context has unknown keys: " + ", ".join(unexpected))
    result = HeightContextConfig(
        world_x_origin_m=_number(config.get("world_x_origin_m"), label="height_context world_x_origin_m"),
        world_y_origin_m=_number(config.get("world_y_origin_m"), label="height_context world_y_origin_m"),
        water_level_m=_number(config.get("water_level_m"), label="height_context water_level_m"),
        land_level_m=_number(config.get("land_level_m"), label="height_context land_level_m"),
        water_original_preservation=_unit(config.get("water_original_preservation"), label="height_context water_original_preservation"),
        coast_original_preservation=_unit(config.get("coast_original_preservation"), label="height_context coast_original_preservation"),
        water_modulation_cap=_unit(config.get("water_modulation_cap"), label="height_context water_modulation_cap"),
        coast_modulation_cap=_unit(config.get("coast_modulation_cap"), label="height_context coast_modulation_cap"),
    )
    if result.water_level_m >= result.land_level_m:
        raise RealPreviewError("height_context water_level_m must be lower than land_level_m")
    return result


def load_real_preview_preset(path: Path) -> RealPreviewPreset:
    """Load the compact, explicit Phase 3.1 modulation model."""
    raw = load_preset(path)
    config = raw.get("real_preview")
    if not isinstance(config, dict):
        raise RealPreviewError("real-preview requires a [real_preview] table")
    allowed = {"world_seed", "structure_blur_radius_px", "variants", "recipes", "height_context", "context_overrides"}
    unexpected = sorted(set(config) - allowed)
    if unexpected:
        raise RealPreviewError("Unknown [real_preview] keys: " + ", ".join(unexpected))
    variants_raw = config.get("variants")
    recipes_raw = config.get("recipes")
    if not isinstance(variants_raw, dict) or not isinstance(recipes_raw, dict):
        raise RealPreviewError("real_preview requires variants and recipes")
    variants: dict[str, Variant] = {}
    for name in ("subtle", "balanced", "authored"):
        item = variants_raw.get(name)
        if not isinstance(item, dict) or set(item) != {"detail_preservation", "modulation_strength"}:
            raise RealPreviewError(f"variant {name} must contain detail_preservation and modulation_strength")
        variants[name] = Variant(name, _unit(item["detail_preservation"], label=f"variant {name} detail_preservation"), _unit(item["modulation_strength"], label=f"variant {name} modulation_strength"))
    recipes = {name: _relative_recipe(name, item) for name, item in recipes_raw.items()}
    surfaces = parse_layers(Path(raw["inputs"]["layers"]))
    aliases = _color_aliases(raw["mask"], surfaces)
    overrides_raw = config.get("context_overrides", {})
    if not isinstance(overrides_raw, dict):
        raise RealPreviewError("context_overrides must be a table")
    context_preservation: dict[tuple[str, str], float] = {}
    for surface, contexts in overrides_raw.items():
        if surface not in recipes or not isinstance(contexts, dict):
            raise RealPreviewError(f"context override {surface} must target a configured recipe")
        for context, item in contexts.items():
            if context not in CONTEXT_NAMES or not isinstance(item, dict) or set(item) != {"preservation_strength"}:
                raise RealPreviewError(f"context override {surface}.{context} supports only preservation_strength")
            context_preservation[(surface, context)] = _unit(item["preservation_strength"], label=f"context override {surface}.{context}")
    return RealPreviewPreset(
        path=path, world_size_m=_world_size(raw["world"]["size_m"]), inputs=_input_paths(raw), aliases=aliases,
        surface_rgb={surface.rgb: surface.name for surface in surfaces}, recipes=recipes, variants=variants,
        context_preservation=context_preservation, height_context=_height_context_config(config.get("height_context")),
        world_seed=str(config.get("world_seed", "terrain-satgen-real-preview")),
        structure_blur_radius_px=int(_number(config.get("structure_blur_radius_px", 12), label="structure_blur_radius_px", minimum=1, maximum=64)),
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
    width, height = round(request.width_m / request.meters_per_pixel), round(request.height_m / request.meters_per_pixel)
    left = round(request.x_m / request.meters_per_pixel)
    top = satellite_size[1] - round((request.y_m + request.height_m) / request.meters_per_pixel)
    if not np.isclose(left * request.meters_per_pixel, request.x_m) or not np.isclose((satellite_size[1] - top - height) * request.meters_per_pixel, request.y_m):
        raise RealPreviewError("real-preview origins must align to source pixels")
    if not np.isclose(width * request.meters_per_pixel, request.width_m) or not np.isclose(height * request.meters_per_pixel, request.height_m):
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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            left, top, right, bottom = box
            halo = max(2, radius * 3)
            expanded = (max(0, left - halo), max(0, top - halo), min(image.width, right + halo), min(image.height, bottom + halo))
            blurred = image.crop(expanded).convert("RGB").filter(ImageFilter.GaussianBlur(radius=radius))
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
        if surface in recipe_index:
            result[packed == ((rgb[0] << 16) | (rgb[1] << 8) | rgb[2])] = recipe_index[surface]
    values = np.unique(packed[result < 0])
    return result, [(int(value >> 16), int((value >> 8) & 255), int(value & 255)) for value in values]


def _expand_box(box: tuple[int, int, int, int], amount: int, size: tuple[int, int]) -> tuple[tuple[int, int, int, int], tuple[slice, slice]]:
    left, top, right, bottom = box
    expanded = (max(0, left - amount), max(0, top - amount), min(size[0], right + amount), min(size[1], bottom + amount))
    return expanded, (slice(top - expanded[1], top - expanded[1] + bottom - top), slice(left - expanded[0], left - expanded[0] + right - left))


def _dilate(mask: np.ndarray) -> np.ndarray:
    result = mask.copy()
    result[1:] |= mask[:-1]
    result[:-1] |= mask[1:]
    result[:, 1:] |= mask[:, :-1]
    result[:, :-1] |= mask[:, 1:]
    return result


def _boundary_distance(indices: np.ndarray, maximum: int) -> np.ndarray:
    """Bounded Manhattan distance to a class boundary; never a global distance field."""
    if maximum <= 0:
        return np.zeros(indices.shape, dtype=np.int16)
    boundary = np.zeros(indices.shape, dtype=bool)
    boundary[1:] |= indices[1:] != indices[:-1]
    boundary[:-1] |= indices[:-1] != indices[1:]
    boundary[:, 1:] |= indices[:, 1:] != indices[:, :-1]
    boundary[:, :-1] |= indices[:, :-1] != indices[:, 1:]
    distance = np.full(indices.shape, maximum + 1, dtype=np.int16)
    distance[boundary] = 0
    frontier = boundary
    for step in range(1, maximum + 1):
        frontier = _dilate(frontier) & (distance > maximum)
        if not np.any(frontier):
            break
        distance[frontier] = step
    return distance


def _height_grid(path: Path) -> tuple[AscStats, np.ndarray]:
    stats = parse_asc(path)
    rows: list[np.ndarray] = []
    started = False
    with path.open("r", encoding="ascii") as stream:
        for line in stream:
            values = line.split()
            if not values:
                continue
            try:
                float(values[0])
                started = True
            except ValueError:
                if started:
                    raise RealPreviewError("heightmap has a non-numeric data row")
                continue
            row = np.fromstring(line, sep=" ", dtype=np.float32)
            if row.size != stats.ncols:
                raise RealPreviewError("heightmap row width changed after validation")
            rows.append(row)
    if len(rows) != stats.nrows:
        raise RealPreviewError("heightmap row count changed after validation")
    return stats, np.stack(rows)


def _height_context(preset: RealPreviewPreset, request: PreviewRequest) -> np.ndarray:
    stats, grid = _height_grid(preset.inputs["height"])
    config = preset.height_context
    if not np.isclose(stats.xllcorner, config.world_x_origin_m) or not np.isclose(stats.yllcorner, config.world_y_origin_m):
        raise RealPreviewError("height_context world origin does not match the documented ASC mapframe")
    if not np.isclose(stats.ncols * stats.cellsize, preset.world_size_m[0]) or not np.isclose(stats.nrows * stats.cellsize, preset.world_size_m[1]):
        raise RealPreviewError("heightmap extent does not match registered world size")
    width, height = round(request.width_m / request.meters_per_pixel), round(request.height_m / request.meters_per_pixel)
    world_x = request.x_m + (np.arange(width, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
    world_y = request.y_m + request.height_m - (np.arange(height, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
    columns = np.floor((config.world_x_origin_m + world_x - stats.xllcorner) / stats.cellsize).astype(np.int32)
    rows_from_bottom = np.floor((config.world_y_origin_m + world_y - stats.yllcorner) / stats.cellsize).astype(np.int32)
    rows = stats.nrows - 1 - rows_from_bottom
    if columns.min() < 0 or columns.max() >= stats.ncols or rows.min() < 0 or rows.max() >= stats.nrows:
        raise RealPreviewError("real-preview region lies outside the authoritative heightmap")
    values = grid[rows[:, None], columns[None, :]]
    context = np.full(values.shape, COAST_TRANSITION, dtype=np.uint8)
    context[values <= config.water_level_m] = WATER
    context[values >= config.land_level_m] = LAND
    return context


def _relative_recipe_layer(preset: RealPreviewPreset, original: np.ndarray, indices: np.ndarray, request: PreviewRequest, context: np.ndarray, feather_distance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    height, width = indices.shape
    result = original.astype(np.float32).copy()
    resolved = np.empty((height, width, 3), dtype=np.uint8)
    recipes = list(preset.recipes.values())
    for top in range(0, height, request.tile_size_px):
        for left in range(0, width, request.tile_size_px):
            bottom, right = min(top + request.tile_size_px, height), min(left + request.tile_size_px, width)
            xs = request.x_m + (np.arange(left, right, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
            ys = request.y_m + request.height_m - (np.arange(top, bottom, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
            tile_indices, tile_context = indices[top:bottom, left:right], context[top:bottom, left:right]
            tile_original = original[top:bottom, left:right].astype(np.float32)
            tile_result, tile_resolved = result[top:bottom, left:right], resolved[top:bottom, left:right]
            luminance = (tile_original[:, :, 0] * 0.2126 + tile_original[:, :, 1] * 0.7152 + tile_original[:, :, 2] * 0.0722)[:, :, None]
            for index, recipe in enumerate(recipes):
                selected = tile_indices == index
                if not np.any(selected):
                    continue
                adjusted = luminance + (tile_original - luminance) * np.float32(1.0 + recipe.saturation_adjustment)
                adjusted += np.float32(recipe.brightness_offset * 255.0)
                adjusted += np.asarray((recipe.warmth_bias + recipe.channel_bias[0], recipe.channel_bias[1], -recipe.warmth_bias + recipe.channel_bias[2]), dtype=np.float32) * np.float32(255.0)
                variation = np.zeros(tile_indices.shape, dtype=np.float32)
                for band, scale, strength in (("macro", 320.0, recipe.macro_strength), ("medium", 72.0, recipe.medium_strength), ("local", 18.0, recipe.local_strength)):
                    variation += (value_noise(xs, ys, cell_size_m=scale, seed=stable_seed(preset.world_seed, recipe.name, band)) - np.float32(0.5)) * np.float32(2.0 * strength * 255.0)
                adjusted += variation[:, :, None]
                preservation = np.full(tile_indices.shape, recipe.preservation_strength, dtype=np.float32)
                for code, context_name in ((WATER, "water"), (COAST_TRANSITION, "coast_transition"), (LAND, "land")):
                    override = preset.context_preservation.get((recipe.name, context_name))
                    if override is not None:
                        preservation[tile_context == code] = override
                strength = 1.0 - preservation
                strength[tile_context == WATER] = np.minimum(strength[tile_context == WATER], preset.height_context.water_modulation_cap)
                strength[tile_context == COAST_TRANSITION] = np.minimum(strength[tile_context == COAST_TRANSITION], preset.height_context.coast_modulation_cap)
                if recipe.feather_width_m > 0:
                    strength *= np.minimum(1.0, feather_distance[top:bottom, left:right].astype(np.float32) * request.meters_per_pixel / recipe.feather_width_m)
                tile_result[selected] = tile_original[selected] + (adjusted[selected] - tile_original[selected]) * strength[selected, None]
                tile_resolved[selected] = np.asarray((40 + (index * 71) % 190, 70 + (index * 47) % 160, 60 + (index * 91) % 180), dtype=np.uint8)
    return np.clip(result, 0, 255).astype(np.float32), resolved


def _boundary_diagnostic(indices: np.ndarray, distance: np.ndarray, recipes: list[Recipe], request: PreviewRequest) -> np.ndarray:
    width_by_surface = np.asarray([recipe.feather_width_m for recipe in recipes], dtype=np.float32)[indices]
    zone = (width_by_surface > 0) & (distance.astype(np.float32) * request.meters_per_pixel < width_by_surface)
    image = np.zeros((*indices.shape, 3), dtype=np.uint8)
    image[zone] = (246, 196, 54)
    image[(distance == 0) & (width_by_surface > 0)] = (224, 69, 107)
    return image


def render_real_preview(preset: RealPreviewPreset, request: PreviewRequest, *, variant: str, tb_compat: bool) -> RealPreviewResult:
    """Render a bounded Phase 3.1 experiment from immutable source inputs."""
    if variant != "original" and variant not in preset.variants:
        raise RealPreviewError(f"unknown real-preview variant {variant!r}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(preset.inputs["satellite"]) as satellite, Image.open(preset.inputs["mask"]) as mask:
            if satellite.mode != "RGB" or mask.mode != "RGB":
                raise RealPreviewError("satellite and mask must be RGB")
            if mask.size != satellite.size:
                raise RealPreviewError("mask dimensions must match satellite dimensions")
            box, raster_size = _request_box(preset, request, satellite.size), satellite.size
    original = _open_rgb_crop(preset.inputs["satellite"], box)
    structure = _structure_crop(preset.inputs["satellite"], box, preset.structure_blur_radius_px)
    # ``original`` is intentionally a pure satellite crop. It remains useful
    # even when STRICT_RGB is used to diagnose the mask separately, so it must
    # not require an alias resolution or an ASC context read.
    if variant == "original":
        empty = np.zeros_like(original)
        return RealPreviewResult(
            original, structure, original.copy(), empty, empty, original.copy(), variant,
            "TB_COMPAT" if tb_compat else "STRICT_RGB", {"water": 0, "coast_transition": 0, "land": 0},
        )
    max_feather = math.ceil(max(recipe.feather_width_m for recipe in preset.recipes.values()) / request.meters_per_pixel)
    expanded_box, core = _expand_box(box, max_feather, raster_size)
    expanded_indices, unknown = _resolve_surfaces(preset, _open_rgb_crop(preset.inputs["mask"], expanded_box), tb_compat=tb_compat)
    if unknown:
        mode = "TB_COMPAT" if tb_compat else "STRICT_RGB"
        raise RealPreviewError(f"{mode} has unknown mask RGB: {unknown[:8]}")
    expanded_distance = _boundary_distance(expanded_indices, max_feather)
    indices, distance = expanded_indices[core], expanded_distance[core]
    context = _height_context(preset, request)
    recipe, mask_resolved = _relative_recipe_layer(preset, original, indices, request, context, distance)
    boundary = _boundary_diagnostic(indices, distance, list(preset.recipes.values()), request)
    settings = preset.variants[variant]
    frequency_base = structure.astype(np.float32) + (original.astype(np.float32) - structure.astype(np.float32)) * settings.detail_preservation
    combined_float = frequency_base + (recipe - original.astype(np.float32)) * settings.modulation_strength
    water, coast = context == WATER, context == COAST_TRANSITION
    combined_float[water] = original[water].astype(np.float32) * preset.height_context.water_original_preservation + combined_float[water] * (1.0 - preset.height_context.water_original_preservation)
    combined_float[coast] = original[coast].astype(np.float32) * preset.height_context.coast_original_preservation + combined_float[coast] * (1.0 - preset.height_context.coast_original_preservation)
    combined = np.rint(np.clip(combined_float, 0, 255)).astype(np.uint8)
    return RealPreviewResult(original, structure, recipe.astype(np.uint8), mask_resolved, boundary, combined, variant, "TB_COMPAT" if tb_compat else "STRICT_RGB", {"water": int(np.count_nonzero(context == WATER)), "coast_transition": int(np.count_nonzero(context == COAST_TRANSITION)), "land": int(np.count_nonzero(context == LAND))})


def write_bmp_atomic(path: Path, pixels: np.ndarray) -> None:
    buffer = io.BytesIO()
    Image.fromarray(pixels, mode="RGB").save(buffer, format="BMP")
    write_bytes_atomic(path, buffer.getvalue())
