"""Read-only consistency audit for Noronha terrain material declarations."""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


LAYER_RE = re.compile(
    r'class\s+(?P<name>\w+)\s*\{\s*texture\s*=\s*"[^"]+";\s*'
    r'material\s*=\s*"(?P<material>[^"]+)";',
    re.DOTALL,
)
COLOR_RE = re.compile(r'(?P<name>\w+)\[\]\s*=\s*\{\{(?P<rgb>[^}]+)\}\};')
MATERIAL_RE = re.compile(r'material\d+\s*=\s*"(?P<material>[^"]+)";')


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_layers(path: Path) -> dict[str, str]:
    return {match["name"]: match["material"] for match in LAYER_RE.finditer(read_text(path))}


def parse_colors(path: Path) -> dict[str, tuple[int, int, int]]:
    colors: dict[str, tuple[int, int, int]] = {}
    for match in COLOR_RE.finditer(read_text(path)):
        colors[match["name"]] = tuple(int(value.strip()) for value in match["rgb"].split(","))
    return colors


def parse_world_materials(path: Path) -> list[str]:
    return MATERIAL_RE.findall(read_text(path))


def duplicate_values(values: dict[str, Any]) -> dict[str, list[str]]:
    groups: dict[Any, list[str]] = defaultdict(list)
    for name, value in values.items():
        groups[value].append(name)
    return {str(value): names for value, names in groups.items() if len(names) > 1}


def build_report(root: Path, layers_path: Path, world_config: Path, layers_dir: Path) -> dict[str, Any]:
    layers = parse_layers(layers_path)
    colors = parse_colors(layers_path)
    world_materials = parse_world_materials(world_config)
    declared_materials = set(layers.values())
    used_materials = set(world_materials)
    missing_from_layers = sorted(used_materials - declared_materials)
    unused_layers = sorted(name for name, material in layers.items() if material not in used_materials)
    local_missing = []
    for material in used_materials:
        if material.lower().startswith("noronha\\"):
            candidate = root / Path(material.replace("\\", "/"))
            if not candidate.is_file():
                local_missing.append(material)

    groups = {"cp": [], "en": [], "other": []}
    for name in sorted(layers):
        groups["cp" if name.startswith("cp_") else "en" if name.startswith("en_") else "other"].append(name)

    return {
        "layers_cfg": str(layers_path),
        "world_config": str(world_config),
        "defined_layers": layers,
        "legend_colors": {name: list(rgb) for name, rgb in colors.items()},
        "world_used_materials": world_materials,
        "generated_rvmats": sorted(path.name for path in layers_dir.glob("*.rvmat")),
        "materials_used_but_not_declared": missing_from_layers,
        "layers_without_world_use": unused_layers,
        "duplicate_legend_colors": duplicate_values(colors),
        "duplicate_layer_materials": duplicate_values(layers),
        "missing_local_material_paths": local_missing,
        "layer_name_groups": groups,
    }


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root, help="Noronha repository root.")
    parser.add_argument("--layers", type=Path, default=root / "source" / "layers.cfg")
    parser.add_argument("--world-config", type=Path, default=root / "world" / "config.cpp")
    parser.add_argument("--layers-dir", type=Path, default=root / "data" / "layers")
    parser.add_argument("--json", action="store_true", help="Emit the complete report as JSON.")
    parser.add_argument("--strict", action="store_true", help="Fail for duplicate or undeclared material findings.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required = (args.layers, args.world_config, args.layers_dir)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("Missing required input: " + ", ".join(missing), file=sys.stderr)
        return 2

    report = build_report(args.root, args.layers, args.world_config, args.layers_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Layers defined: {len(report['defined_layers'])}")
        print(f"Legend colors: {len(report['legend_colors'])}")
        print(f"World materials: {len(report['world_used_materials'])}")
        print(f"Generated RVMATs: {len(report['generated_rvmats'])}")
        for key in ("materials_used_but_not_declared", "layers_without_world_use", "duplicate_legend_colors", "duplicate_layer_materials", "missing_local_material_paths"):
            print(f"{key}: {report[key]}")

    findings = (
        report["materials_used_but_not_declared"]
        or report["duplicate_legend_colors"]
        or report["duplicate_layer_materials"]
        or report["missing_local_material_paths"]
    )
    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
