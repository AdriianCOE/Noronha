import tempfile
import unittest
from pathlib import Path

import audit_surfaces as audit


class SurfaceAuditTests(unittest.TestCase):
    def test_build_report_finds_undeclared_material_and_duplicate_color(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layers = root / "layers.cfg"
            world = root / "config.cpp"
            generated = root / "layers"
            generated.mkdir()
            layers.write_text(
                'class Layers { class cp_grass { texture="x"; material="DZ\\grass.rvmat"; }; };\n'
                'class Legend { class Colors { cp_grass[]={{1,2,3}}; cp_dirt[]={{1,2,3}}; }; };\n',
                encoding="utf-8",
            )
            world.write_text(
                'class UsedTerrainMaterials { material0="DZ\\grass.rvmat"; material1="DZ\\rock.rvmat"; };',
                encoding="utf-8",
            )
            (generated / "tile.rvmat").write_text("", encoding="utf-8")

            report = audit.build_report(root, layers, world, generated)

        self.assertEqual(report["materials_used_but_not_declared"], ["DZ\\rock.rvmat"])
        self.assertEqual(report["duplicate_legend_colors"], {"(1, 2, 3)": ["cp_grass", "cp_dirt"]})
        self.assertEqual(report["generated_rvmats"], ["tile.rvmat"])


if __name__ == "__main__":
    unittest.main()
