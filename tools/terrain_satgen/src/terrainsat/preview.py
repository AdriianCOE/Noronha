"""Synthetic-only tiled procedural satellite-preview renderer."""

from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
import tomllib
from typing import Any

import numpy as np
from PIL import Image

from .procedural import stable_seed, value_noise
from .safety import write_bytes_atomic


MAX_SYNTHETIC_PIXELS = 2048 * 2048


class PreviewError(ValueError):
    """A synthetic preview preset or request is invalid."""


@dataclass(frozen=True)
class Band:
    enabled: bool
    cell_size_m: float
    strength: float


@dataclass(frozen=True)
class Material:
    name: str
    rgb: tuple[int, int, int]
    seed: str
    tint: tuple[float, float, float]


@dataclass(frozen=True)
class SyntheticPreset:
    world_seed: str
    bands: dict[str, Band]
    materials: tuple[Material, ...]
    region_cell_size_m: float


@dataclass(frozen=True)
class PreviewRequest:
    x_m: float
    y_m: float
    width_m: float
    height_m: float
    meters_per_pixel: float
    tile_size_px: int = 256


@dataclass(frozen=True)
class PreviewResult:
    base: np.ndarray
    macro: np.ndarray
    medium: np.ndarray
    local: np.ndarray
    combined: np.ndarray
    surface_map: np.ndarray
    clipped_pixel_count: int


def load_synthetic_preset(path: Path) -> SyntheticPreset:
    with path.open("rb") as stream:
        raw = tomllib.load(stream)
    if raw.get("mode") != "synthetic":
        raise PreviewError("preview accepts only presets with mode = \"synthetic\"")
    synthetic = raw.get("synthetic")
    if not isinstance(synthetic, dict):
        raise PreviewError("synthetic preset requires a [synthetic] table")
    bands_raw = synthetic.get("bands")
    materials_raw = synthetic.get("materials")
    if not isinstance(bands_raw, dict) or not isinstance(materials_raw, dict):
        raise PreviewError("synthetic preset requires bands and materials")
    bands: dict[str, Band] = {}
    for name in ("macro", "medium", "local"):
        item = bands_raw.get(name)
        if not isinstance(item, dict):
            raise PreviewError(f"synthetic preset is missing band {name}")
        bands[name] = Band(
            enabled=bool(item.get("enabled", True)),
            cell_size_m=float(item["cell_size_m"]),
            strength=float(item["strength"]),
        )
        if bands[name].cell_size_m <= 0:
            raise PreviewError(f"band {name} cell_size_m must be positive")
    materials: list[Material] = []
    for name, item in materials_raw.items():
        if not isinstance(item, dict):
            raise PreviewError(f"material {name} must be a table")
        rgb = tuple(item.get("rgb", ()))
        tint = tuple(item.get("tint", (1.0, 1.0, 1.0)))
        if len(rgb) != 3 or any(not isinstance(value, int) or value < 0 or value > 255 for value in rgb):
            raise PreviewError(f"material {name} rgb must contain three bytes")
        if len(tint) != 3:
            raise PreviewError(f"material {name} tint must have three values")
        materials.append(Material(name, rgb, str(item["seed"]), tuple(float(value) for value in tint)))
    if not materials:
        raise PreviewError("synthetic preset needs at least one material")
    return SyntheticPreset(
        world_seed=str(synthetic["world_seed"]),
        bands=bands,
        materials=tuple(materials),
        region_cell_size_m=float(synthetic.get("region_cell_size_m", 900.0)),
    )


