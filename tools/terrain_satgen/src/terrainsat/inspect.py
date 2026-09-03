"""Read-only orchestration for the TerrainSatGen inspect command."""

from __future__ import annotations

import hashlib
import io
import math
import os
import time
import tomllib
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any

import numpy as np
from PIL import Image
from PIL import ImageDraw

from . import __version__
from .parsers import AscStats, Surface, parse_asc, parse_layers
from .safety import write_bytes_atomic, write_json_atomic


class InspectionError(ValueError):
    """The preset or an input prevents a complete inspection."""


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_preset(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        preset = tomllib.load(stream)
    allowed_sections = {"world", "inputs", "mask", "terrain_builder", "real_preview"}
    unknown_sections = sorted(set(preset) - allowed_sections)
    if unknown_sections:
        raise InspectionError("Unknown preset sections: " + ", ".join(unknown_sections))
    for required in {"world", "inputs", "mask"}:
        if required not in preset or not isinstance(preset[required], dict):
            raise InspectionError(f"Preset requires table [{required}]")
    _reject_unknown(preset["world"], {"size_m"}, "world")
    _reject_unknown(
        preset["inputs"],
        {"layers", "height", "satellite", "mask", "vanilla_root"},
        "inputs",
    )
    _reject_unknown(preset["mask"], {"unknown_color_policy", "tile_rows", "color_aliases"}, "mask")
    if "terrain_builder" in preset:
        if not isinstance(preset["terrain_builder"], dict):
            raise InspectionError("Preset [terrain_builder] must be a table")
        _reject_unknown(
            preset["terrain_builder"],
            {
                "tile_texture_px",
                "core_stride_px",
                "border_px",
                "actual_shared_overlap_px",
                "tiles_per_row",
                "material_limit",
            },
            "terrain_builder",
        )
    if "real_preview" in preset and not isinstance(preset["real_preview"], dict):
        raise InspectionError("Preset [real_preview] must be a table")
    required_inputs = {"layers", "height", "satellite", "mask", "vanilla_root"}
    missing_inputs = sorted(required_inputs - preset["inputs"].keys())
    if missing_inputs:
        raise InspectionError("Missing preset inputs: " + ", ".join(missing_inputs))
    aliases = preset["mask"].get("color_aliases", {})
    if not isinstance(aliases, dict):
        raise InspectionError("mask.color_aliases must be a table")
    for rgb, surface in aliases.items():
        _parse_rgb_key(rgb)
        if not isinstance(surface, str) or not surface:
            raise InspectionError(f"Alias {rgb!r} must name a surface")
    if preset["mask"].get("unknown_color_policy") not in {"error", "warning"}:
        raise InspectionError("mask.unknown_color_policy must be 'error' or 'warning'")
    tile_rows = preset["mask"].get("tile_rows", 256)
    if not isinstance(tile_rows, int) or tile_rows <= 0:
        raise InspectionError("mask.tile_rows must be a positive integer")
    _world_size(preset["world"].get("size_m"))
    return preset


def _parse_rgb_key(value: Any) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise InspectionError("mask.color_aliases keys must be RGB strings such as '255,175,23'")
    parts = value.split(",")
    if len(parts) != 3:
        raise InspectionError(f"Invalid alias RGB {value!r}")
    try:
        rgb = tuple(int(part.strip()) for part in parts)
    except ValueError as error:
        raise InspectionError(f"Invalid alias RGB {value!r}") from error
    if any(channel < 0 or channel > 255 for channel in rgb):
        raise InspectionError(f"Alias RGB outside 0..255: {value!r}")
    return rgb  # type: ignore[return-value]


def _color_aliases(mask: dict[str, Any], surfaces: list[Surface]) -> dict[tuple[int, int, int], str]:
    exact = {surface.rgb: surface.name for surface in surfaces}
    names = {surface.name for surface in surfaces}
    aliases: dict[tuple[int, int, int], str] = {}
    for raw_rgb, surface in mask.get("color_aliases", {}).items():
        rgb = _parse_rgb_key(raw_rgb)
        if surface not in names:
            raise InspectionError(f"Alias {raw_rgb!r} references unknown surface {surface!r}")
        if rgb in exact:
            raise InspectionError(f"Alias {raw_rgb!r} conflicts with exact Legend RGB for {exact[rgb]}")
        if rgb in aliases:
            raise InspectionError(f"Duplicate alias RGB {raw_rgb!r}")
        aliases[rgb] = surface
    return aliases


def _reject_unknown(table: dict[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise InspectionError(f"Unknown keys in [{name}]: " + ", ".join(unknown))


def _world_size(value: Any) -> tuple[float, float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = (float(value), float(value))
    elif isinstance(value, list) and len(value) == 2 and all(
        isinstance(item, (int, float)) and not isinstance(item, bool) for item in value
    ):
        result = (float(value[0]), float(value[1]))
    else:
        raise InspectionError("world.size_m must be a positive number or [width, height]")
    if result[0] <= 0 or result[1] <= 0:
        raise InspectionError("world.size_m values must be positive")
    return result


def _input_paths(preset: dict[str, Any]) -> dict[str, Path]:
    paths = {
        name: Path(preset["inputs"][name])
        for name in ("layers", "height", "satellite", "mask")
    }
    missing = [f"{name}={path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        raise InspectionError("Missing input files: " + ", ".join(missing))
    vanilla_root = Path(preset["inputs"]["vanilla_root"])
    if not vanilla_root.is_dir():
        raise InspectionError(f"Missing vanilla root: {vanilla_root}")
    paths["vanilla_root"] = vanilla_root
    return paths


def _raster_metadata(path: Path) -> dict[str, Any]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            return {
                "path": str(path),
                "format": image.format,
                "mode": image.mode,
                "width": image.width,
                "height": image.height,
                "file_bytes": path.stat().st_size,
            }


def _scan_mask(
    path: Path,
    surfaces: list[Surface],
    aliases: dict[tuple[int, int, int], str],
    tile_rows: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    known = {surface.rgb: surface.name for surface in surfaces}
    counts: Counter[tuple[int, int, int]] = Counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.mode != "RGB":
                raise InspectionError(f"Mask mode must be RGB, found {image.mode}")
            width, height = image.size
            for top in range(0, height, tile_rows):
                bottom = min(top + tile_rows, height)
                rgb = np.asarray(image.crop((0, top, width, bottom)), dtype=np.uint8)
                packed = (
                    (rgb[:, :, 0].astype(np.uint32) << 16)
                    | (rgb[:, :, 1].astype(np.uint32) << 8)
                    | rgb[:, :, 2].astype(np.uint32)
                )
                values, frequencies = np.unique(packed, return_counts=True)
                counts.update(
                    {
                        (int(value >> 16), int((value >> 8) & 255), int(value & 255)): int(count)
                        for value, count in zip(values, frequencies)
                    }
                )
    total = width * height
    usage: list[dict[str, Any]] = []
    for rgb, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        entry: dict[str, Any] = {
            "rgb": list(rgb),
            "pixel_count": count,
            "percentage": count / total * 100,
            "status": "exact" if rgb in known else "explicit_alias" if rgb in aliases else "unknown",
        }
        if rgb in known:
            entry["surface"] = known[rgb]
        elif rgb in aliases:
            entry["surface"] = aliases[rgb]
        else:
            distance, nearest_rgb, nearest_surface = min(
                (
                    math.dist(rgb, candidate_rgb),
                    candidate_rgb,
                    candidate_surface,
                )
                for candidate_rgb, candidate_surface in known.items()
            )
            entry["nearest"] = {
                "surface": nearest_surface,
                "rgb": list(nearest_rgb),
                "distance": distance,
                "diagnostic_only": True,
            }
        usage.append(entry)
    primary_bytes = width * min(tile_rows, height) * (3 + 4)
    scan = {
        "unique_color_count": len(usage),
        "unknown_color_count": sum(entry["status"] == "unknown" for entry in usage),
        "unknown_pixel_count": sum(
            entry["pixel_count"] for entry in usage if entry["status"] == "unknown"
        ),
        "tile_rows": tile_rows,
        "primary_tile_buffers_mib": primary_bytes / (1024 * 1024),
    }
    return usage, scan


def _positive_int(table: dict[str, Any], name: str) -> int:
    value = table.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InspectionError(f"terrain_builder.{name} must be a positive integer")
    return value


def _terrain_builder_sampler(
    preset: dict[str, Any], width: int, height: int
) -> dict[str, int]:
    if "terrain_builder" not in preset:
        raise InspectionError("Surface segment audit requires a [terrain_builder] table")
    table = preset["terrain_builder"]
    tile_texture = _positive_int(table, "tile_texture_px")
    stride = _positive_int(table, "core_stride_px")
    border = table.get("border_px")
    if not isinstance(border, int) or isinstance(border, bool) or border < 0:
        raise InspectionError("terrain_builder.border_px must be a non-negative integer")
    actual_overlap = _positive_int(table, "actual_shared_overlap_px")
    configured_tiles = _positive_int(table, "tiles_per_row")
    material_limit = _positive_int(table, "material_limit")
    if stride > tile_texture or tile_texture != stride + 2 * border:
        raise InspectionError("Terrain Builder tile_texture_px must equal core_stride_px + 2 * border_px")
    if actual_overlap != 2 * border or actual_overlap != tile_texture - stride:
        raise InspectionError("Terrain Builder actual_shared_overlap_px must equal 2 * border_px")
    tiles_x = math.ceil(width / stride)
    tiles_y = math.ceil(height / stride)
    if configured_tiles != tiles_x or configured_tiles != tiles_y:
        raise InspectionError(
            f"Terrain Builder tiles_per_row={configured_tiles} does not match raster geometry {tiles_x} x {tiles_y}"
        )
    return {
        "tile_texture_px": tile_texture,
        "core_stride_px": stride,
        "border_px": border,
        "actual_shared_overlap_px": actual_overlap,
        "tiles_x": tiles_x,
        "tiles_y": tiles_y,
        "material_limit": material_limit,
    }


def _bounds(left: int, top: int, right: int, bottom: int) -> dict[str, int]:
    return {"left": left, "top": top, "right": right, "bottom": bottom}


def segment_window_model(width: int, height: int, sampler: dict[str, int]) -> list[dict[str, Any]]:
    """Return half-open core and overlap windows derived from recorded TB samplers."""

    stride = sampler["core_stride_px"]
    border = sampler["border_px"]
    windows: list[dict[str, Any]] = []
    for tile_y in range(sampler["tiles_y"]):
        core_top = tile_y * stride
        core_bottom = min(core_top + stride, height)
        for tile_x in range(sampler["tiles_x"]):
            core_left = tile_x * stride
            core_right = min(core_left + stride, width)
            windows.append(
                {
                    "tile_x": tile_x,
                    "tile_y": tile_y,
                    "core_bounds": _bounds(core_left, core_top, core_right, core_bottom),
                    "bounds": _bounds(
                        max(0, core_left - border),
                        max(0, core_top - border),
                        min(width, core_right + border),
                        min(height, core_bottom + border),
                    ),
                }
            )
    return windows


def _surface_histogram(
    pixels: np.ndarray,
    known: dict[tuple[int, int, int], str],
    aliases: dict[tuple[int, int, int], str],
) -> tuple[list[str], list[list[int]], list[dict[str, Any]]]:
    packed = (
        (pixels[:, :, 0].astype(np.uint32) << 16)
        | (pixels[:, :, 1].astype(np.uint32) << 8)
        | pixels[:, :, 2].astype(np.uint32)
    )
    total = pixels.shape[0] * pixels.shape[1]
    surfaces: dict[str, dict[tuple[tuple[int, int, int], str], int]] = {}
    unknown: list[list[int]] = []
    for value, count in zip(*np.unique(packed, return_counts=True)):
        rgb = (int(value >> 16), int((value >> 8) & 255), int(value & 255))
        status = "exact" if rgb in known else "explicit_alias" if rgb in aliases else "unknown"
        surface = known.get(rgb) or aliases.get(rgb)
        if surface is None:
            unknown.append(list(rgb))
        else:
            sources = surfaces.setdefault(surface, {})
            sources[(rgb, status)] = int(count)
    histogram = [
        {
            "surface": surface,
            "pixel_count": sum(sources.values()),
            "percentage": sum(sources.values()) / total * 100,
            "sources": [
                {"rgb": list(rgb), "status": status, "pixel_count": count}
                for (rgb, status), count in sorted(sources.items())
            ],
        }
        for surface, sources in sorted(surfaces.items())
    ]
    return sorted(surfaces), unknown, histogram


def audit_surface_segments(
    path: Path,
    surfaces: list[Surface],
    aliases: dict[tuple[int, int, int], str],
    sampler: dict[str, int],
) -> dict[str, Any]:
    """Audit each Terrain Builder segment window without modifying the mask."""

    known = {surface.rgb: surface.name for surface in surfaces}
    segments: list[dict[str, Any]] = []
    started = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.mode != "RGB":
                raise InspectionError(f"Mask mode must be RGB, found {image.mode}")
            width, height = image.size
            for window in segment_window_model(image.width, image.height, sampler):
                bounds = window["bounds"]
                core = window["core_bounds"]
                pixels = np.asarray(
                    image.crop((bounds["left"], bounds["top"], bounds["right"], bounds["bottom"])),
                    dtype=np.uint8,
                )
                core_pixels = pixels[
                    core["top"] - bounds["top"] : core["bottom"] - bounds["top"],
                    core["left"] - bounds["left"] : core["right"] - bounds["left"],
                ]
                core_surfaces, core_unknown, core_histogram = _surface_histogram(core_pixels, known, aliases)
                window_surfaces, window_unknown, window_histogram = _surface_histogram(pixels, known, aliases)
                unknown_rgb = sorted({tuple(rgb) for rgb in core_unknown + window_unknown})
                status = (
                    "UNKNOWN"
                    if unknown_rgb
                    else "FAIL"
                    if len(window_surfaces) > sampler["material_limit"]
                    else "PASS"
                )
                segments.append(
                    {
                        **window,
                        "surfaces_core": core_surfaces,
                        "surfaces_with_overlap": window_surfaces,
                        "surfaces_overlap_only": sorted(set(window_surfaces) - set(core_surfaces)),
                        "histogram_core": core_histogram,
                        "histogram_with_overlap": window_histogram,
                        "material_count": len(window_surfaces),
                        "unknown_rgb": [list(rgb) for rgb in unknown_rgb],
                        "status": status,
                    }
                )
    maximum = max((segment["material_count"] for segment in segments), default=0)
    worst = [
        {key: segment[key] for key in ("tile_x", "tile_y", "bounds", "material_count", "status")}
        for segment in segments
        if segment["material_count"] == maximum
    ][:16]
    return {
        "model": "TB_SEGMENT_WINDOW_MODEL",
        "source_size": {"width": width, "height": height},
        "tile_texture_px": sampler["tile_texture_px"],
        "core_stride_px": sampler["core_stride_px"],
        "border_per_side_px": sampler["border_px"],
        "actual_shared_overlap_px": sampler["actual_shared_overlap_px"],
        "tiles": {"x": sampler["tiles_x"], "y": sampler["tiles_y"], "total": len(segments)},
        "material_limit": sampler["material_limit"],
        "pass_count": sum(segment["status"] == "PASS" for segment in segments),
        "fail_count": sum(segment["status"] == "FAIL" for segment in segments),
        "unknown_count": sum(segment["status"] == "UNKNOWN" for segment in segments),
        "maximum_material_count": maximum,
        "worst_segments": worst,
        "segments": segments,
        "timing_seconds": time.perf_counter() - started,
    }


_DIAGNOSTIC_COLORS = (
    (51, 160, 44),
    (31, 120, 180),
    (227, 26, 28),
    (255, 127, 0),
    (106, 61, 154),
    (166, 206, 227),
)


def _write_image_atomic(path: Path, image: Image.Image, image_format: str) -> None:
    encoded = io.BytesIO()
    image.save(encoded, format=image_format)
    write_bytes_atomic(path, encoded.getvalue())


def _open_large_raster(path: Path) -> Image.Image:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
        return Image.open(path)


def _diagnostic_mask_image(
    pixels: np.ndarray,
    known: dict[tuple[int, int, int], str],
    aliases: dict[tuple[int, int, int], str],
    histogram: list[dict[str, Any]],
) -> Image.Image:
    colors = {
        entry["surface"]: _DIAGNOSTIC_COLORS[index % len(_DIAGNOSTIC_COLORS)]
        for index, entry in enumerate(histogram)
    }
    packed = (
        (pixels[:, :, 0].astype(np.uint32) << 16)
        | (pixels[:, :, 1].astype(np.uint32) << 8)
        | pixels[:, :, 2].astype(np.uint32)
    )
    resolved = np.zeros_like(pixels)
    for value in np.unique(packed):
        rgb = (int(value >> 16), int((value >> 8) & 255), int(value & 255))
        surface = known.get(rgb) or aliases.get(rgb)
        if surface is not None:
            resolved[packed == value] = colors[surface]
    legend_height = 24 * max(1, len(histogram)) + 8
    canvas = Image.new("RGB", (max(resolved.shape[1], 360), resolved.shape[0] + legend_height), "white")
    canvas.paste(Image.fromarray(resolved, "RGB"), (0, 0))
    draw = ImageDraw.Draw(canvas)
    for index, entry in enumerate(histogram):
        top = resolved.shape[0] + 4 + index * 24
        draw.rectangle((4, top, 20, top + 16), fill=colors[entry["surface"]])
        sources = ", ".join(
            f"{source['rgb']} {source['status']}" for source in entry["sources"]
        )
        draw.text((28, top + 2), f"{entry['surface']}: {sources}", fill="black")
    return canvas


def _highlight_surfaces(segment: dict[str, Any]) -> tuple[list[str], str]:
    overlap_only = segment["surfaces_overlap_only"]
    if overlap_only:
        return overlap_only, "introduced_by_overlap"
    histogram = segment["histogram_with_overlap"]
    minimum = min(entry["pixel_count"] for entry in histogram)
    return [entry["surface"] for entry in histogram if entry["pixel_count"] == minimum], "rarest_surface"


def write_segment_diagnostics(
    preset_path: Path,
    report: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    """Write read-only QA crops for failed TB-compatible segment windows."""

    if report["terrain_builder_compatibility"]["mode"] != "TB_COMPAT":
        raise InspectionError("Segment diagnostics require TB_COMPAT")
    audit = report["surface_segment_audit"]
    if audit is None:
        raise InspectionError("Segment diagnostics require a surface segment audit")
    preset = load_preset(preset_path)
    paths = _input_paths(preset)
    surfaces = parse_layers(paths["layers"])
    aliases = _color_aliases(preset["mask"], surfaces)
    known = {surface.rgb: surface.name for surface in surfaces}
    failed = [segment for segment in audit["segments"] if segment["status"] == "FAIL"]
    output_root.mkdir(parents=True, exist_ok=True)
    manifests: list[dict[str, Any]] = []
    with _open_large_raster(paths["mask"]) as mask, _open_large_raster(paths["satellite"]) as satellite:
        for segment in failed:
            bounds = segment["bounds"]
            core = segment["core_bounds"]
            crop_box = (bounds["left"], bounds["top"], bounds["right"], bounds["bottom"])
            mask_crop = mask.crop(crop_box).convert("RGB")
            satellite_crop = satellite.crop(crop_box).convert("RGB")
            pixels = np.asarray(mask_crop, dtype=np.uint8)
            tile_root = output_root / f"tile_{segment['tile_x']}_{segment['tile_y']}"
            tile_root.mkdir(parents=True, exist_ok=True)
            raw_path = tile_root / "mask_raw.bmp"
            resolved_path = tile_root / "mask_resolved.png"
            satellite_path = tile_root / "satellite_crop.bmp"
            overlay_path = tile_root / "overlay_bounds.png"
            report_path = tile_root / "report.json"
            _write_image_atomic(raw_path, mask_crop, "BMP")
            _write_image_atomic(
                resolved_path,
                _diagnostic_mask_image(pixels, known, aliases, segment["histogram_with_overlap"]),
                "PNG",
            )
            _write_image_atomic(satellite_path, satellite_crop, "BMP")
            highlighted, highlight_reason = _highlight_surfaces(segment)
            overlay = satellite_crop.convert("RGBA")
            overlay_pixels = np.asarray(overlay).copy()
            packed = (
                (pixels[:, :, 0].astype(np.uint32) << 16)
                | (pixels[:, :, 1].astype(np.uint32) << 8)
                | pixels[:, :, 2].astype(np.uint32)
            )
            highlighted_rgb = {
                tuple(source["rgb"])
                for entry in segment["histogram_with_overlap"]
                if entry["surface"] in highlighted
                for source in entry["sources"]
            }
            highlight_mask = np.zeros(packed.shape, dtype=bool)
            for rgb in highlighted_rgb:
                value = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
                highlight_mask |= packed == value
            overlay_pixels[highlight_mask, :3] = (255, 0, 255)
            overlay_pixels[highlight_mask, 3] = 128
            overlay = Image.fromarray(overlay_pixels, "RGBA")
            draw = ImageDraw.Draw(overlay)
            draw.rectangle((0, 0, overlay.width - 1, overlay.height - 1), outline="blue", width=2)
            draw.rectangle(
                (
                    core["left"] - bounds["left"],
                    core["top"] - bounds["top"],
                    core["right"] - bounds["left"] - 1,
                    core["bottom"] - bounds["top"] - 1,
                ),
                outline="red",
                width=2,
            )
            _write_image_atomic(overlay_path, overlay, "PNG")
            manifest = {
                "author_decision": "AUTHOR_DECISION_REQUIRED",
                "tile": {"x": segment["tile_x"], "y": segment["tile_y"]},
                "highlighted_surfaces": highlighted,
                "highlight_reason": highlight_reason,
                "diagnostic_note": "mask_resolved.png is diagnostic only and is not a Terrain Builder mask.",
                "outputs": {
                    "mask_raw": raw_path.name,
                    "mask_resolved": resolved_path.name,
                    "satellite_crop": satellite_path.name,
                    "overlay_bounds": overlay_path.name,
                },
                **segment,
            }
            write_json_atomic(report_path, manifest)
            manifests.append(manifest)
    summary = {"failed_tiles": manifests, "output_root": str(output_root)}
    write_json_atomic(output_root / "report.json", summary)
    return summary


def _resolve_vanilla(reference: str, root: Path) -> Path:
    windows_path = PureWindowsPath(reference)
    if windows_path.is_absolute() or windows_path.drive or ".." in windows_path.parts:
        raise InspectionError(f"Unsafe vanilla reference: {reference}")
    return root.joinpath(*windows_path.parts)


def _vanilla_checks(surfaces: list[Surface], root: Path) -> dict[str, Any]:
    missing: list[dict[str, str]] = []
    for surface in surfaces:
        for kind, reference in (("texture", surface.texture), ("material", surface.material)):
            resolved = _resolve_vanilla(reference, root)
            if not resolved.is_file():
                missing.append(
                    {
                        "surface": surface.name,
                        "kind": kind,
                        "reference": reference,
                        "resolved": str(resolved),
                    }
                )
    return {
        "texture_refs": len(surfaces),
        "material_refs": len(surfaces),
        "existing_refs": len(surfaces) * 2 - len(missing),
        "missing_paths": missing,
    }


def _asc_payload(stats: AscStats, path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "ncols": stats.ncols,
        "nrows": stats.nrows,
        "xllcorner": stats.xllcorner,
        "yllcorner": stats.yllcorner,
        "cellsize": stats.cellsize,
        "nodata_value": stats.nodata_value,
        "value_count": stats.value_count,
        "nodata_count": stats.nodata_count,
        "minimum": stats.minimum,
        "maximum": stats.maximum,
        "mean": stats.mean,
        "extent": stats.extent,
    }


def inspect_preset(
    preset_path: Path,
    *,
    tb_compat: bool = False,
    surface_segment_audit: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    timings: dict[str, float] = {}

    step = time.perf_counter()
    preset = load_preset(preset_path)
    paths = _input_paths(preset)
    timings["preset"] = time.perf_counter() - step

    step = time.perf_counter()
    surfaces = parse_layers(paths["layers"])
    configured_aliases = _color_aliases(preset["mask"], surfaces)
    active_aliases = configured_aliases if tb_compat else {}
    timings["layers"] = time.perf_counter() - step

    step = time.perf_counter()
    heightmap = parse_asc(paths["height"])
    timings["heightmap"] = time.perf_counter() - step

    step = time.perf_counter()
    satellite = _raster_metadata(paths["satellite"])
    mask = _raster_metadata(paths["mask"])
    timings["raster_metadata"] = time.perf_counter() - step

    checks: list[dict[str, str]] = []
    for name, metadata in (("satellite", satellite), ("mask", mask)):
        supported_format = metadata["format"] in {"BMP", "PNG"}
        checks.append(
            {
                "status": "PASS" if supported_format else "FAIL",
                "code": f"{name}_format",
                "message": (
                    f"format is {metadata['format']}"
                    if supported_format
                    else f"unsupported format {metadata['format']}; expected BMP or PNG"
                ),
            }
        )
        if metadata["mode"] == "RGB":
            checks.append({"status": "PASS", "code": f"{name}_rgb", "message": "mode is RGB"})
        else:
            checks.append(
                {
                    "status": "FAIL",
                    "code": f"{name}_rgb",
                    "message": f"mode is {metadata['mode']}; expected RGB",
                }
            )
    dimensions_match = (satellite["width"], satellite["height"]) == (
        mask["width"],
        mask["height"],
    )
    checks.append(
        {
            "status": "PASS" if dimensions_match else "FAIL",
            "code": "raster_dimensions",
            "message": (
                "satellite and mask dimensions match"
                if dimensions_match
                else "satellite and mask dimensions differ"
            ),
        }
    )

    world_width, world_height = _world_size(preset["world"]["size_m"])
    meters_per_pixel = {
        "x": world_width / satellite["width"],
        "y": world_height / satellite["height"],
    }
    raster_aspect = satellite["width"] / satellite["height"]
    world_aspect = world_width / world_height
    aspect_matches = math.isclose(raster_aspect, world_aspect, rel_tol=0, abs_tol=1e-12)
    checks.append(
        {
            "status": "PASS" if aspect_matches else "FAIL",
            "code": "world_raster_aspect",
            "message": "world and raster aspect ratios match" if aspect_matches else "world and raster aspect ratios differ",
        }
    )
    height_extent_matches = math.isclose(heightmap.ncols * heightmap.cellsize, world_width) and math.isclose(
        heightmap.nrows * heightmap.cellsize, world_height
    )
    checks.append(
        {
            "status": "PASS" if height_extent_matches else "FAIL",
            "code": "heightmap_world_extent",
            "message": "heightmap extent matches world size" if height_extent_matches else "heightmap extent differs from world size",
        }
    )

    step = time.perf_counter()
    mask_usage, mask_scan = _scan_mask(
        paths["mask"], surfaces, active_aliases, preset["mask"]["tile_rows"]
    )
    timings["mask_scan"] = time.perf_counter() - step
    unknown_status = (
        "FAIL"
        if mask_scan["unknown_color_count"] and preset["mask"]["unknown_color_policy"] == "error"
        else "WARNING"
        if mask_scan["unknown_color_count"]
        else "PASS"
    )
    checks.append(
        {
            "status": unknown_status,
            "code": "mask_colors",
            "message": f"{mask_scan['unknown_color_count']} unknown RGB colors across {mask_scan['unknown_pixel_count']} pixels",
        }
    )

    segment_audit: dict[str, Any] | None = None
    if surface_segment_audit:
        step = time.perf_counter()
        sampler = _terrain_builder_sampler(preset, mask["width"], mask["height"])
        segment_audit = audit_surface_segments(paths["mask"], surfaces, active_aliases, sampler)
        timings["surface_segment_audit"] = time.perf_counter() - step
        audit_status = (
            "FAIL"
            if segment_audit["fail_count"] or segment_audit["unknown_count"]
            else "PASS"
        )
        checks.append(
            {
                "status": audit_status,
                "code": "surface_segment_audit",
                "message": (
                    f"{segment_audit['tiles']['total']} segments: "
                    f"{segment_audit['pass_count']} pass, {segment_audit['fail_count']} fail, "
                    f"{segment_audit['unknown_count']} unknown; "
                    f"maximum {segment_audit['maximum_material_count']} materials"
                ),
            }
        )

    step = time.perf_counter()
    vanilla = _vanilla_checks(surfaces, paths["vanilla_root"])
    timings["vanilla_paths"] = time.perf_counter() - step
    checks.append(
        {
            "status": "FAIL" if vanilla["missing_paths"] else "PASS",
            "code": "vanilla_paths",
            "message": f"{vanilla['existing_refs']}/{vanilla['texture_refs'] + vanilla['material_refs']} references exist",
        }
    )

    step = time.perf_counter()
    hashes = {name: sha256_file(paths[name]) for name in ("layers", "height", "satellite", "mask")}
    timings["hashes"] = time.perf_counter() - step
    timings["total"] = time.perf_counter() - started
    status = "FAIL" if any(check["status"] == "FAIL" for check in checks) else "WARNING" if any(
        check["status"] == "WARNING" for check in checks
    ) else "PASS"
    return {
        "tool": {"name": "TerrainSatGen", "version": __version__},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "preset": str(preset_path.resolve()),
        "status": status,
        "world": {"size_m": {"width": world_width, "height": world_height}},
        "satellite": satellite,
        "mask": mask,
        "meters_per_pixel": meters_per_pixel,
        "heightmap": _asc_payload(heightmap, paths["height"]),
        "surfaces": [
            {
                "name": surface.name,
                "texture": surface.texture,
                "material": surface.material,
                "legend_rgb": list(surface.rgb),
            }
            for surface in surfaces
        ],
        "mask_color_usage": mask_usage,
        "mask_scan": mask_scan,
        "terrain_builder_compatibility": {
            "mode": "TB_COMPAT" if tb_compat else "STRICT_RGB",
            "configured_aliases": [
                {"rgb": list(rgb), "surface": surface}
                for rgb, surface in sorted(configured_aliases.items())
            ],
            "active_alias_count": len(active_aliases),
        },
        "surface_segment_audit": segment_audit,
        "vanilla_paths": vanilla,
        "input_sha256": hashes,
        "validation_results": checks,
        "manual_review_flags": ["MANUAL_TB_REVIEW", "RUNTIME_VISUAL_REVIEW"],
        "timings_seconds": timings,
        "process": {"pid": os.getpid()},
    }
