import tempfile
import unittest
from pathlib import Path

import audit_sounds as audit


class SoundAuditTests(unittest.TestCase):
    def test_detects_case_and_reads_vorbis_header(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "world").mkdir()
            (root / "sounds").mkdir()
            (root / "docs").mkdir()
            (root / "world" / "config.cpp").write_text('sound="Noronha\\sounds\\bird";', encoding="utf-8")
            (root / "sounds" / "$pboprefix$").write_text("Noronha\\sounds", encoding="utf-8")
            (root / "sounds" / "bird.ogg").write_bytes(b"OggS" + b"\x01vorbis" + struct_pack_vorbis(2, 44100))
            provenance = root / "docs" / "ASSET_PROVENANCE.md"
            provenance.write_text("Noronha\\sounds\\bird", encoding="utf-8")
            report = audit.audit(root, provenance)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["custom_sounds"][0]["ogg"], {"channels": 2, "sample_rate": 44100})


def struct_pack_vorbis(channels, sample_rate):
    import struct
    return struct.pack("<IBI", 0, channels, sample_rate)


if __name__ == "__main__":
    unittest.main()
