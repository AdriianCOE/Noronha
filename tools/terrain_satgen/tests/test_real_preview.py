from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from terrainsat.cli import OUTPUT_ROOT, main, write_real_bmp_atomic as cli_write_real_bmp_atomic
from terrainsat.inspect import sha256_file
from terrainsat.preview import PreviewRequest
from terrainsat.real_preview import RealPreviewError, load_real_preview_preset, render_real_preview, write_bmp_atomic
from terrainsat.reference_analysis import image_statistics


def write_fixture(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "layers.cfg").write_text(
        """class Layers
{
    class grass { texture = "DZ\\grass.paa"; material = "DZ\\grass.rvmat"; };
    class dirt { texture = "DZ\\dirt.paa"; material = "DZ\\dirt.rvmat"; };
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
    (root / "height.asc").write_text(
        "ncols 32\nnrows 32\nxllcorner 0\nyllcorner 0\ncellsize 1\n" + "\n".join(" ".join("0" for _ in range(32)) for _ in range(32)) + "\n",
        encoding="ascii",
    )
    yy, xx = np.mgrid[:32, :32]
    satellite = np.stack((30 + xx * 3, 50 + yy * 2, 70 + (xx + yy) % 17), axis=-1).astype(np.uint8)
    mask = np.full((32, 32, 3), (10, 20, 30), dtype=np.uint8)
    mask[:, 12:20] = (11, 20, 30)
    mask[:, 20:] = (40, 50, 60)
    Image.fromarray(satellite, "RGB").save(root / "satellite.bmp")
    Image.fromarray(mask, "RGB").save(root / "mask.bmp")
    vanilla = root / "vanilla"
    vanilla.mkdir()
    preset = root / "preset.toml"
    preset.write_text(
        f"""[world]
size_m = 32
[inputs]
layers = "{(root / 'layers.cfg').as_posix()}"
height = "{(root / 'height.asc').as_posix()}"
satellite = "{(root / 'satellite.bmp').as_posix()}"
mask = "{(root / 'mask.bmp').as_posix()}"
vanilla_root = "{vanilla.as_posix()}"
[mask]
unknown_color_policy = "error"
tile_rows = 8
[mask.color_aliases]
"11,20,30" = "grass"
[real_preview]
world_seed = "real-fixture"
structure_blur_radius_px = 2
[real_preview.variants.subtle]
structure_weight = 0.55
detail_weight = 0.35
recipe_weight = 0.10
[real_preview.variants.balanced]
structure_weight = 0.45
detail_weight = 0.15
recipe_weight = 0.40
[real_preview.variants.authored]
structure_weight = 0.32
detail_weight = 0.05
recipe_weight = 0.63
[real_preview.recipes.grass]
base_rgb = [80, 110, 50]
macro_strength = 12
medium_strength = 8
local_strength = 3
blend_strength = 0.75
[real_preview.recipes.dirt]
base_rgb = [125, 85, 60]
macro_strength = 10
medium_strength = 6
local_strength = 2
blend_strength = 0.75
""",
        encoding="utf-8",
    )
    return preset


def request(*, x: int = 0, y: int = 0, width: int = 32, height: int = 32, tile: int = 8) -> PreviewRequest:
    return PreviewRequest(x, y, width, height, 1, tile)


class RealPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = write_fixture(self.root)
        self.preset = load_real_preview_preset(self.path)

    def test_read_only_and_original_crop_are_exact(self) -> None:
        before = tuple(sha256_file(self.preset.inputs[name]) for name in ("satellite", "mask"))
        result = render_real_preview(self.preset, request(x=4, y=5, width=12, height=10), variant="original", tb_compat=True)
        with Image.open(self.preset.inputs["satellite"]) as image:
            expected = np.asarray(image.crop((4, 17, 16, 27)), dtype=np.uint8)
        self.assertTrue(np.array_equal(result.combined, expected))
        self.assertEqual(before, tuple(sha256_file(self.preset.inputs[name]) for name in ("satellite", "mask")))

    def test_strict_rejects_alias_and_tb_compat_resolves_it(self) -> None:
        with self.assertRaisesRegex(RealPreviewError, "STRICT_RGB"):
            render_real_preview(self.preset, request(), variant="balanced", tb_compat=False)
        result = render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        self.assertEqual(result.mask_mode, "TB_COMPAT")
        self.assertFalse(np.array_equal(result.mask_resolved, result.recipe))

    def test_rejects_mismatched_mask_dimensions_and_fractional_regions(self) -> None:
        Image.new("RGB", (64, 64), (10, 20, 30)).save(self.preset.inputs["mask"])
        with self.assertRaisesRegex(RealPreviewError, "mask dimensions"):
            render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        Image.new("RGB", (32, 32), (10, 20, 30)).save(self.preset.inputs["mask"])
        with self.assertRaisesRegex(RealPreviewError, "dimensions"):
            render_real_preview(self.preset, PreviewRequest(0, 0, 8.4, 8, 1), variant="balanced", tb_compat=True)

    def test_rejects_blend_strength_above_one(self) -> None:
        invalid = self.root / "invalid.toml"
        invalid.write_text(self.path.read_text(encoding="utf-8").replace("blend_strength = 0.75", "blend_strength = 1.01", 1), encoding="utf-8")
        with self.assertRaisesRegex(RealPreviewError, "blend_strength"):
            load_real_preview_preset(invalid)

    def test_variants_differ_and_regional_crop_is_consistent(self) -> None:
        outputs = [render_real_preview(self.preset, request(), variant=name, tb_compat=True).combined for name in ("original", "subtle", "balanced", "authored")]
        self.assertFalse(np.array_equal(outputs[0], outputs[1]))
        self.assertFalse(np.array_equal(outputs[1], outputs[2]))
        self.assertFalse(np.array_equal(outputs[2], outputs[3]))
        full = render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        crop = render_real_preview(self.preset, request(x=8, y=8, width=12, height=12, tile=5), variant="balanced", tb_compat=True)
        self.assertTrue(np.array_equal(full.combined[12:24, 8:20], crop.combined))
        tiled = render_real_preview(self.preset, request(tile=5), variant="balanced", tb_compat=True)
        single_tile = render_real_preview(self.preset, request(tile=64), variant="balanced", tb_compat=True)
        self.assertTrue(np.array_equal(tiled.combined, single_tile.combined))

    def test_atomic_failure_never_publishes_final_output(self) -> None:
        target = self.root / "failed.bmp"
        with patch("terrainsat.safety.os.replace", side_effect=OSError("blocked")):
            with self.assertRaisesRegex(OSError, "blocked"):
                write_bmp_atomic(target, np.zeros((2, 2, 3), dtype=np.uint8))
        self.assertFalse(target.exists())

    def test_reference_statistics_are_derived_and_report_normalized_frequency_units(self) -> None:
        reference = self.root / "reference.png"
        Image.new("RGB", (16, 8), (10, 30, 50)).save(reference)
        result = image_statistics(reference)
        self.assertEqual(result["analysis_sample_size"], {"width": 16, "height": 8})
        self.assertEqual(result["frequency_units"], "normalized sample pixels; physical metres are not inferred")
        self.assertIn("high_frequency_mean_abs", result["statistics"])


class RealPreviewCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.preset = write_fixture(Path(self.temporary.name))
        self.output = Path("test-real-preview.bmp")
        for suffix in ("", ".original", ".structure", ".recipe", ".mask_resolved"):
            self.addCleanup(lambda suffix=suffix: (OUTPUT_ROOT / f"test-real-preview{suffix}.bmp").unlink(missing_ok=True))

    def test_output_stays_in_out_and_debug_failure_hides_combined(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            escaped = main([
                "real-preview", "--preset", str(self.preset), "--x", "0", "--y", "0", "--width-m", "8", "--height-m", "8",
                "--meters-per-pixel", "1", "--variant", "balanced", "--tb-compat", "--output", "..\\outside.bmp",
            ])
        self.assertEqual(escaped, 2)

        def fail_debug(path: Path, pixels: np.ndarray) -> None:
            if path.name.endswith(".structure.bmp"):
                raise OSError("debug blocked")
            cli_write_real_bmp_atomic(path, pixels)

        with patch("terrainsat.cli.write_real_bmp_atomic", side_effect=fail_debug), contextlib.redirect_stderr(io.StringIO()):
            status = main([
                "real-preview", "--preset", str(self.preset), "--x", "0", "--y", "0", "--width-m", "8", "--height-m", "8",
                "--meters-per-pixel", "1", "--variant", "balanced", "--tb-compat", "--output", str(self.output), "--diagnostics",
            ])
        self.assertEqual(status, 2)
        self.assertFalse((OUTPUT_ROOT / self.output).exists())


if __name__ == "__main__":
    unittest.main()
