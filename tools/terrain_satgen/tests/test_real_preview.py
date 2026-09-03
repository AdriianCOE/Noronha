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
from terrainsat.real_preview import (
    COAST_TRANSITION,
    LAND,
    WATER,
    RealPreviewError,
    _frequency_components,
    _height_context,
    frequency_component_display,
    load_real_preview_preset,
    render_real_preview,
    write_bmp_atomic,
)
from terrainsat.reference_analysis import image_statistics, local_roi_statistics


def write_fixture(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "layers.cfg").write_text(
        """class Layers
{
    class grass { texture = "DZ\\grass.paa"; material = "DZ\\grass.rvmat"; };
    class cp_gravel { texture = "DZ\\gravel.paa"; material = "DZ\\gravel.rvmat"; };
};
class Legend
{
    class Colors
    {
        grass[] = {{10,20,30}};
        cp_gravel[] = {{40,50,60}};
    };
};
""",
        encoding="utf-8",
    )
    elevations = np.full((32, 32), 10.0, dtype=np.float32)
    elevations[:8] = -10.0
    elevations[8:12] = 0.0
    (root / "height.asc").write_text(
        "ncols 32\nnrows 32\nxllcorner 0\nyllcorner 0\ncellsize 1\n"
        + "\n".join(" ".join(f"{value:g}" for value in row) for row in elevations) + "\n",
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
        f'''[world]
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
structure_blur_radius_px = 4
meso_blur_radius_px = 1
[real_preview.variants.subtle]
macro_preservation = 1.0
meso_preservation = 0.9
micro_preservation = 0.8
modulation_strength = 0.25
[real_preview.variants.balanced]
macro_preservation = 1.0
meso_preservation = 0.7
micro_preservation = 0.5
modulation_strength = 0.55
[real_preview.variants.authored]
macro_preservation = 1.0
meso_preservation = 0.4
micro_preservation = 0.2
modulation_strength = 0.9
[real_preview.height_context]
world_x_origin_m = 0
world_y_origin_m = 0
water_level_m = -2
land_level_m = 2
water_original_preservation = 0.9
coast_original_preservation = 0.5
water_modulation_cap = 0.02
coast_modulation_cap = 0.1
[real_preview.recipes.grass]
brightness_offset = -0.02
saturation_adjustment = 0.03
warmth_bias = 0.01
channel_bias = [0, 0, 0]
macro_strength = 0.06
medium_strength = 0.03
local_strength = 0.01
preservation_strength = 0.5
feather_width_m = 3
[real_preview.recipes.cp_gravel]
brightness_offset = -0.03
saturation_adjustment = -0.01
warmth_bias = 0.04
channel_bias = [0.01, 0, -0.01]
macro_strength = 0.05
medium_strength = 0.02
local_strength = 0.01
preservation_strength = 0.5
feather_width_m = 2
[real_preview.context_overrides.cp_gravel.water]
preservation_strength = 0.995
[real_preview.context_overrides.cp_gravel.coast_transition]
preservation_strength = 0.96
''',
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

    def _reloaded(self, replacements: dict[str, str]):
        text = self.path.read_text(encoding="utf-8")
        for before, after in replacements.items():
            text = text.replace(before, after)
        changed = self.root / "changed.toml"
        changed.write_text(text, encoding="utf-8")
        return load_real_preview_preset(changed)

    def test_read_only_and_original_crop_are_exact(self) -> None:
        before = tuple(sha256_file(self.preset.inputs[name]) for name in ("height", "satellite", "mask"))
        result = render_real_preview(self.preset, request(x=4, y=5, width=12, height=10), variant="original", tb_compat=True)
        with Image.open(self.preset.inputs["satellite"]) as image:
            expected = np.asarray(image.crop((4, 17, 16, 27)), dtype=np.uint8)
        self.assertTrue(np.array_equal(result.combined, expected))
        self.assertEqual(before, tuple(sha256_file(self.preset.inputs[name]) for name in ("height", "satellite", "mask")))

    def test_original_is_a_pure_crop_even_when_strict_mask_would_fail(self) -> None:
        result = render_real_preview(self.preset, request(), variant="original", tb_compat=False)
        with Image.open(self.preset.inputs["satellite"]) as image:
            self.assertTrue(np.array_equal(result.combined, np.asarray(image, dtype=np.uint8)))

    def test_strict_rejects_alias_and_tb_compat_resolves_it(self) -> None:
        with self.assertRaisesRegex(RealPreviewError, "STRICT_RGB"):
            render_real_preview(self.preset, request(), variant="balanced", tb_compat=False)
        result = render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        self.assertEqual(result.mask_mode, "TB_COMPAT")
        self.assertFalse(np.array_equal(result.mask_resolved, result.recipe))

    def test_relative_modulation_preserves_luminance_ordering(self) -> None:
        preset = self._reloaded({"macro_strength = 0.06": "macro_strength = 0", "medium_strength = 0.03": "medium_strength = 0", "local_strength = 0.01": "local_strength = 0"})
        result = render_real_preview(preset, request(), variant="authored", tb_compat=True)
        original_luminance = result.original[20, :8].astype(np.float32).mean(axis=1)
        recipe_luminance = result.recipe[20, :8].astype(np.float32).mean(axis=1)
        self.assertTrue(np.all(np.diff(original_luminance) > 0))
        self.assertTrue(np.all(np.diff(recipe_luminance) > 0))

    def test_zero_modulation_is_identity(self) -> None:
        preset = self._reloaded({"modulation_strength = 0.55": "modulation_strength = 0.0", "micro_preservation = 0.5": "micro_preservation = 1.0", "meso_preservation = 0.7": "meso_preservation = 1.0"})
        result = render_real_preview(preset, request(), variant="balanced", tb_compat=True)
        self.assertTrue(np.array_equal(result.original, result.combined))

    def test_frequency_decomposition_is_deterministic_and_recomposes_exactly(self) -> None:
        original = np.asarray(Image.open(self.preset.inputs["satellite"]), dtype=np.uint8)
        one = _frequency_components(self.preset.inputs["satellite"], (0, 0, 32, 32), macro_radius=4, meso_radius=1, original=original)
        two = _frequency_components(self.preset.inputs["satellite"], (0, 0, 32, 32), macro_radius=4, meso_radius=1, original=original)
        self.assertTrue(all(np.array_equal(left, right) for left, right in zip(one, two)))
        macro, meso, micro = one
        self.assertTrue(np.array_equal(macro.astype(np.float32) + meso + micro, original.astype(np.float32)))
        self.assertGreater(np.count_nonzero(frequency_component_display(meso)), 0)

    def test_more_meso_preservation_retains_intermediate_structure_without_restoring_micro(self) -> None:
        lower = self._reloaded({"meso_preservation = 0.7": "meso_preservation = 0.0"})
        higher = self._reloaded({"meso_preservation = 0.7": "meso_preservation = 1.0"})
        low = render_real_preview(lower, request(), variant="balanced", tb_compat=True)
        high = render_real_preview(higher, request(), variant="balanced", tb_compat=True)
        # The same micro weight isolates the visual change to the meso band.
        self.assertFalse(np.array_equal(low.combined, high.combined))
        self.assertLess(
            np.abs(high.combined.astype(np.int16) - high.original.astype(np.int16)).mean(),
            np.abs(low.combined.astype(np.int16) - low.original.astype(np.int16)).mean(),
        )

    def test_micro_reduction_leaves_macro_component_unchanged(self) -> None:
        muted = self._reloaded({"micro_preservation = 0.5": "micro_preservation = 0.0"})
        preserved = self._reloaded({"micro_preservation = 0.5": "micro_preservation = 1.0"})
        muted_result = render_real_preview(muted, request(), variant="balanced", tb_compat=True)
        preserved_result = render_real_preview(preserved, request(), variant="balanced", tb_compat=True)
        self.assertTrue(np.array_equal(muted_result.structure, preserved_result.structure))
        self.assertFalse(np.array_equal(muted_result.combined, preserved_result.combined))

    def test_same_preset_real_render_is_bit_identical(self) -> None:
        first = render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        second = render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        self.assertTrue(np.array_equal(first.combined, second.combined))
        self.assertTrue(np.array_equal(first.meso, second.meso))
        self.assertTrue(np.array_equal(first.micro, second.micro))

    def test_feathering_is_present_and_zero_width_disables_it(self) -> None:
        result = render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        self.assertGreater(np.count_nonzero(result.boundary), 0)
        preset = self._reloaded({"feather_width_m = 3": "feather_width_m = 0", "feather_width_m = 2": "feather_width_m = 0"})
        no_feather = render_real_preview(preset, request(), variant="balanced", tb_compat=True)
        self.assertEqual(np.count_nonzero(no_feather.boundary), 0)

    def test_narrow_structural_feature_keeps_a_nonzero_adjustment(self) -> None:
        with Image.open(self.preset.inputs["mask"]) as image:
            pixels = np.asarray(image, dtype=np.uint8).copy()
        pixels[:, 13:20] = (40, 50, 60)
        Image.fromarray(pixels, "RGB").save(self.preset.inputs["mask"])
        result = render_real_preview(self.preset, request(), variant="authored", tb_compat=True)
        self.assertFalse(np.array_equal(result.recipe[16, 16], result.original[16, 16]))

    def test_height_context_has_confirmed_orientation_edges_and_classes(self) -> None:
        context = _height_context(self.preset, request())
        self.assertEqual(context[0, 0], WATER)
        self.assertEqual(context[8, 0], COAST_TRANSITION)
        self.assertEqual(context[12, 0], LAND)
        self.assertEqual(_height_context(self.preset, request(x=0, y=0, width=1, height=1))[0, 0], LAND)
        self.assertEqual(_height_context(self.preset, request(x=31, y=31, width=1, height=1))[0, 0], WATER)

    def test_water_cap_protects_cp_gravel_and_land_still_modulates(self) -> None:
        result = render_real_preview(self.preset, request(), variant="authored", tb_compat=True)
        water_delta = np.abs(result.recipe[:8, 24:].astype(np.int16) - result.original[:8, 24:].astype(np.int16)).mean()
        land_delta = np.abs(result.recipe[16:, 24:].astype(np.int16) - result.original[16:, 24:].astype(np.int16)).mean()
        self.assertLessEqual(water_delta, 1.0)
        self.assertGreater(land_delta, water_delta)
        final_water_delta = np.abs(result.combined[:8].astype(np.int16) - result.original[:8].astype(np.int16)).mean()
        self.assertLessEqual(final_water_delta, 1.5)

    def test_variants_differ_and_boundary_tiling_and_regional_crop_are_consistent(self) -> None:
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
        self.assertTrue(np.array_equal(tiled.boundary, single_tile.boundary))

    def test_rejects_mismatched_mask_dimensions_fractional_regions_and_invalid_recipe(self) -> None:
        Image.new("RGB", (64, 64), (10, 20, 30)).save(self.preset.inputs["mask"])
        with self.assertRaisesRegex(RealPreviewError, "mask dimensions"):
            render_real_preview(self.preset, request(), variant="balanced", tb_compat=True)
        Image.new("RGB", (32, 32), (10, 20, 30)).save(self.preset.inputs["mask"])
        with self.assertRaisesRegex(RealPreviewError, "dimensions"):
            render_real_preview(self.preset, PreviewRequest(0, 0, 8.4, 8, 1), variant="balanced", tb_compat=True)
        invalid = self.root / "invalid.toml"
        invalid.write_text(self.path.read_text(encoding="utf-8").replace("preservation_strength = 0.5", "preservation_strength = 1.01", 1), encoding="utf-8")
        with self.assertRaisesRegex(RealPreviewError, "preservation_strength"):
            load_real_preview_preset(invalid)

    def test_atomic_failure_never_publishes_final_output(self) -> None:
        target = self.root / "failed.bmp"
        with patch("terrainsat.safety.os.replace", side_effect=OSError("blocked")):
            with self.assertRaisesRegex(OSError, "blocked"):
                write_bmp_atomic(target, np.zeros((2, 2, 3), dtype=np.uint8))
        self.assertFalse(target.exists())

    def test_reference_statistics_are_derived_and_report_normalized_frequency_units(self) -> None:
        reference = self.root / "reference.png"
        Image.new("RGB", (16, 8), (10, 30, 50)).save(reference)
        before = sha256_file(reference)
        result = image_statistics(reference)
        self.assertEqual(result["analysis_sample_size"], {"width": 16, "height": 8})
        self.assertEqual(result["frequency_units"], "normalized sample pixels; physical metres are not inferred")
        self.assertIn("high_frequency_mean_abs", result["statistics"])
        self.assertIn("meso_variance", result["statistics"]["frequency"])
        self.assertIn("edge_preservation_proxy", result["statistics"])
        self.assertEqual(sha256_file(reference), before)

    def test_local_roi_is_read_only_and_has_no_automatic_semantics(self) -> None:
        reference = self.root / "reference.png"
        Image.new("RGB", (16, 8), (10, 30, 50)).save(reference)
        before = sha256_file(reference)
        config = self.root / "local-rois.toml"
        config.write_text(
            f'''[livonia.author_named_test]\nsource = "{reference.as_posix()}"\nx = 2\ny = 1\nwidth = 8\nheight = 4\n''',
            encoding="utf-8",
        )
        results = local_roi_statistics(config)
        self.assertEqual(results[0]["roi_name"], "livonia.author_named_test")
        self.assertEqual(results[0]["semantic_status"], "AUTHOR_NAMED_LOCAL_ROI; no automatic terrain classification")
        self.assertEqual(sha256_file(reference), before)


class RealPreviewCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.preset = write_fixture(Path(self.temporary.name))
        self.output = Path("test-real-preview.bmp")
        for suffix in ("", ".original", ".structure", ".recipe", ".mask_resolved", ".boundary"):
            self.addCleanup(lambda suffix=suffix: (OUTPUT_ROOT / f"test-real-preview{suffix}.bmp").unlink(missing_ok=True))

    def test_output_stays_in_out_and_debug_failure_hides_combined(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            escaped = main(["real-preview", "--preset", str(self.preset), "--x", "0", "--y", "0", "--width-m", "8", "--height-m", "8", "--meters-per-pixel", "1", "--variant", "balanced", "--tb-compat", "--output", "..\\outside.bmp"])
        self.assertEqual(escaped, 2)

        def fail_debug(path: Path, pixels: np.ndarray) -> None:
            if path.name.endswith(".structure.bmp"):
                raise OSError("debug blocked")
            cli_write_real_bmp_atomic(path, pixels)

        with patch("terrainsat.cli.write_real_bmp_atomic", side_effect=fail_debug), contextlib.redirect_stderr(io.StringIO()):
            status = main(["real-preview", "--preset", str(self.preset), "--x", "0", "--y", "0", "--width-m", "8", "--height-m", "8", "--meters-per-pixel", "1", "--variant", "balanced", "--tb-compat", "--output", str(self.output), "--diagnostics"])
        self.assertEqual(status, 2)
        self.assertFalse((OUTPUT_ROOT / self.output).exists())


if __name__ == "__main__":
    unittest.main()
