from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from terrainsat.inspect import (
    InspectionError,
    audit_surface_segments,
    inspect_preset,
    segment_window_model,
    sha256_file,
    write_segment_diagnostics,
)
from terrainsat.parsers import Surface


def sampler(*, tile: int, stride: int, border: int, tiles_x: int, tiles_y: int, limit: int = 4) -> dict[str, int]:
    return {
        "tile_texture_px": tile,
        "core_stride_px": stride,
        "border_px": border,
        "actual_shared_overlap_px": 2 * border,
        "tiles_x": tiles_x,
        "tiles_y": tiles_y,
        "material_limit": limit,
    }


def write_fixture(
    root: Path,
    pixels: np.ndarray,
    *,
    aliases: str = "",
    terrain_builder: str = "",
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    height, width = pixels.shape[:2]
    layers = root / "layers.cfg"
    layers.write_text(
        """class Layers
{
    class grass { texture = "DZ\\\\grass.paa"; material = "DZ\\\\grass.rvmat"; };
    class dirt { texture = "DZ\\\\dirt.paa"; material = "DZ\\\\dirt.rvmat"; };
};
class Legend
{
    class Colors
    {
        grass[] = {{10,20,30}};
        dirt[] = {{40,50,60}};
    };
};
""",
        encoding="utf-8",
    )
    asc = root / "height.asc"
    asc.write_text(
        f"ncols {width}\nnrows {height}\nxllcorner 0\nyllcorner 0\ncellsize 1\n"
        + "\n".join(" ".join("0" for _ in range(width)) for _ in range(height))
        + "\n",
        encoding="ascii",
    )
    satellite = root / "satellite.bmp"
    Image.new("RGB", (width, height), (10, 20, 30)).save(satellite)
    mask = root / "mask.bmp"
    Image.fromarray(pixels, "RGB").save(mask)
    vanilla = root / "vanilla"
    for name in ("grass.paa", "grass.rvmat", "dirt.paa", "dirt.rvmat"):
        path = vanilla / "DZ" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    preset = root / "preset.toml"
    preset.write_text(
        f"""[world]
size_m = [{width}, {height}]
[inputs]
layers = "{layers.as_posix()}"
height = "{asc.as_posix()}"
satellite = "{satellite.as_posix()}"
mask = "{mask.as_posix()}"
vanilla_root = "{vanilla.as_posix()}"
[mask]
unknown_color_policy = "error"
tile_rows = 2
{aliases}
{terrain_builder}
""",
        encoding="utf-8",
    )
    return preset


class TerrainBuilderCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.unknown = np.array([[[10, 20, 30], [11, 20, 30]]], dtype=np.uint8)

    def test_strict_keeps_unknown_and_tb_compat_resolves_only_declared_alias(self) -> None:
        preset = write_fixture(
            self.root,
            self.unknown,
            aliases='[mask.color_aliases]\n"11,20,30" = "grass"\n',
        )
        strict = inspect_preset(preset)
        compat = inspect_preset(preset, tb_compat=True)
        self.assertEqual(strict["status"], "FAIL")
        self.assertEqual(strict["mask_color_usage"][1]["status"], "unknown")
        self.assertEqual(compat["status"], "PASS")
        self.assertEqual(compat["mask_color_usage"][1]["status"], "explicit_alias")
        self.assertEqual(compat["mask_color_usage"][1]["surface"], "grass")

    def test_tb_compat_never_uses_nearest_implicitly(self) -> None:
        report = inspect_preset(write_fixture(self.root, self.unknown), tb_compat=True)
        unknown = report["mask_color_usage"][1]
        self.assertEqual(unknown["status"], "unknown")
        self.assertEqual(unknown["nearest"]["surface"], "grass")

    def test_alias_target_must_exist_and_exact_legend_rgb_cannot_be_shadowed(self) -> None:
        nonexistent = write_fixture(
            self.root / "nonexistent",
            self.unknown,
            aliases='[mask.color_aliases]\n"11,20,30" = "missing"\n',
        )
        with self.assertRaisesRegex(InspectionError, "unknown surface"):
            inspect_preset(nonexistent, tb_compat=True)
        conflicting = write_fixture(
            self.root / "conflicting",
            self.unknown,
            aliases='[mask.color_aliases]\n"10,20,30" = "dirt"\n',
        )
        with self.assertRaisesRegex(InspectionError, "conflicts with exact"):
            inspect_preset(conflicting, tb_compat=True)
        duplicate = write_fixture(
            self.root / "duplicate",
            self.unknown,
            aliases='[mask.color_aliases]\n"11,20,30" = "grass"\n"11,20,30" = "dirt"\n',
        )
        with self.assertRaisesRegex(ValueError, "Cannot overwrite a value"):
            inspect_preset(duplicate, tb_compat=True)

    def test_real_sampler_geometry_is_22_by_22_with_clipped_edges(self) -> None:
        windows = segment_window_model(10240, 10240, sampler(tile=512, stride=480, border=16, tiles_x=22, tiles_y=22))
        self.assertEqual(len(windows), 484)
        self.assertEqual(windows[0]["core_bounds"], {"left": 0, "top": 0, "right": 480, "bottom": 480})
        self.assertEqual(windows[0]["bounds"], {"left": 0, "top": 0, "right": 496, "bottom": 496})
        self.assertEqual(windows[1]["bounds"], {"left": 464, "top": 0, "right": 976, "bottom": 496})
        self.assertEqual(windows[-1]["core_bounds"], {"left": 10080, "top": 10080, "right": 10240, "bottom": 10240})
        self.assertEqual(windows[-1]["bounds"], {"left": 10064, "top": 10064, "right": 10240, "bottom": 10240})

    def test_audit_statuses_count_surfaces_not_rgb_and_does_not_modify_mask(self) -> None:
        mask = self.root / "mask.bmp"
        pixels = np.array([[[10, 20, 30], [11, 20, 30]]], dtype=np.uint8)
        Image.fromarray(pixels, "RGB").save(mask)
        surfaces = [Surface("grass", "", "", (10, 20, 30))]
        before = sha256_file(mask)
        strict = audit_surface_segments(mask, surfaces, {}, sampler(tile=2, stride=2, border=0, tiles_x=1, tiles_y=1))
        compat = audit_surface_segments(mask, surfaces, {(11, 20, 30): "grass"}, sampler(tile=2, stride=2, border=0, tiles_x=1, tiles_y=1))
        self.assertEqual(strict["unknown_count"], 1)
        self.assertEqual(strict["segments"][0]["status"], "UNKNOWN")
        self.assertEqual(compat["pass_count"], 1)
        self.assertEqual(compat["segments"][0]["material_count"], 1)
        self.assertEqual(compat["segments"][0]["histogram_with_overlap"][0]["surface"], "grass")
        self.assertEqual(compat["segments"][0]["histogram_with_overlap"][0]["pixel_count"], 2)
        self.assertEqual(
            {source["status"] for source in compat["segments"][0]["histogram_with_overlap"][0]["sources"]},
            {"exact", "explicit_alias"},
        )
        self.assertEqual(sha256_file(mask), before)

    def test_audit_fails_more_than_four_and_overlap_can_raise_the_count(self) -> None:
        colors = [(1, 1, 1), (2, 2, 2), (3, 3, 3), (4, 4, 4), (5, 5, 5)]
        surfaces = [Surface(f"s{index}", "", "", color) for index, color in enumerate(colors)]
        mask = self.root / "five.bmp"
        pixels = np.array([[colors[0]] * 16 + colors[1:]], dtype=np.uint8)
        Image.fromarray(pixels, "RGB").save(mask)
        failed = audit_surface_segments(mask, surfaces, {}, sampler(tile=20, stride=20, border=0, tiles_x=1, tiles_y=1))
        self.assertEqual(failed["fail_count"], 1)
        self.assertEqual(failed["maximum_material_count"], 5)
        self.assertEqual(failed["segments"][0]["histogram_with_overlap"][-1]["pixel_count"], 1)

        overlap_mask = self.root / "overlap.bmp"
        pixels = np.full((12, 12, 3), (10, 20, 30), dtype=np.uint8)
        pixels[:, 5] = (40, 50, 60)
        Image.fromarray(pixels, "RGB").save(overlap_mask)
        two_surfaces = [Surface("grass", "", "", (10, 20, 30)), Surface("dirt", "", "", (40, 50, 60))]
        report = audit_surface_segments(overlap_mask, two_surfaces, {}, sampler(tile=8, stride=6, border=1, tiles_x=2, tiles_y=1))
        second = next(segment for segment in report["segments"] if segment["tile_x"] == 1)
        self.assertEqual(second["surfaces_core"], ["grass"])
        self.assertEqual(second["surfaces_with_overlap"], ["dirt", "grass"])
        self.assertEqual(second["surfaces_overlap_only"], ["dirt"])

    def test_json_report_has_complete_segment_records(self) -> None:
        pixels = np.full((12, 12, 3), (10, 20, 30), dtype=np.uint8)
        preset = write_fixture(
            self.root,
            pixels,
            terrain_builder="""[terrain_builder]
tile_texture_px = 8
core_stride_px = 6
border_px = 1
actual_shared_overlap_px = 2
tiles_per_row = 2
material_limit = 4
""",
        )
        audit = inspect_preset(preset, surface_segment_audit=True)["surface_segment_audit"]
        self.assertEqual(audit["tiles"]["total"], 4)
        self.assertEqual(
            set(audit["segments"][0]),
            {
                "tile_x", "tile_y", "core_bounds", "bounds", "surfaces_core", "surfaces_with_overlap",
                "surfaces_overlap_only", "histogram_core", "histogram_with_overlap", "material_count",
                "unknown_rgb", "status",
            },
        )

    def test_diagnostics_write_bounds_matched_read_only_outputs(self) -> None:
        pixels = np.array([[[10, 20, 30], [40, 50, 60]]], dtype=np.uint8)
        preset = write_fixture(self.root, pixels)
        mask = self.root / "mask.bmp"
        satellite = self.root / "satellite.bmp"
        before = (sha256_file(mask), sha256_file(satellite))
        segment = {
            "tile_x": 0,
            "tile_y": 0,
            "core_bounds": {"left": 0, "top": 0, "right": 2, "bottom": 1},
            "bounds": {"left": 0, "top": 0, "right": 2, "bottom": 1},
            "surfaces_core": ["dirt", "grass"],
            "surfaces_with_overlap": ["dirt", "grass"],
            "surfaces_overlap_only": [],
            "histogram_core": [
                {"surface": "dirt", "pixel_count": 1, "percentage": 50, "sources": [{"rgb": [40, 50, 60], "status": "exact", "pixel_count": 1}]},
                {"surface": "grass", "pixel_count": 1, "percentage": 50, "sources": [{"rgb": [10, 20, 30], "status": "exact", "pixel_count": 1}]},
            ],
            "histogram_with_overlap": [
                {"surface": "dirt", "pixel_count": 1, "percentage": 50, "sources": [{"rgb": [40, 50, 60], "status": "exact", "pixel_count": 1}]},
                {"surface": "grass", "pixel_count": 1, "percentage": 50, "sources": [{"rgb": [10, 20, 30], "status": "exact", "pixel_count": 1}]},
            ],
            "material_count": 2,
            "unknown_rgb": [],
            "status": "FAIL",
        }
        report = {
            "terrain_builder_compatibility": {"mode": "TB_COMPAT"},
            "surface_segment_audit": {"segments": [segment]},
        }
        root = self.root / "out"
        summary = write_segment_diagnostics(preset, report, root)
        tile_root = root / "tile_0_0"
        self.assertEqual(summary["failed_tiles"][0]["bounds"], segment["bounds"])
        for name in ("mask_raw.bmp", "mask_resolved.png", "satellite_crop.bmp", "overlay_bounds.png", "report.json"):
            self.assertTrue((tile_root / name).is_file())
        self.assertEqual(before, (sha256_file(mask), sha256_file(satellite)))


if __name__ == "__main__":
    unittest.main()
