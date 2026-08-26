"""Read-only ESRI ASCII terrain statistics and optional diagnostic raster export."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def load_ascii(path: Path) -> tuple[np.ndarray, dict[str, float]]:
    header: dict[str, float] = {}
    with path.open(encoding="utf-8") as handle:
        for _ in range(6):
            key, value = handle.readline().split()
            header[key.lower()] = float(value)
    data = np.loadtxt(path, skiprows=6)
    data[data == header["nodata_value"]] = np.nan
    return data, header


def inspect(data: np.ndarray, cellsize: float, sea_level: float) -> tuple[dict[str, object], np.ndarray]:
    slope = np.degrees(np.arctan(np.hypot(*np.gradient(data, cellsize))))
    valid = np.isfinite(data)
    land = valid & (data > sea_level)
    area_km2 = cellsize * cellsize / 1_000_000
    stats = {
        "elevation": {key: float(value) for key, value in {
            "min": np.nanmin(data), "max": np.nanmax(data), "mean": np.nanmean(data),
            "median": np.nanmedian(data), "p05": np.nanpercentile(data, 5), "p95": np.nanpercentile(data, 95),
        }.items()},
        "cells": int(valid.sum()), "land_cells": int(land.sum()), "underwater_cells": int((valid & ~land).sum()),
        "land_area_km2": float(land.sum() * area_km2), "underwater_area_km2": float((valid & ~land).sum() * area_km2),
        "slope": {"mean": float(np.nanmean(slope)), "over_20": int((slope > 20).sum()), "over_30": int((slope > 30).sum()), "over_45": int((slope > 45).sum())},
    }
    return stats, slope


def grayscale(data: np.ndarray) -> Image.Image:
    minimum, maximum = np.nanmin(data), np.nanmax(data)
    scaled = np.zeros(data.shape, dtype=np.uint8) if maximum == minimum else np.nan_to_num((data - minimum) * 255 / (maximum - minimum)).astype(np.uint8)
    return Image.fromarray(scaled, mode="L")


def hillshade(data: np.ndarray, cellsize: float) -> Image.Image:
    dy, dx = np.gradient(data, cellsize)
    azimuth, altitude = np.radians(315), np.radians(45)
    shaded = np.sin(altitude) / np.sqrt(1 + dx * dx + dy * dy) + np.cos(altitude) * (-dx * np.sin(azimuth) - dy * np.cos(azimuth)) / np.sqrt(1 + dx * dx + dy * dy)
    return Image.fromarray(np.clip((shaded + 1) * 127.5, 0, 255).astype(np.uint8), mode="L")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--heightmap", type=Path, required=True)
    parser.add_argument("--sea-level", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--stats-only", action="store_true")
    parser.add_argument("--hillshade", action="store_true")
    parser.add_argument("--slope", action="store_true")
    args = parser.parse_args()
    data, header = load_ascii(args.heightmap)
    report, slope = inspect(data, header["cellsize"], args.sea_level)
    report.update({"heightmap": str(args.heightmap), "cellsize": header["cellsize"], "sea_level": args.sea_level})
    if (args.hillshade or args.slope) and args.output is None:
        parser.error("--output is required for raster diagnostics")
    if args.output and not args.stats_only:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "terrain_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.hillshade:
            hillshade(data, header["cellsize"]).save(args.output / "hillshade.png")
        if args.slope:
            grayscale(slope).save(args.output / "slope.png")
    print(json.dumps(report, indent=2) if args.json else f"land_area_km2={report['land_area_km2']:.3f} max_elevation={report['elevation']['max']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
