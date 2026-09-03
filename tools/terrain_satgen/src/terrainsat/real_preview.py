"""Read-only regional renderer for the current Noronha satellite and mask."""

from __future__ import annotations

from dataclasses import dataclass
import io
import math
import os
from pathlib import Path
import struct
import tempfile
import time
from typing import Any
import warnings

import numpy as np
from PIL import Image, ImageFilter

from .inspect import _color_aliases, _input_paths, _world_size, load_preset, sha256_file
from .parsers import AscStats, parse_asc, parse_layers
from .preview import PreviewRequest
from .procedural import anisotropic_bands, coherent_patch_field, stable_seed, value_noise, value_noise_at, warped_coordinates
from .safety import write_bytes_atomic


NORMAL_MAX_REAL_PIXELS = 2048 * 2048
STREAMING_MAX_DIMENSION = 4096
BMP_HEADER_SIZE = 54
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
    patch_strength: float
    motif_strength: float
    motif_scale_m: float
    anisotropy_strength: float
    anisotropy_scale_m: float


@dataclass(frozen=True)
class Variant:
    name: str
    macro_preservation: float
    meso_preservation: float
    micro_preservation: float
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
class ArtPassConfig:
    patch_scale_m: float
    warp_scale_m: float
    warp_strength_m: float
    adaptive_radius_px: int
    adaptive_min_multiplier: float
    adaptive_max_multiplier: float


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
    meso_blur_radius_px: int
    art_pass: ArtPassConfig


@dataclass(frozen=True)
class RealPreviewResult:
    original: np.ndarray
    structure: np.ndarray
    meso: np.ndarray
    micro: np.ndarray
    recipe: np.ndarray
    mask_resolved: np.ndarray
    boundary: np.ndarray
    combined: np.ndarray
    variant: str
    mask_mode: str
    context_counts: dict[str, int]
    source_uniformity: np.ndarray
    adaptive_strength: np.ndarray
    patch_identity: np.ndarray
    warped_meso: np.ndarray
    forest_motif: np.ndarray


@dataclass(frozen=True)
class StreamingRenderReport:
    """Small evidence record for a bounded-memory real-preview render."""

    width: int
    height: int
    tile_size_px: int
    tile_count: int
    elapsed_seconds: float
    input_hashes_before: dict[str, str]
    input_hashes_after: dict[str, str]
    context_counts: dict[str, int]
    metrics: dict[str, float | str]
    adaptive: dict[str, float] | None
    memory_model: dict[str, object]


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
        "feather_width_m", "patch_strength", "motif_strength", "motif_scale_m",
        "anisotropy_strength", "anisotropy_scale_m",
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
        patch_strength=_unit(item.get("patch_strength", 0.0), label=f"recipe {name} patch_strength"),
        motif_strength=_unit(item.get("motif_strength", 0.0), label=f"recipe {name} motif_strength"),
        motif_scale_m=_number(item.get("motif_scale_m", 80.0), label=f"recipe {name} motif_scale_m", minimum=4.0, maximum=512.0),
        anisotropy_strength=_unit(item.get("anisotropy_strength", 0.0), label=f"recipe {name} anisotropy_strength"),
        anisotropy_scale_m=_number(item.get("anisotropy_scale_m", 24.0), label=f"recipe {name} anisotropy_scale_m", minimum=4.0, maximum=256.0),
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


def _art_pass_config(config: Any) -> ArtPassConfig:
    if config is None:
        return ArtPassConfig(220.0, 480.0, 22.0, 5, 0.68, 1.18)
    if not isinstance(config, dict):
        raise RealPreviewError("art_pass must be a table")
    allowed = {"patch_scale_m", "warp_scale_m", "warp_strength_m", "adaptive_radius_px", "adaptive_min_multiplier", "adaptive_max_multiplier"}
    unexpected = sorted(set(config) - allowed)
    if unexpected:
        raise RealPreviewError("art_pass has unknown keys: " + ", ".join(unexpected))
    result = ArtPassConfig(
        patch_scale_m=_number(config.get("patch_scale_m"), label="art_pass patch_scale_m", minimum=32.0, maximum=1024.0),
        warp_scale_m=_number(config.get("warp_scale_m"), label="art_pass warp_scale_m", minimum=64.0, maximum=2048.0),
        warp_strength_m=_number(config.get("warp_strength_m"), label="art_pass warp_strength_m", minimum=0.0, maximum=128.0),
        adaptive_radius_px=int(_number(config.get("adaptive_radius_px"), label="art_pass adaptive_radius_px", minimum=1, maximum=32)),
        adaptive_min_multiplier=_number(config.get("adaptive_min_multiplier"), label="art_pass adaptive_min_multiplier", minimum=0.05, maximum=2.0),
        adaptive_max_multiplier=_number(config.get("adaptive_max_multiplier"), label="art_pass adaptive_max_multiplier", minimum=0.05, maximum=2.0),
    )
    if result.adaptive_min_multiplier > result.adaptive_max_multiplier:
        raise RealPreviewError("art_pass adaptive_min_multiplier must not exceed adaptive_max_multiplier")
    return result


