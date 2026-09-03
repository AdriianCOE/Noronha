"""Read-only orchestration for the TerrainSatGen inspect command."""

from __future__ import annotations

import hashlib
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

from . import __version__
from .parsers import AscStats, Surface, parse_asc, parse_layers


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
    allowed_sections = {"world", "inputs", "mask"}
    unknown_sections = sorted(set(preset) - allowed_sections)
    if unknown_sections:
        raise InspectionError("Unknown preset sections: " + ", ".join(unknown_sections))
    for required in allowed_sections:
        if required not in preset or not isinstance(preset[required], dict):
            raise InspectionError(f"Preset requires table [{required}]")
    _reject_unknown(preset["world"], {"size_m"}, "world")
    _reject_unknown(
        preset["inputs"],
        {"layers", "height", "satellite", "mask", "vanilla_root"},
        "inputs",
    )
    _reject_unknown(preset["mask"], {"unknown_color_policy", "tile_rows", "color_aliases"}, "mask")
    required_inputs = {"layers", "height", "satellite", "mask", "vanilla_root"}
    missing_inputs = sorted(required_inputs - preset["inputs"].keys())
    if missing_inputs:
        raise InspectionError("Missing preset inputs: " + ", ".join(missing_inputs))
    if "color_aliases" in preset["mask"] and preset["mask"]["color_aliases"]:
        raise InspectionError("Active mask color aliases are not allowed in the inspect-only MVP")
    if preset["mask"].get("unknown_color_policy") not in {"error", "warning"}:
        raise InspectionError("mask.unknown_color_policy must be 'error' or 'warning'")
    tile_rows = preset["mask"].get("tile_rows", 256)
    if not isinstance(tile_rows, int) or tile_rows <= 0:
        raise InspectionError("mask.tile_rows must be a positive integer")
    _world_size(preset["world"].get("size_m"))
    return preset


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
            "status": "exact" if rgb in known else "unknown",
        }
        if rgb in known:
            entry["surface"] = known[rgb]
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


def inspect_preset(preset_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    timings: dict[str, float] = {}

    step = time.perf_counter()
    preset = load_preset(preset_path)
    paths = _input_paths(preset)
    timings["preset"] = time.perf_counter() - step

    step = time.perf_counter()
    surfaces = parse_layers(paths["layers"])
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
    mask_usage, mask_scan = _scan_mask(paths["mask"], surfaces, preset["mask"]["tile_rows"])
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
        "vanilla_paths": vanilla,
        "input_sha256": hashes,
        "validation_results": checks,
        "manual_review_flags": ["MANUAL_TB_REVIEW", "RUNTIME_VISUAL_REVIEW"],
        "timings_seconds": timings,
        "process": {"pid": os.getpid()},
    }
