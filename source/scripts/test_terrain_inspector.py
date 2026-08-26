import tempfile
import unittest
from pathlib import Path

import terrain_inspector as terrain


class TerrainInspectorTests(unittest.TestCase):
    def test_inspect_reports_land_and_slope(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "terrain.asc"
            path.write_text("ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 10\nNODATA_value -9999\n-1 1\n2 3\n", encoding="utf-8")
            data, header = terrain.load_ascii(path)
            report, slope = terrain.inspect(data, header["cellsize"], 0)
        self.assertEqual(report["land_cells"], 3)
        self.assertEqual(report["underwater_cells"], 1)
        self.assertEqual(slope.shape, (2, 2))


if __name__ == "__main__":
    unittest.main()