def load_real_preview_preset(path: Path) -> RealPreviewPreset:
    """Load the compact, explicit Phase 3.1 modulation model."""
    raw = load_preset(path)
    config = raw.get("real_preview")
    if not isinstance(config, dict):
        raise RealPreviewError("real-preview requires a [real_preview] table")
    allowed = {
        "world_seed", "structure_blur_radius_px", "meso_blur_radius_px", "variants",
        "recipes", "height_context", "context_overrides", "art_pass",
    }
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
        expected = {"macro_preservation", "meso_preservation", "micro_preservation", "modulation_strength"}
        if not isinstance(item, dict) or set(item) != expected:
            raise RealPreviewError(
                f"variant {name} must contain macro_preservation, meso_preservation, "
                "micro_preservation and modulation_strength"
            )
        variants[name] = Variant(
            name,
            _unit(item["macro_preservation"], label=f"variant {name} macro_preservation"),
            _unit(item["meso_preservation"], label=f"variant {name} meso_preservation"),
            _unit(item["micro_preservation"], label=f"variant {name} micro_preservation"),
            _unit(item["modulation_strength"], label=f"variant {name} modulation_strength"),
        )
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
    structure_blur_radius_px = int(_number(config.get("structure_blur_radius_px", 12), label="structure_blur_radius_px", minimum=2, maximum=64))
    meso_blur_radius_px = int(_number(config.get("meso_blur_radius_px", 4), label="meso_blur_radius_px", minimum=1, maximum=32))
    if meso_blur_radius_px >= structure_blur_radius_px:
        raise RealPreviewError("meso_blur_radius_px must be smaller than structure_blur_radius_px")
    return RealPreviewPreset(
        path=path, world_size_m=_world_size(raw["world"]["size_m"]), inputs=_input_paths(raw), aliases=aliases,
        surface_rgb={surface.rgb: surface.name for surface in surfaces}, recipes=recipes, variants=variants,
        context_preservation=context_preservation, height_context=_height_context_config(config.get("height_context")),
        world_seed=str(config.get("world_seed", "terrain-satgen-real-preview")),
        structure_blur_radius_px=structure_blur_radius_px,
        meso_blur_radius_px=meso_blur_radius_px,
        art_pass=_art_pass_config(config.get("art_pass")),
    )


def _request_box(
    preset: RealPreviewPreset,
    request: PreviewRequest,
    satellite_size: tuple[int, int],
    *,
    allow_streaming: bool = False,
) -> tuple[int, int, int, int]:
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
    if width <= 0 or height <= 0:
        raise RealPreviewError("real-preview dimensions must be positive")
    if allow_streaming:
        if width > STREAMING_MAX_DIMENSION or height > STREAMING_MAX_DIMENSION:
            raise RealPreviewError(
                f"stream-output exceeds the {STREAMING_MAX_DIMENSION} x {STREAMING_MAX_DIMENSION}-pixel safety limit"
            )
    elif width * height > NORMAL_MAX_REAL_PIXELS:
        raise RealPreviewError(f"real-preview exceeds the {NORMAL_MAX_REAL_PIXELS:,}-pixel safety limit")
    if left < 0 or top < 0 or left + width > satellite_size[0] or top + height > satellite_size[1]:
        raise RealPreviewError("real-preview region lies outside the registered source raster")
    return left, top, left + width, top + height


@dataclass(frozen=True)
class _BmpInfo:
    width: int
    height: int
    pixel_offset: int
    row_stride: int


