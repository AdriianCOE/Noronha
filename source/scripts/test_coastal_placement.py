import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import coastal_placement as cp


class PlacementCoreTests(unittest.TestCase):
    def test_matches_any_surface_uses_tolerance(self):
        self.assertTrue(cp.matches_any_surface((100, 100, 100), [(105, 100, 100)], 6))
        self.assertFalse(cp.matches_any_surface((100, 100, 100), [(110, 100, 100)], 6))

    def test_world_to_surface_supports_non_square_inputs(self):
        shape = (100, 200, 3)
        row, col = cp.world_to_surface(500.0, 250.0, shape, 1000.0, 500.0)
        self.assertEqual((row, col), (49, 100))

    def test_placement_grid_spacing(self):
        grid = cp.PlacementGrid(cell_size=8.0)
        grid.add(100.0, 100.0)
        self.assertTrue(grid.too_close(102.0, 103.0, 4.0))
        self.assertFalse(grid.too_close(110.0, 110.0, 4.0))

    def test_real_coast_checks_diagonal_land(self):
        header = cp.MapHeader(
            ncols=9,
            nrows=9,
            xllcorner=0.0,
            yllcorner=0.0,
            cellsize=10.0,
            nodata=-9999.0,
        )
        terrain = np.zeros((9, 9), dtype=float)

        # Candidate is around the map center. Put dry land on a diagonal sample.
        row, col = cp.world_to_heightmap(60.0, 60.0, header)
        terrain[row, col] = 2.0

        self.assertTrue(
            cp.is_real_coast(
                40.0,
                40.0,
                terrain,
                header,
                search_radius=28.284271,
                min_land_height=1.0,
            )
        )

    def test_profile_validation_rejects_unknown_surface(self):
        profile = {
            "global": {},
            "surfaces": {"coastal": [1, 2, 3]},
            "categories": {
                "boats": {"surfaces": ["missing"]},
                "reeds": {"surfaces": []},
                "stones": {"surfaces": []},
                "debris": {"surfaces": []},
                "shrubs": {"surfaces": []},
            },
        }
        with self.assertRaises(ValueError):
            cp.validate_profile("test", profile)

    def test_load_profile_reads_selected_profile(self):
        payload = {
            "profiles": {
                "test": {
                    "global": {},
                    "surfaces": {"coastal": [1, 2, 3]},
                    "categories": {
                        "boats": {"surfaces": ["coastal"]},
                        "reeds": {"surfaces": ["coastal"]},
                        "stones": {"surfaces": ["coastal"]},
                        "debris": {"surfaces": ["coastal"]},
                        "shrubs": {"surfaces": ["coastal"]},
                    },
                }
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            profile = cp.load_profile(path, "test")
        self.assertEqual(profile["surfaces"]["coastal"], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
