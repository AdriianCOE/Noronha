from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from terrainsat.cli import main
from terrainsat.inspect import inspect_preset, sha256_file
from terrainsat.parsers import InputFormatError, parse_asc, parse_layers
from terrainsat.safety import UnsafeOutputError, safe_output_path


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def layers_text(
    *,
    duplicate_surface: bool = False,
    duplicate_rgb: bool = False,
    unknown_legend_surface: bool = False,
) -> str:
    second_name = "grass" if duplicate_surface else "dirt"
    legend_second_name = "stone" if unknown_legend_surface else "dirt"
    second_rgb = "10,20,30" if duplicate_rgb else "40,50,60"
    return f'''class Layers
{{
    class grass
    {{
        texture = "DZ\\surfaces\\data\\terrain\\cp_grass_ca.paa";
        material = "DZ\\surfaces\\data\\terrain\\cp_grass.rvmat";
    }};
    class {second_name}
    {{
        texture = "DZ\\surfaces\\data\\terrain\\cp_dirt_ca.paa";
        material = "DZ\\surfaces\\data\\terrain\\cp_dirt.rvmat";
    }};
}};
class Legend
{{
    class Colors
    {{
        grass[] = {{{{10,20,30}}}};
        {legend_second_name}[] = {{{{{second_rgb}}}}};
    }};
}};
'''


class LayersParserTests(unittest.TestCase):
    def test_valid_fixture_and_comments(self) -> None:
        surfaces = parse_layers(FIXTURES / "layers.cfg")
        self.assertEqual([surface.name for surface in surfaces], ["grass", "dirt"])
        self.assertEqual(surfaces[0].rgb, (10, 20, 30))
        self.assertTrue(surfaces[0].texture.endswith("cp_grass_ca.paa"))

    def _assert_invalid(self, text: str, expected: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "layers.cfg"
            path.write_text(text, encoding="utf-8", newline="\r\n")
            with self.assertRaisesRegex(InputFormatError, expected):
                parse_layers(path)

    def test_duplicate_surface_is_rejected(self) -> None:
        self._assert_invalid(layers_text(duplicate_surface=True), "Duplicate surface")

    def test_duplicate_rgb_is_rejected(self) -> None:
        self._assert_invalid(layers_text(duplicate_rgb=True), "Duplicate Legend RGB")

    def test_legend_surface_must_exist_in_layers(self) -> None:
        self._assert_invalid(layers_text(unknown_legend_surface=True), "undefined surfaces")


class AscParserTests(unittest.TestCase):
    def test_valid_fixture_and_nodata(self) -> None:
        stats = parse_asc(FIXTURES / "heightmap.asc")
        self.assertEqual((stats.ncols, stats.nrows), (2, 2))
        self.assertEqual(stats.nodata_count, 1)
        self.assertEqual(stats.minimum, 1)
        self.assertEqual(stats.maximum, 5)
        self.assertEqual(stats.mean, 3)
        self.assertEqual(stats.extent["x"], [200000, 200020])

    def _parse_text(self, text: str):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "height.asc"
        path.write_text(text, encoding="ascii")
        return parse_asc(path)

    def test_nodata_header_is_optional(self) -> None:
        stats = self._parse_text(
            "ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 2\n7\n"
        )
        self.assertIsNone(stats.nodata_value)
        self.assertEqual(stats.mean, 7)

    def test_invalid_header_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputFormatError, "Unknown ASC header"):
            self._parse_text(
                "ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\nbanana 2\n7\n"
            )

    def test_short_row_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputFormatError, "has 1 values; expected 2"):
            self._parse_text(
                "ncols 2\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\n5\n"
            )

    def test_incorrect_row_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(InputFormatError, "has 1 rows; expected 2"):
            self._parse_text(
                "ncols 1\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\n5\n"
            )


class InspectionFixture:
    def __init__(self, root: Path, *, unknown: bool = False, mismatch: bool = False) -> None:
        self.root = root
        self.layers = root / "layers.cfg"
        self.height = root / "height.asc"
        self.satellite = root / "satellite.bmp"
        self.mask = root / "mask.bmp"
        self.vanilla = root / "vanilla"
        self.preset = root / "preset.toml"
        self.layers.write_text(layers_text(), encoding="utf-8")
        self.height.write_text(
            "ncols 2\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 10\n1 2\n",
            encoding="ascii",
        )
        for reference in (
            "DZ/surfaces/data/terrain/cp_grass_ca.paa",
            "DZ/surfaces/data/terrain/cp_grass.rvmat",
            "DZ/surfaces/data/terrain/cp_dirt_ca.paa",
            "DZ/surfaces/data/terrain/cp_dirt.rvmat",
        ):
            path = self.vanilla / reference
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        Image.new("RGB", (2, 1), (1, 2, 3)).save(self.satellite)
        mask_size = (1, 1) if mismatch else (2, 1)
        mask = Image.new("RGB", mask_size, (10, 20, 30))
        if unknown and not mismatch:
            mask.putpixel((1, 0), (11, 20, 30))
        mask.save(self.mask)
        self.preset.write_text(
            f'''[world]
size_m = [20, 10]
[inputs]
layers = "{self.layers.as_posix()}"
height = "{self.height.as_posix()}"
satellite = "{self.satellite.as_posix()}"
mask = "{self.mask.as_posix()}"
vanilla_root = "{self.vanilla.as_posix()}"
[mask]
unknown_color_policy = "error"
tile_rows = 1
''',
            encoding="utf-8",
        )


class InspectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_exact_mask_and_rectangular_world_pass(self) -> None:
        fixture = InspectionFixture(self.root)
        report = inspect_preset(fixture.preset)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["meters_per_pixel"], {"x": 10.0, "y": 10.0})
        self.assertEqual(report["mask_color_usage"][0]["status"], "exact")
        self.assertEqual(report["vanilla_paths"]["existing_refs"], 4)

    def test_mismatched_raster_dimensions_fail(self) -> None:
        fixture = InspectionFixture(self.root, mismatch=True)
        report = inspect_preset(fixture.preset)
        checks = {item["code"]: item["status"] for item in report["validation_results"]}
        self.assertEqual(checks["raster_dimensions"], "FAIL")

    def test_unknown_is_diagnostic_and_policy_error_fails(self) -> None:
        fixture = InspectionFixture(self.root, unknown=True)
        report = inspect_preset(fixture.preset)
        unknown = next(item for item in report["mask_color_usage"] if item["status"] == "unknown")
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(unknown["rgb"], [11, 20, 30])
        self.assertEqual(unknown["nearest"]["surface"], "grass")
        self.assertEqual(unknown["nearest"]["distance"], 1.0)
        self.assertTrue(unknown["nearest"]["diagnostic_only"])

    def test_inputs_keep_identical_hashes(self) -> None:
        fixture = InspectionFixture(self.root, unknown=True)
        inputs = (fixture.layers, fixture.height, fixture.satellite, fixture.mask)
        before = [sha256_file(path) for path in inputs]
        inspect_preset(fixture.preset)
        self.assertEqual(before, [sha256_file(path) for path in inputs])

    def test_cli_without_json_creates_nothing(self) -> None:
        fixture = InspectionFixture(self.root)
        output_root = self.root / "out"
        with patch("terrainsat.cli.OUTPUT_ROOT", output_root), contextlib.redirect_stdout(io.StringIO()):
            exit_code = main(["inspect", "--preset", str(fixture.preset)])
        self.assertEqual(exit_code, 0)
        self.assertFalse(output_root.exists())

    def test_cli_writes_requested_json_inside_out(self) -> None:
        fixture = InspectionFixture(self.root)
        output_root = self.root / "out"
        with patch("terrainsat.cli.OUTPUT_ROOT", output_root), contextlib.redirect_stdout(io.StringIO()):
            exit_code = main(
                ["inspect", "--preset", str(fixture.preset), "--json-out", "inspect/report.json"]
            )
        self.assertEqual(exit_code, 0)
        report_path = output_root / "inspect" / "report.json"
        self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["status"], "PASS")

    def test_cli_returns_one_after_complete_unknown_report(self) -> None:
        fixture = InspectionFixture(self.root, unknown=True)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            exit_code = main(["inspect", "--preset", str(fixture.preset)])
        self.assertEqual(exit_code, 1)
        self.assertIn("diagnostic only", stdout.getvalue())
        self.assertIn("[FAIL] mask_colors", stdout.getvalue())


class OutputSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.out = self.root / "out"

    def test_valid_relative_output(self) -> None:
        self.assertEqual(
            safe_output_path(Path("inspect/report.json"), self.out),
            (self.out / "inspect/report.json").resolve(),
        )

    def test_parent_escape_is_rejected(self) -> None:
        with self.assertRaisesRegex(UnsafeOutputError, "escapes"):
            safe_output_path(Path("../report.json"), self.out)

    def test_absolute_external_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(UnsafeOutputError, "must be relative"):
            safe_output_path((self.root / "external.json").resolve(), self.out)

    def test_output_equal_to_input_is_rejected(self) -> None:
        input_path = self.out / "input.json"
        input_path.parent.mkdir(parents=True)
        input_path.touch()
        with self.assertRaisesRegex(UnsafeOutputError, "input file"):
            safe_output_path(Path("input.json"), self.out, [input_path])

    def test_symlink_escape_is_rejected_when_supported(self) -> None:
        external = self.root / "external"
        external.mkdir()
        self.out.mkdir()
        link = self.out / "link"
        try:
            link.symlink_to(external, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        with self.assertRaisesRegex(UnsafeOutputError, "escapes"):
            safe_output_path(Path("link/report.json"), self.out)

    def test_output_root_symlink_is_rejected_when_supported(self) -> None:
        external = self.root / "external-root"
        external.mkdir()
        try:
            self.out.symlink_to(external, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        with self.assertRaisesRegex(UnsafeOutputError, "must not be a symlink"):
            safe_output_path(Path("inspect/report.json"), self.out)


if __name__ == "__main__":
    unittest.main()