def _bmp_info(path: Path) -> _BmpInfo | None:
    """Return the narrow 24-bit BMP layout used by the authoritative inputs."""
    if path.suffix.lower() != ".bmp":
        return None
    with path.open("rb") as stream:
        header = stream.read(54)
    if len(header) != 54 or header[:2] != b"BM":
        return None
    dib_size = struct.unpack_from("<I", header, 14)[0]
    width, height = struct.unpack_from("<ii", header, 18)
    planes, bits_per_pixel = struct.unpack_from("<HH", header, 26)
    compression = struct.unpack_from("<I", header, 30)[0]
    if dib_size != 40 or width <= 0 or height <= 0 or planes != 1 or bits_per_pixel != 24 or compression != 0:
        return None
    return _BmpInfo(width, height, struct.unpack_from("<I", header, 10)[0], ((width * 3 + 3) // 4) * 4)


def _read_bmp_rgb_crop(path: Path, info: _BmpInfo, box: tuple[int, int, int, int]) -> np.ndarray:
    left, top, right, bottom = box
    if left < 0 or top < 0 or right > info.width or bottom > info.height or left >= right or top >= bottom:
        raise RealPreviewError("BMP crop lies outside the source raster")
    result = np.empty((bottom - top, right - left, 3), dtype=np.uint8)
    row_bytes = (right - left) * 3
    with path.open("rb") as stream:
        for output_row, source_row in enumerate(range(top, bottom)):
            # BMP scanlines are stored bottom-up in BGR order.
            offset = info.pixel_offset + (info.height - 1 - source_row) * info.row_stride + left * 3
            stream.seek(offset)
            row = stream.read(row_bytes)
            if len(row) != row_bytes:
                raise RealPreviewError(f"{path.name} ended while reading a BMP scanline")
            result[output_row] = np.frombuffer(row, dtype=np.uint8).reshape(-1, 3)[:, ::-1]
    return result


def _open_rgb_crop(path: Path, box: tuple[int, int, int, int]) -> np.ndarray:
    info = _bmp_info(path)
    if info is not None:
        return _read_bmp_rgb_crop(path, info, box)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.mode != "RGB":
                raise RealPreviewError(f"{path.name} must be RGB, found {image.mode}")
            return np.asarray(image.crop(box), dtype=np.uint8).copy()


def _structure_crop(path: Path, box: tuple[int, int, int, int], radius: int) -> np.ndarray:
    info = _bmp_info(path)
    if info is not None:
        image_size = (info.width, info.height)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                image_size = image.size
    left, top, right, bottom = box
    halo = max(2, radius * 3)
    expanded = (max(0, left - halo), max(0, top - halo), min(image_size[0], right + halo), min(image_size[1], bottom + halo))
    source = _open_rgb_crop(path, expanded)
    blurred = Image.fromarray(source, mode="RGB").filter(ImageFilter.GaussianBlur(radius=radius))
    offset = (left - expanded[0], top - expanded[1])
    return np.asarray(blurred.crop((offset[0], offset[1], offset[0] + right - left, offset[1] + bottom - top)), dtype=np.uint8).copy()


def _frequency_components(
    path: Path,
    box: tuple[int, int, int, int],
    *,
    macro_radius: int,
    meso_radius: int,
    original: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a deterministic Laplacian-style macro/meso/micro split.

    Both low passes are read with their own three-radius source halo.  This
    keeps a nested crop and a tiled render byte-identical at their shared
    pixels while avoiding a full-raster buffer.
    """
    macro = _structure_crop(path, box, macro_radius)
    meso_lowpass = _structure_crop(path, box, meso_radius)
    macro_float = macro.astype(np.float32)
    meso = meso_lowpass.astype(np.float32) - macro_float
    micro = original.astype(np.float32) - meso_lowpass.astype(np.float32)
    return macro, meso, micro


def frequency_component_display(component: np.ndarray, *, gain: float = 4.0) -> np.ndarray:
    """Make a signed meso/micro component inspectable without changing data."""
    return np.rint(np.clip(component * np.float32(gain) + 128.0, 0, 255)).astype(np.uint8)


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


def _height_data_row_offsets(path: Path, stats: AscStats) -> list[int]:
    """Index ASC data-row byte offsets without retaining any height samples."""
    offsets: list[int] = []
    started = False
    with path.open("rb") as stream:
        while True:
            offset = stream.tell()
            line = stream.readline()
            if not line:
                break
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
            offsets.append(offset)
    if len(offsets) != stats.nrows:
        raise RealPreviewError("heightmap row count changed after validation")
    return offsets


def _height_row_window(
    path: Path,
    stats: AscStats,
    first_row: int,
    last_row: int,
    *,
    data_row_offsets: list[int] | None = None,
) -> np.ndarray:
    if data_row_offsets is not None:
        if len(data_row_offsets) != stats.nrows:
            raise RealPreviewError("heightmap row-offset index is invalid")
        rows: list[np.ndarray] = []
        with path.open("rb") as stream:
            for data_row in range(first_row, last_row + 1):
                stream.seek(data_row_offsets[data_row])
                row = np.fromstring(stream.readline().decode("ascii"), sep=" ", dtype=np.float32)
                if row.size != stats.ncols:
                    raise RealPreviewError("heightmap row width changed after validation")
                rows.append(row)
        return np.stack(rows)
    rows: list[np.ndarray] = []
    data_row = 0
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
            if first_row <= data_row <= last_row:
                row = np.fromstring(line, sep=" ", dtype=np.float32)
                if row.size != stats.ncols:
                    raise RealPreviewError("heightmap row width changed after validation")
                rows.append(row)
            data_row += 1
    if data_row != stats.nrows:
        raise RealPreviewError("heightmap row count changed after validation")
    expected = last_row - first_row + 1
    if len(rows) != expected:
        raise RealPreviewError("heightmap requested rows are incomplete")
    return np.stack(rows)


def _height_context(
    preset: RealPreviewPreset,
    request: PreviewRequest,
    *,
    stats: AscStats | None = None,
    data_row_offsets: list[int] | None = None,
) -> np.ndarray:
    stats = parse_asc(preset.inputs["height"]) if stats is None else stats
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
    first_row, last_row = int(rows.min()), int(rows.max())
    grid = _height_row_window(
        preset.inputs["height"], stats, first_row, last_row, data_row_offsets=data_row_offsets,
    )
    values = grid[(rows - first_row)[:, None], columns[None, :]]
    context = np.full(values.shape, COAST_TRANSITION, dtype=np.uint8)
    context[values <= config.water_level_m] = WATER
    context[values >= config.land_level_m] = LAND
    return context


def _source_uniformity(path: Path, box: tuple[int, int, int, int], original: np.ndarray, radius: int, art_pass: ArtPassConfig) -> tuple[np.ndarray, np.ndarray]:
    """Reduce material modulation where the source already has meaningful meso detail."""
    local_base = _structure_crop(path, box, radius).astype(np.float32)
    original_luma = original.astype(np.float32).dot(np.asarray((0.2126, 0.7152, 0.0722), dtype=np.float32))
    local_luma = local_base.dot(np.asarray((0.2126, 0.7152, 0.0722), dtype=np.float32))
    local_structure = np.abs(original_luma - local_luma)
    uniformity = np.float32(1.0) - np.clip(local_structure / np.float32(18.0), 0.0, 1.0)
    adaptive = np.float32(art_pass.adaptive_min_multiplier) + uniformity * np.float32(art_pass.adaptive_max_multiplier - art_pass.adaptive_min_multiplier)
    return uniformity.astype(np.float32), adaptive.astype(np.float32)


def scalar_field_display(field: np.ndarray, *, maximum: float = 1.0) -> np.ndarray:
    """Show a bounded scalar diagnostic as neutral RGB without affecting render data."""
    grey = np.rint(np.clip(field.astype(np.float32) / np.float32(maximum), 0.0, 1.0) * 255.0).astype(np.uint8)
    return np.repeat(grey[:, :, None], 3, axis=2)


def _relative_recipe_layer(
    preset: RealPreviewPreset,
    original: np.ndarray,
    indices: np.ndarray,
    request: PreviewRequest,
    context: np.ndarray,
    feather_distance: np.ndarray,
    adaptive_strength: np.ndarray,
    *,
    art_pass: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    height, width = indices.shape
    result = original.astype(np.float32).copy()
    resolved = np.empty((height, width, 3), dtype=np.uint8)
    patch_identity = np.zeros((height, width), dtype=np.uint8)
    warped_meso = np.zeros((height, width), dtype=np.float32)
    forest_motif = np.zeros((height, width), dtype=np.float32)
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
                if art_pass:
                    patch, identity = coherent_patch_field(
                        xs, ys,
                        patch_scale_m=preset.art_pass.patch_scale_m,
                        warp_scale_m=preset.art_pass.warp_scale_m,
                        warp_strength_m=preset.art_pass.warp_strength_m,
                        seed=stable_seed(preset.world_seed, recipe.name, "patch"),
                    )
                    variation += patch * np.float32(recipe.patch_strength * 255.0)
                    patch_identity[top:bottom, left:right][selected] = identity[selected]
                    warped_meso[top:bottom, left:right][selected] = patch[selected]
                    if recipe.motif_strength > 0:
                        warped_x, warped_y = warped_coordinates(
                            xs, ys,
                            scale_m=preset.art_pass.warp_scale_m,
                            strength_m=preset.art_pass.warp_strength_m,
                            seed=stable_seed(preset.world_seed, recipe.name, "motif-warp"),
                        )
                        motif = (value_noise_at(warped_x, warped_y, cell_size_m=recipe.motif_scale_m, seed=stable_seed(preset.world_seed, recipe.name, "motif")) - np.float32(0.5)) * np.float32(2.0)
                        variation += motif * np.float32(recipe.motif_strength * 255.0)
                        if recipe.name == "en_forest_con":
                            forest_motif[top:bottom, left:right][selected] = motif[selected]
                    if recipe.anisotropy_strength > 0:
                        warped_x, warped_y = warped_coordinates(
                            xs, ys,
                            scale_m=preset.art_pass.warp_scale_m,
                            strength_m=preset.art_pass.warp_strength_m,
                            seed=stable_seed(preset.world_seed, recipe.name, "anisotropy-warp"),
                        )
                        bands = anisotropic_bands(warped_x, warped_y, scale_m=recipe.anisotropy_scale_m, strength=recipe.anisotropy_strength)
                        variation += bands * np.float32(255.0)
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
                if art_pass:
                    strength *= adaptive_strength[top:bottom, left:right]
                tile_result[selected] = tile_original[selected] + (adjusted[selected] - tile_original[selected]) * strength[selected, None]
                tile_resolved[selected] = np.asarray((40 + (index * 71) % 190, 70 + (index * 47) % 160, 60 + (index * 91) % 180), dtype=np.uint8)
    return np.clip(result, 0, 255).astype(np.float32), resolved, patch_identity, warped_meso, forest_motif


def _boundary_diagnostic(indices: np.ndarray, distance: np.ndarray, recipes: list[Recipe], request: PreviewRequest) -> np.ndarray:
    width_by_surface = np.asarray([recipe.feather_width_m for recipe in recipes], dtype=np.float32)[indices]
    zone = (width_by_surface > 0) & (distance.astype(np.float32) * request.meters_per_pixel < width_by_surface)
    image = np.zeros((*indices.shape, 3), dtype=np.uint8)
    image[zone] = (246, 196, 54)
    image[(distance == 0) & (width_by_surface > 0)] = (224, 69, 107)
    return image


def render_real_preview(
    preset: RealPreviewPreset,
    request: PreviewRequest,
    *,
    variant: str,
    tb_compat: bool,
    art_pass: bool = False,
    height_stats: AscStats | None = None,
    height_row_offsets: list[int] | None = None,
) -> RealPreviewResult:
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
    structure, meso, micro = _frequency_components(
        preset.inputs["satellite"],
        box,
        macro_radius=preset.structure_blur_radius_px,
        meso_radius=preset.meso_blur_radius_px,
        original=original,
    )
    # ``original`` is intentionally a pure satellite crop. It remains useful
    # even when STRICT_RGB is used to diagnose the mask separately, so it must
    # not require an alias resolution or an ASC context read.
    if variant == "original":
        empty = np.zeros_like(original)
        empty_scalar = np.zeros(original.shape[:2], dtype=np.float32)
        return RealPreviewResult(
            original, structure, meso, micro, original.copy(), empty, empty, original.copy(), variant,
            "TB_COMPAT" if tb_compat else "STRICT_RGB", {"water": 0, "coast_transition": 0, "land": 0},
            empty_scalar, empty_scalar, np.zeros(original.shape[:2], dtype=np.uint8), empty_scalar, empty_scalar,
        )
    max_feather = math.ceil(max(recipe.feather_width_m for recipe in preset.recipes.values()) / request.meters_per_pixel)
    expanded_box, core = _expand_box(box, max_feather, raster_size)
    expanded_indices, unknown = _resolve_surfaces(preset, _open_rgb_crop(preset.inputs["mask"], expanded_box), tb_compat=tb_compat)
    if unknown:
        mode = "TB_COMPAT" if tb_compat else "STRICT_RGB"
        raise RealPreviewError(f"{mode} has unknown mask RGB: {unknown[:8]}")
    expanded_distance = _boundary_distance(expanded_indices, max_feather)
    indices, distance = expanded_indices[core], expanded_distance[core]
    context = _height_context(
        preset, request, stats=height_stats, data_row_offsets=height_row_offsets,
    )
    source_uniformity, adaptive_strength = _source_uniformity(
        preset.inputs["satellite"], box, original, preset.art_pass.adaptive_radius_px, preset.art_pass,
    )
    recipe, mask_resolved, patch_identity, warped_meso, forest_motif = _relative_recipe_layer(
        preset, original, indices, request, context, distance, adaptive_strength, art_pass=art_pass,
    )
    boundary = _boundary_diagnostic(indices, distance, list(preset.recipes.values()), request)
    settings = preset.variants[variant]
    frequency_base = (
        structure.astype(np.float32) * settings.macro_preservation
        + meso * settings.meso_preservation
        + micro * settings.micro_preservation
    )
    combined_float = frequency_base + (recipe - original.astype(np.float32)) * settings.modulation_strength
    water, coast = context == WATER, context == COAST_TRANSITION
    combined_float[water] = original[water].astype(np.float32) * preset.height_context.water_original_preservation + combined_float[water] * (1.0 - preset.height_context.water_original_preservation)
    combined_float[coast] = original[coast].astype(np.float32) * preset.height_context.coast_original_preservation + combined_float[coast] * (1.0 - preset.height_context.coast_original_preservation)
    combined = np.rint(np.clip(combined_float, 0, 255)).astype(np.uint8)
    return RealPreviewResult(
        original, structure, meso, micro, recipe.astype(np.uint8), mask_resolved, boundary,
        combined, variant, "TB_COMPAT" if tb_compat else "STRICT_RGB",
        {"water": int(np.count_nonzero(context == WATER)), "coast_transition": int(np.count_nonzero(context == COAST_TRANSITION)), "land": int(np.count_nonzero(context == LAND))},
        source_uniformity, adaptive_strength, patch_identity, warped_meso, forest_motif,
    )


class _ScalarAccumulator:
    def __init__(self, *, minimum: float, maximum: float, bins: int = 2048) -> None:
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.bins = bins
        self.count = 0
        self.total = 0.0
        self.min_positive: float | None = None
        self.max_value: float | None = None
        self.histogram = np.zeros(bins, dtype=np.int64)

    def add(self, values: np.ndarray) -> None:
        flat = values.astype(np.float32, copy=False).ravel()
        if flat.size == 0:
            return
        self.count += int(flat.size)
        self.total += float(np.sum(flat, dtype=np.float64))
        positive = flat[flat > 0]
        if positive.size:
            candidate = float(positive.min())
            self.min_positive = candidate if self.min_positive is None else min(self.min_positive, candidate)
        candidate_max = float(flat.max())
        self.max_value = candidate_max if self.max_value is None else max(self.max_value, candidate_max)
        span = self.maximum - self.minimum
        if span <= 0:
            indices = np.zeros(flat.shape, dtype=np.int32)
        else:
            indices = np.floor((np.clip(flat, self.minimum, self.maximum) - self.minimum) / span * (self.bins - 1)).astype(np.int32)
        self.histogram += np.bincount(indices, minlength=self.bins)

    def finish(self) -> dict[str, float]:
        if self.count == 0:
            return {"mean": 0.0, "p05": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "min_positive": 0.0, "max": 0.0}
        cumulative = np.cumsum(self.histogram)

        def percentile(fraction: float) -> float:
            rank = max(1, math.ceil(self.count * fraction))
            index = int(np.searchsorted(cumulative, rank, side="left"))
            if self.bins <= 1:
                return self.minimum
            return self.minimum + (self.maximum - self.minimum) * (index / (self.bins - 1))

        return {
            "mean": round(self.total / self.count, 6),
            "p05": round(percentile(0.05), 6),
            "p50": round(percentile(0.50), 6),
            "p90": round(percentile(0.90), 6),
            "p95": round(percentile(0.95), 6),
            "min_positive": round(self.min_positive or 0.0, 6),
            "max": round(self.max_value or 0.0, 6),
        }


class _MomentAccumulator:
    """Bounded running moments for streaming-only render diagnostics."""

    def __init__(self) -> None:
        self.count = 0
        self.total = 0.0
        self.total_squares = 0.0

    def add(self, values: np.ndarray) -> None:
        flat = values.astype(np.float32, copy=False).ravel()
        self.count += int(flat.size)
        self.total += float(np.sum(flat, dtype=np.float64))
        self.total_squares += float(np.dot(flat.astype(np.float64), flat.astype(np.float64)))

    def mean_abs(self) -> float:
        return 0.0 if self.count == 0 else self.total / self.count

    def variance(self) -> float:
        if self.count == 0:
            return 0.0
        mean = self.total / self.count
        return max(0.0, self.total_squares / self.count - mean * mean)


def _stream_luminance(rgb: np.ndarray) -> np.ndarray:
    values = rgb.astype(np.float32, copy=False)
    return values[:, :, 0] * 0.2126 + values[:, :, 1] * 0.7152 + values[:, :, 2] * 0.0722


def _bmp_layout(width: int, height: int) -> tuple[bytes, int, int]:
    row_stride = ((width * 3 + 3) // 4) * 4
    image_bytes = row_stride * height
    file_bytes = BMP_HEADER_SIZE + image_bytes
    header = struct.pack("<2sIHHI", b"BM", file_bytes, 0, 0, BMP_HEADER_SIZE)
    header += struct.pack("<IIIHHIIIIII", 40, width, height, 1, 24, 0, image_bytes, 3780, 3780, 0, 0)
    return header, row_stride, file_bytes


def _initialise_bmp(stream: Any, width: int, height: int) -> tuple[int, int]:
    header, row_stride, file_bytes = _bmp_layout(width, height)
    stream.seek(0)
    stream.write(header)
    zero_row = b"\0" * row_stride
    for _ in range(height):
        stream.write(zero_row)
    return row_stride, file_bytes


def _write_bmp_tile(stream: Any, pixels: np.ndarray, *, output_left: int, output_top: int, output_height: int, row_stride: int) -> None:
    if pixels.ndim != 3 or pixels.shape[2] != 3 or pixels.dtype != np.uint8:
        raise RealPreviewError("stream-output tiles must be RGB uint8")
    height, width = pixels.shape[:2]
    for row in range(height):
        output_row = output_top + row
        bmp_row = output_height - 1 - output_row
        offset = BMP_HEADER_SIZE + bmp_row * row_stride + output_left * 3
        stream.seek(offset)
        stream.write(pixels[row, :, ::-1].tobytes())


def _tile_requests(request: PreviewRequest) -> list[tuple[int, int, PreviewRequest]]:
    width = round(request.width_m / request.meters_per_pixel)
    height = round(request.height_m / request.meters_per_pixel)
    tiles: list[tuple[int, int, PreviewRequest]] = []
    for top in range(0, height, request.tile_size_px):
        tile_height = min(request.tile_size_px, height - top)
        y_m = request.y_m + request.height_m - (top + tile_height) * request.meters_per_pixel
        for left in range(0, width, request.tile_size_px):
            tile_width = min(request.tile_size_px, width - left)
            x_m = request.x_m + left * request.meters_per_pixel
            tiles.append((
                left,
                top,
                PreviewRequest(
                    x_m,
                    y_m,
                    tile_width * request.meters_per_pixel,
                    tile_height * request.meters_per_pixel,
                    request.meters_per_pixel,
                    request.tile_size_px,
                ),
            ))
    return tiles


def _input_hashes(preset: RealPreviewPreset) -> dict[str, str]:
    return {name: sha256_file(preset.inputs[name]) for name in ("satellite", "mask", "height")}


def stream_real_preview_to_bmp_atomic(
    path: Path,
    preset: RealPreviewPreset,
    request: PreviewRequest,
    *,
    variant: str,
    tb_compat: bool,
    art_pass: bool = False,
    fail_after_tiles: int | None = None,
    reverse_traversal: bool = False,
) -> StreamingRenderReport:
    """Render the combined layer tile-by-tile into one atomically promoted BMP."""
    if variant != "original" and variant not in preset.variants:
        raise RealPreviewError(f"unknown real-preview variant {variant!r}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(preset.inputs["satellite"]) as satellite, Image.open(preset.inputs["mask"]) as mask:
            if satellite.mode != "RGB" or mask.mode != "RGB":
                raise RealPreviewError("satellite and mask must be RGB")
            if mask.size != satellite.size:
                raise RealPreviewError("mask dimensions must match satellite dimensions")
            box = _request_box(preset, request, satellite.size, allow_streaming=True)
    width, height = box[2] - box[0], box[3] - box[1]
    if variant == "original" and not tb_compat:
        mask_mode = "STRICT_RGB"
    else:
        mask_mode = "TB_COMPAT" if tb_compat else "STRICT_RGB"
    input_hashes_before = _input_hashes(preset)
    height_stats = parse_asc(preset.inputs["height"])
    height_row_offsets = _height_data_row_offsets(preset.inputs["height"], height_stats)
    tiles = _tile_requests(request)
    if reverse_traversal:
        tiles = list(reversed(tiles))
    context_counts = {"water": 0, "coast_transition": 0, "land": 0}
    adaptive_stats = _ScalarAccumulator(minimum=0.0, maximum=preset.art_pass.adaptive_max_multiplier)
    micro_energy = _MomentAccumulator()
    meso_moments = _MomentAccumulator()
    macro_moments = _MomentAccumulator()
    local_contrast = _MomentAccumulator()
    edge_magnitudes = _ScalarAccumulator(minimum=0.0, maximum=255.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    started = time.perf_counter()
    rendered_tiles = 0
    row_stride = 0
    file_bytes = 0
    try:
        with tempfile.NamedTemporaryFile(mode="w+b", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            row_stride, file_bytes = _initialise_bmp(stream, width, height)
            for left, top, tile_request in tiles:
                result = render_real_preview(
                    preset,
                    tile_request,
                    variant=variant,
                    tb_compat=tb_compat,
                    art_pass=art_pass,
                    height_stats=height_stats,
                    height_row_offsets=height_row_offsets,
                )
                _write_bmp_tile(stream, result.combined, output_left=left, output_top=top, output_height=height, row_stride=row_stride)
                if variant == "original":
                    # A pure crop deliberately avoids a height read in the normal
                    # renderer. The streaming report still records the same
                    # read-only terrain-context coverage as its comparisons.
                    context = _height_context(
                        preset,
                        tile_request,
                        stats=height_stats,
                        data_row_offsets=height_row_offsets,
                    )
                    context_counts["water"] += int(np.count_nonzero(context == WATER))
                    context_counts["coast_transition"] += int(np.count_nonzero(context == COAST_TRANSITION))
                    context_counts["land"] += int(np.count_nonzero(context == LAND))
                else:
                    for key in context_counts:
                        context_counts[key] += result.context_counts[key]
                micro_energy.add(np.abs(_stream_luminance(result.micro)))
                meso_moments.add(_stream_luminance(result.meso))
                macro_moments.add(_stream_luminance(result.structure))
                combined_luminance = _stream_luminance(result.combined)
                local_low = np.asarray(
                    Image.fromarray(np.rint(combined_luminance).clip(0, 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(1)),
                    dtype=np.float32,
                )
                local_contrast.add(np.abs(combined_luminance - local_low))
                edge_magnitudes.add(np.abs(np.diff(combined_luminance, axis=1)))
                edge_magnitudes.add(np.abs(np.diff(combined_luminance, axis=0)))
                if art_pass and variant != "original":
                    adaptive_stats.add(result.adaptive_strength)
                rendered_tiles += 1
                if fail_after_tiles is not None and rendered_tiles >= fail_after_tiles:
                    raise RealPreviewError("injected stream-output failure")
            stream.flush()
            os.fsync(stream.fileno())
        if temporary.stat().st_size != file_bytes:
            raise RealPreviewError("stream-output temporary BMP has an unexpected size")
        with Image.open(temporary) as image:
            if image.mode != "RGB" or image.size != (width, height):
                raise RealPreviewError("stream-output temporary BMP failed validation")
        input_hashes_after = _input_hashes(preset)
        if input_hashes_before != input_hashes_after:
            raise RealPreviewError("input hashes changed during stream-output render")
        os.replace(temporary, path)
        elapsed = time.perf_counter() - started
        return StreamingRenderReport(
            width=width,
            height=height,
            tile_size_px=request.tile_size_px,
            tile_count=rendered_tiles,
            elapsed_seconds=round(elapsed, 3),
            input_hashes_before=input_hashes_before,
            input_hashes_after=input_hashes_after,
            context_counts=context_counts,
            metrics={
                "row_stride_bytes": float(row_stride),
                "bmp_file_bytes": float(file_bytes),
                "largest_combined_tile_rgb_mib": round(request.tile_size_px * request.tile_size_px * 3 / (1024 * 1024), 4),
                "frequency_metric_basis": "TerrainSatGen render components; local contrast and edges are tile-local",
                "micro_energy_mean_abs": round(micro_energy.mean_abs(), 6),
                "meso_variance": round(meso_moments.variance(), 6),
                "macro_variance": round(macro_moments.variance(), 6),
                "local_contrast_mean_abs": round(local_contrast.mean_abs(), 6),
                "edge_mean_abs_gradient": edge_magnitudes.finish()["mean"],
                "edge_p90_abs_gradient": edge_magnitudes.finish()["p90"],
            },
            adaptive=adaptive_stats.finish() if art_pass and variant != "original" else None,
            memory_model={
                "classification": "BOUNDED",
                "depends_on": "tile_size_px plus filter and feather halos, not final output area",
                "normal_limit_pixels": NORMAL_MAX_REAL_PIXELS,
                "streaming_max_dimension": STREAMING_MAX_DIMENSION,
            },
        )
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def write_bmp_atomic(path: Path, pixels: np.ndarray) -> None:
    buffer = io.BytesIO()
    Image.fromarray(pixels, mode="RGB").save(buffer, format="BMP")
    write_bytes_atomic(path, buffer.getvalue())
