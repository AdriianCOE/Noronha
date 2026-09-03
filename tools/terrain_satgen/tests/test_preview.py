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

from terrainsat.cli import OUTPUT_ROOT, main, write_bmp_atomic as cli_write_bmp_atomic
from terrainsat.preview import (
    PreviewRequest,
    display_layer,
    load_synthetic_preset,
    render_preview,
    write_bmp_atomic,
)
from terrainsat.procedural import stable_seed


FIXTURES = Path(__file__).resolve().parent / "fixtures"
PRESET_PATH = FIXTURES / "procedural.toml"


def request(*, x: float = 0, y: float = 0, width: float = 512, height: float = 512, mpp: float = 1, tile: int = 128) -> PreviewRequest:
    return PreviewRequest(x, y, width, height, mpp, tile)


class ProceduralPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.preset = load_synthetic_preset(PRESET_PATH)

    def test_stable_seed_uses_process_stable_blake2_derivation(self) -> None:
        self.assertEqual(stable_seed("world", "grass", "macro"), stable_seed("world", "grass", "macro"))
        self.assertNotEqual(stable_seed("world", "grass", "macro"), stable_seed("world", "grass", "medium"))

    def test_deterministic_render_is_bit_identical(self) -> None:
        first = render_preview(self.preset, request())
        second = render_preview(self.preset, request())
        self.assertTrue(np.array_equal(first.combined, second.combined))
        self.assertTrue(np.array_equal(first.surface_map, second.surface_map))

    def test_world_seed_variation_changes_output(self) -> None:
        text = PRESET_PATH.read_text(encoding="utf-8").replace("terrain-satgen-fixture-v1", "other-world")
        with tempfile.TemporaryDirectory() as directory:
            other_path = Path(directory) / "other.toml"
            other_path.write_text(text, encoding="utf-8")
            other = render_preview(load_synthetic_preset(other_path), request())
        self.assertFalse(np.array_equal(render_preview(self.preset, request()).combined, other.combined))

    def test_material_seed_is_independent_of_other_material_pixels(self) -> None:
        text = PRESET_PATH.read_text(encoding="utf-8").replace("forest-surface-v1", "changed-forest-seed")
        with tempfile.TemporaryDirectory() as directory:
            other_path = Path(directory) / "other.toml"
            other_path.write_text(text, encoding="utf-8")
            other = render_preview(load_synthetic_preset(other_path), request())
        original = render_preview(self.preset, request())
        grass = original.surface_map == 0
        self.assertGreater(np.count_nonzero(grass), 0)
        self.assertTrue(np.array_equal(original.combined[grass], other.combined[grass]))

    def test_metres_not_pixels_control_noise_scale(self) -> None:
        origin = render_preview(self.preset, request(width=16, height=16, mpp=1))
        shifted = render_preview(self.preset, request(x=16, width=16, height=16, mpp=1))
        self.assertFalse(np.array_equal(origin.combined, shifted.combined))

    def test_resolution_invariance_at_matching_pixel_centres(self) -> None:
        one_metre = render_preview(self.preset, request(width=16, height=16, mpp=1))
        half_metre = render_preview(self.preset, request(x=0.25, y=0.25, width=8, height=8, mpp=0.5))
        self.assertTrue(np.allclose(one_metre.combined[:8, :8], half_metre.combined[::2, ::2], atol=1e-5))

    def test_aligned_regional_crop_matches_full_render(self) -> None:
        full = render_preview(self.preset, request(width=512, height=512))
        crop = render_preview(self.preset, request(x=128, y=256, width=128, height=128))
        self.assertTrue(np.array_equal(full.combined[256:384, 128:256], crop.combined))

    def test_tiled_render_matches_single_tile_render(self) -> None:
        tiled = render_preview(self.preset, request(tile=73))
        full = render_preview(self.preset, request(tile=4096))
        self.assertTrue(np.array_equal(tiled.combined, full.combined))
        self.assertTrue(np.array_equal(tiled.surface_map, full.surface_map))

    def test_vertical_and_horizontal_tile_seams_match_full_coordinates(self) -> None:
        tiled = render_preview(self.preset, request(tile=128))
        full = render_preview(self.preset, request(tile=4096))
        self.assertTrue(np.array_equal(tiled.combined[:, 127:129], full.combined[:, 127:129]))
        self.assertTrue(np.array_equal(tiled.combined[127:129, :], full.combined[127:129, :]))

    def test_non_even_300_pixel_tiles_match_full_render(self) -> None:
        tiled = render_preview(self.preset, request(width=700, height=650, tile=300))
        full = render_preview(self.preset, request(width=700, height=650, tile=4096))
        self.assertTrue(np.array_equal(tiled.combined, full.combined))

    def test_large_preview_is_rejected_before_full_arrays_are_allocated(self) -> None:
        with self.assertRaisesRegex(ValueError, "safety limit"):
            render_preview(self.preset, request(width=10240, height=10240, tile=300))

    def test_disabled_band_is_zero_and_excluded_from_composition(self) -> None:
        text = PRESET_PATH.read_text(encoding="utf-8").replace("[synthetic.bands.macro]\nenabled = true", "[synthetic.bands.macro]\nenabled = false")
        with tempfile.TemporaryDirectory() as directory:
            disabled_path = Path(directory) / "disabled.toml"
            disabled_path.write_text(text, encoding="utf-8")
            disabled = render_preview(load_synthetic_preset(disabled_path), request())
        self.assertEqual(np.count_nonzero(disabled.macro), 0)
        expected = np.clip(disabled.base + disabled.medium + disabled.local, 0, 255)
        self.assertTrue(np.array_equal(disabled.combined, expected))

    def test_debug_layers_explain_combined_composition(self) -> None:
        result = render_preview(self.preset, request())
        expected = np.clip(result.base + result.macro + result.medium + result.local, 0, 255)
        self.assertTrue(np.array_equal(result.combined, expected))
        self.assertEqual(display_layer(result, "surface_map", self.preset.materials).shape, result.combined.shape)

    def test_fixture_is_not_modified(self) -> None:
        before = PRESET_PATH.read_bytes()
        render_preview(self.preset, request())
        self.assertEqual(PRESET_PATH.read_bytes(), before)


class PreviewCliAndOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output = Path("test-preview.bmp")
        self.addCleanup(lambda: (OUTPUT_ROOT / self.output).unlink(missing_ok=True))
        for name in ("base", "macro", "medium", "local", "surface_map"):
            self.addCleanup(lambda name=name: (OUTPUT_ROOT / f"test-preview.{name}.bmp").unlink(missing_ok=True))

    def test_cli_writes_combined_and_debug_layers_inside_out(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            status = main([
                "preview", "--preset", str(PRESET_PATH), "--x", "0", "--y", "0", "--width-m", "32", "--height-m", "32",
                "--meters-per-pixel", "1", "--output", str(self.output), "--debug-layers",
            ])
        self.assertEqual(status, 0)
        with Image.open(OUTPUT_ROOT / self.output) as image:
            self.assertEqual(image.size, (32, 32))
        self.assertTrue((OUTPUT_ROOT / "test-preview.surface_map.bmp").exists())

    def test_cli_rejects_external_output_and_real_noronha_preset(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            escaped = main([
                "preview", "--preset", str(PRESET_PATH), "--x", "0", "--y", "0", "--width-m", "8", "--height-m", "8",
                "--meters-per-pixel", "1", "--output", "..\\outside.bmp",
            ])
            real = main([
                "preview", "--preset", "presets/noronha.toml", "--x", "0", "--y", "0", "--width-m", "8", "--height-m", "8",
                "--meters-per-pixel", "1", "--output", "real.bmp",
            ])
        self.assertEqual(escaped, 2)
        self.assertEqual(real, 2)
        self.assertFalse((OUTPUT_ROOT / "real.bmp").exists())

    def test_atomic_write_failure_leaves_no_final_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "failed.bmp"
            with patch("terrainsat.safety.os.replace", side_effect=OSError("blocked")):
                with self.assertRaisesRegex(OSError, "blocked"):
                    write_bmp_atomic(target, np.zeros((4, 4, 3), dtype=np.uint8))
            self.assertFalse(target.exists())

    def test_debug_write_failure_leaves_requested_combined_output_absent(self) -> None:
        def fail_debug(path: Path, pixels: np.ndarray) -> None:
            if path.name.endswith(".base.bmp"):
                raise OSError("debug blocked")
            cli_write_bmp_atomic(path, pixels)

        with patch("terrainsat.cli.write_bmp_atomic", side_effect=fail_debug), contextlib.redirect_stderr(io.StringIO()):
            status = main([
                "preview", "--preset", str(PRESET_PATH), "--x", "0", "--y", "0", "--width-m", "32", "--height-m", "32",
                "--meters-per-pixel", "1", "--output", str(self.output), "--debug-layers",
            ])
        self.assertEqual(status, 2)
        self.assertFalse((OUTPUT_ROOT / self.output).exists())