def _coordinates(request: PreviewRequest) -> tuple[np.ndarray, np.ndarray, int, int]:
    if min(request.width_m, request.height_m, request.meters_per_pixel) <= 0:
        raise PreviewError("width, height and meters-per-pixel must be positive")
    width_px = round(request.width_m / request.meters_per_pixel)
    height_px = round(request.height_m / request.meters_per_pixel)
    if width_px <= 0 or height_px <= 0:
        raise PreviewError("preview dimensions resolve to zero pixels")
    if width_px * height_px > MAX_SYNTHETIC_PIXELS:
        raise PreviewError(
            f"synthetic preview exceeds the {MAX_SYNTHETIC_PIXELS:,}-pixel safety limit"
        )
    if not np.isclose(width_px * request.meters_per_pixel, request.width_m) or not np.isclose(
        height_px * request.meters_per_pixel, request.height_m
    ):
        raise PreviewError("width and height must align to meters-per-pixel")
    # Pixel center convention: origin + (pixel + 0.5) * metres-per-pixel.
    xs = request.x_m + (np.arange(width_px, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
    ys = request.y_m + (np.arange(height_px, dtype=np.float32) + np.float32(0.5)) * np.float32(request.meters_per_pixel)
    return xs, ys, width_px, height_px


def _surface_indices(preset: SyntheticPreset, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    region = value_noise(
        xs, ys, cell_size_m=preset.region_cell_size_m, seed=stable_seed(preset.world_seed, "regions")
    )
    count = len(preset.materials)
    return np.minimum((region * np.float32(count)).astype(np.uint8), count - 1)


def _render_tile(preset: SyntheticPreset, xs: np.ndarray, ys: np.ndarray) -> PreviewResult:
    surface_map = _surface_indices(preset, xs, ys)
    height, width = surface_map.shape
    base = np.empty((height, width, 3), dtype=np.float32)
    layers = {name: np.zeros_like(base) for name in ("macro", "medium", "local")}
    for index, material in enumerate(preset.materials):
        selector = surface_map == index
        base[selector] = np.asarray(material.rgb, dtype=np.float32)
        for band_name, band in preset.bands.items():
            if not band.enabled:
                continue
            noise = value_noise(
                xs,
                ys,
                cell_size_m=band.cell_size_m,
                seed=stable_seed(preset.world_seed, material.seed, band_name),
            )
            contribution = ((noise - np.float32(0.5)) * np.float32(2.0 * band.strength))[..., None]
            layers[band_name][selector] = contribution[selector] * np.asarray(material.tint, dtype=np.float32)
    unclamped = base + layers["macro"] + layers["medium"] + layers["local"]
    combined = np.clip(unclamped, 0, 255).astype(np.float32)
    return PreviewResult(
        base=base,
        macro=layers["macro"],
        medium=layers["medium"],
        local=layers["local"],
        combined=combined,
        surface_map=surface_map,
        clipped_pixel_count=int(np.count_nonzero(np.any((unclamped < 0) | (unclamped > 255), axis=2))),
    )


def render_preview(preset: SyntheticPreset, request: PreviewRequest) -> PreviewResult:
    """Render in tiles with no halo; fields depend only on absolute pixel centres."""
    xs, ys, width, height = _coordinates(request)
    if request.tile_size_px <= 0:
        raise PreviewError("tile size must be positive")
    rgb_layers = {name: np.empty((height, width, 3), dtype=np.float32) for name in ("base", "macro", "medium", "local", "combined")}
    surface_map = np.empty((height, width), dtype=np.uint8)
    clipped = 0
    for top in range(0, height, request.tile_size_px):
        for left in range(0, width, request.tile_size_px):
            tile = _render_tile(
                preset,
                xs[left : left + request.tile_size_px],
                ys[top : top + request.tile_size_px],
            )
            row = slice(top, top + tile.surface_map.shape[0])
            col = slice(left, left + tile.surface_map.shape[1])
            for name, target in rgb_layers.items():
                target[row, col] = getattr(tile, name)
            surface_map[row, col] = tile.surface_map
            clipped += tile.clipped_pixel_count
    return PreviewResult(**rgb_layers, surface_map=surface_map, clipped_pixel_count=clipped)


def display_layer(result: PreviewResult, name: str, materials: tuple[Material, ...]) -> np.ndarray:
    if name == "surface_map":
        palette = np.asarray([material.rgb for material in materials], dtype=np.uint8)
        return palette[result.surface_map]
    if name == "combined" or name == "base":
        return np.rint(getattr(result, name)).clip(0, 255).astype(np.uint8)
    # Signed contributions are visualized around neutral grey; combined remains the physical output.
    return np.rint(getattr(result, name) + np.float32(128.0)).clip(0, 255).astype(np.uint8)


def write_bmp_atomic(path: Path, pixels: np.ndarray) -> None:
    buffer = io.BytesIO()
    Image.fromarray(pixels, mode="RGB").save(buffer, format="BMP")
    write_bytes_atomic(path, buffer.getvalue())
