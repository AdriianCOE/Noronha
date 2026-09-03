"""Command-line interface for TerrainSatGen."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from .inspect import InspectionError, inspect_preset, load_preset, write_segment_diagnostics
from .parsers import InputFormatError
from .preview import PreviewError, PreviewRequest, display_layer, load_synthetic_preset, render_preview, write_bmp_atomic
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
    inspect_command.add_argument(
        "--tb-compat",
        action="store_true",
        help="Resolve only explicitly configured Terrain Builder mask aliases",
    )
    inspect_command.add_argument(
        "--surface-segment-audit",
        action="store_true",
        help="Audit Terrain Builder surface windows using the recorded sampler model",
    )
    inspect_command.add_argument(
        "--segment-diagnostics",
        action="store_true",
        help="Write read-only crops for failed TB-compatible surface segments",
    )
    preview_command = subcommands.add_parser("preview", help="Render a synthetic procedural preview")
    preview_command.add_argument("--preset", type=Path, required=True, help="Synthetic TOML preset path")
    preview_command.add_argument("--x", type=float, required=True, help="Absolute world X origin in metres")
    preview_command.add_argument("--y", type=float, required=True, help="Absolute world Y origin in metres")
    preview_command.add_argument("--width-m", type=float, required=True, help="Preview width in metres")
    preview_command.add_argument("--height-m", type=float, required=True, help="Preview height in metres")
    preview_command.add_argument("--meters-per-pixel", type=float, required=True, help="Metres per output pixel")
    preview_command.add_argument("--tile-size", type=int, default=256, help="Tile edge in pixels (default: 256)")
    preview_command.add_argument("--output", type=Path, required=True, help="BMP path relative to tools/terrain_satgen/out")
    preview_command.add_argument(
        "--debug-layers",
        action="store_true",
        help="Also write base, macro, medium, local and surface-map BMPs beside the output",
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
    compatibility = report["terrain_builder_compatibility"]  # type: ignore[assignment]
    print(
        f"Terrain Builder compatibility: {compatibility['mode']}; "
        f"{compatibility['active_alias_count']}/{len(compatibility['configured_aliases'])} aliases active"
    )
    for entry in report["mask_color_usage"]:  # type: ignore[union-attr]
        rgb = ",".join(str(value) for value in entry["rgb"])
        if entry["status"] in {"exact", "explicit_alias"}:
            suffix = f" -> {entry['surface']}"
        else:
            suffix = (
                f"; nearest {entry['nearest']['surface']} "
                f"({','.join(str(value) for value in entry['nearest']['rgb'])}), "
                f"distance={entry['nearest']['distance']:.3g}, diagnostic only"
            )
        print(
            f"  ({rgb}) {entry['pixel_count']} px ({entry['percentage']:.6f}%) "
            f"{entry['status']}{suffix}"
        )
    audit = report["surface_segment_audit"]
    if audit is not None:
        print(
            "Surface segment audit: "
            f"{audit['tiles']['x']} x {audit['tiles']['y']} = {audit['tiles']['total']}; "
            f"core={audit['core_stride_px']} px, border={audit['border_per_side_px']} px, "
            f"shared overlap={audit['actual_shared_overlap_px']} px, limit={audit['material_limit']}"
        )
        print(
            f"  pass={audit['pass_count']}, fail={audit['fail_count']}, "
            f"unknown={audit['unknown_count']}, maximum={audit['maximum_material_count']}"
        )
        for segment in audit["worst_segments"][:8]:
            print(
                f"  worst tile ({segment['tile_x']},{segment['tile_y']}) "
                f"{segment['bounds']} {segment['material_count']} {segment['status']}"
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


def _preview_paths(output: Path, debug_layers: bool) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    if debug_layers:
        paths.update({
            name: output.with_name(f"{output.stem}.{name}{output.suffix}")
            for name in ("base", "macro", "medium", "local", "surface_map")
        })
    # The primary requested output is promoted last: a debug write failure never leaves it behind.
    paths["combined"] = output
    return paths


def _run_preview(args: argparse.Namespace) -> int:
    preset = load_synthetic_preset(args.preset)
    paths = _preview_paths(args.output, args.debug_layers)
    safe_paths = {name: safe_output_path(path, OUTPUT_ROOT, [args.preset]) for name, path in paths.items()}
    result = render_preview(
        preset,
        PreviewRequest(args.x, args.y, args.width_m, args.height_m, args.meters_per_pixel, args.tile_size),
    )
    for name, path in safe_paths.items():
        write_bmp_atomic(path, display_layer(result, name, preset.materials))
        print(f"{name}: {path}")
    print(
        f"TerrainSatGen synthetic preview: {result.combined.shape[1]} x {result.combined.shape[0]} px; "
        f"clipped pixels={result.clipped_pixel_count}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preview":
            return _run_preview(args)
        if args.segment_diagnostics and not args.tb_compat:
            raise InspectionError("--segment-diagnostics requires --tb-compat")
        output_path: Path | None = None
        inputs: list[Path] = []
        if args.json_out is not None:
            preset = load_preset(args.preset)
            inputs = [Path(preset["inputs"][name]) for name in ("layers", "height", "satellite", "mask")]
            output_path = safe_output_path(args.json_out, OUTPUT_ROOT, inputs)
        report = inspect_preset(
            args.preset,
            tb_compat=args.tb_compat,
            surface_segment_audit=args.surface_segment_audit or args.segment_diagnostics,
        )
        _print_report(report)
        if output_path is not None:
            write_json_atomic(output_path, report)
            print(f"JSON report: {output_path}")
        if args.segment_diagnostics:
            if not inputs:
                preset = load_preset(args.preset)
                inputs = [Path(preset["inputs"][name]) for name in ("layers", "height", "satellite", "mask")]
            diagnostic_root = safe_output_path(Path("tb-segment-audit/report.json"), OUTPUT_ROOT, inputs).parent
            diagnostics = write_segment_diagnostics(args.preset, report, diagnostic_root)
            print(f"Segment diagnostics: {len(diagnostics['failed_tiles'])} tiles in {diagnostic_root}")
        return 1 if report["status"] == "FAIL" else 0
    except (OSError, InspectionError, InputFormatError, PreviewError, UnsafeOutputError, tomllib.TOMLDecodeError) as error:
        print(f"terrainsat: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
