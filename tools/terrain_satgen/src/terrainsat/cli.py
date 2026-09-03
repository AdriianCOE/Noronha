"""Command-line interface for TerrainSatGen."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from .inspect import InspectionError, inspect_preset, load_preset
from .parsers import InputFormatError
from .safety import UnsafeOutputError, safe_output_path, write_json_atomic


TOOL_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = TOOL_ROOT / "out"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="terrainsat", description="Inspect DayZ terrain satellite inputs read-only.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    inspect_command = subcommands.add_parser("inspect", help="Inspect and validate terrain inputs")
    inspect_command.add_argument("--preset", type=Path, required=True, help="TOML preset path")
    inspect_command.add_argument(
        "--json-out",
        type=Path,
        help="Optional report path relative to tools/terrain_satgen/out",
    )
    return parser


def _print_report(report: dict[str, object]) -> None:
    print(f"TerrainSatGen inspect: {report['status']}")
    print(f"Preset: {report['preset']}")
    world = report["world"]["size_m"]  # type: ignore[index]
    print(f"World: {world['width']:g} x {world['height']:g} m")
    satellite = report["satellite"]  # type: ignore[assignment]
    mask = report["mask"]  # type: ignore[assignment]
    print(
        f"Satellite: {satellite['width']} x {satellite['height']} "
        f"{satellite['format']} {satellite['mode']}"
    )
    print(f"Mask: {mask['width']} x {mask['height']} {mask['format']} {mask['mode']}")
    scale = report["meters_per_pixel"]  # type: ignore[assignment]
    print(f"Meters per pixel: x={scale['x']:.6g}, y={scale['y']:.6g}")
    height = report["heightmap"]  # type: ignore[assignment]
    print(
        f"Heightmap: {height['ncols']} x {height['nrows']}, cell={height['cellsize']:g} m, "
        f"min={height['minimum']:g}, max={height['maximum']:g}, mean={height['mean']:.6g}, "
        f"NODATA={height['nodata_count']}"
    )
    print(f"Surfaces: {len(report['surfaces'])}")  # type: ignore[arg-type]
    scan = report["mask_scan"]  # type: ignore[assignment]
    print(
        f"Mask colors: {scan['unique_color_count']} used, {scan['unknown_color_count']} unknown, "
        f"{scan['unknown_pixel_count']} unknown pixels"
    )
    print(
        f"Mask scan tile: {scan['tile_rows']} rows, "
        f"~{scan['primary_tile_buffers_mib']:.2f} MiB primary RGB/packed buffers"
    )
    for entry in report["mask_color_usage"]:  # type: ignore[union-attr]
        rgb = ",".join(str(value) for value in entry["rgb"])
        suffix = f" -> {entry['surface']}" if entry["status"] == "exact" else (
            f"; nearest {entry['nearest']['surface']} "
            f"({','.join(str(value) for value in entry['nearest']['rgb'])}), "
            f"distance={entry['nearest']['distance']:.3g}, diagnostic only"
        )
        print(
            f"  ({rgb}) {entry['pixel_count']} px ({entry['percentage']:.6f}%) "
            f"{entry['status']}{suffix}"
        )
    vanilla = report["vanilla_paths"]  # type: ignore[assignment]
    print(
        f"Vanilla references: {vanilla['existing_refs']}/"
        f"{vanilla['texture_refs'] + vanilla['material_refs']} exist"
    )
    print("Validation:")
    for check in report["validation_results"]:  # type: ignore[union-attr]
        print(f"  [{check['status']}] {check['code']}: {check['message']}")
    timings = report["timings_seconds"]  # type: ignore[assignment]
    slowest = max((name for name in timings if name != "total"), key=timings.__getitem__)
    print(f"Timing: total={timings['total']:.3f}s, slowest={slowest} ({timings[slowest]:.3f}s)")
    print("Manual gates: MANUAL_TB_REVIEW, RUNTIME_VISUAL_REVIEW")
    if report["status"] == "FAIL":
        print("Inspect completed with validation failures; see [FAIL] entries above.", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output_path: Path | None = None
        if args.json_out is not None:
            preset = load_preset(args.preset)
            inputs = [Path(preset["inputs"][name]) for name in ("layers", "height", "satellite", "mask")]
            output_path = safe_output_path(args.json_out, OUTPUT_ROOT, inputs)
        report = inspect_preset(args.preset)
        _print_report(report)
        if output_path is not None:
            write_json_atomic(output_path, report)
            print(f"JSON report: {output_path}")
        return 1 if report["status"] == "FAIL" else 0
    except (OSError, InspectionError, InputFormatError, UnsafeOutputError, tomllib.TOMLDecodeError) as error:
        print(f"terrainsat: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
