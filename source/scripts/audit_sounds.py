"""Read-only sound reference, provenance and OGG-header audit for Noronha."""

import argparse
import json
import re
import struct
from pathlib import Path


CUSTOM_RE = re.compile(r"Noronha\\sounds\\([A-Za-z0-9_-]+)")
VANILLA_RE = re.compile(r"(?:DZ|dz)\\sounds\\[^\"]+")


def ogg_metadata(path: Path) -> dict[str, int] | None:
    data = path.read_bytes()
    marker = data.find(b"\x01vorbis")
    if marker < 0 or len(data) < marker + 16:
        return None
    _, channels, sample_rate = struct.unpack_from("<IBI", data, marker + 7)
    return {"channels": channels, "sample_rate": sample_rate}


def audit(root: Path, provenance: Path) -> dict[str, object]:
    world = (root / "world" / "config.cpp").read_text(encoding="utf-8", errors="replace")
    sounds_root = root / "sounds"
    prefix = (sounds_root / "$pboprefix$").read_text(encoding="utf-8", errors="replace").strip()
    provenance_text = provenance.read_text(encoding="utf-8", errors="replace")
    provenance_paths = provenance_text.replace(chr(92) * 2, chr(92))
    entries = []
    for sound_id in sorted(set(CUSTOM_RE.findall(world))):
        filename = f"{sound_id}.ogg"
        matches = [path for path in sounds_root.glob("*.ogg") if path.name.lower() == filename.lower()]
        exact = any(path.name == filename for path in matches)
        path = next((path for path in matches if path.name == filename), None)
        metadata = ogg_metadata(path) if path else None
        entries.append({"id": sound_id, "file": filename, "exists": path is not None, "case_correct": exact,
                        "bytes": path.stat().st_size if path else 0, "ogg": metadata,
                        "provenance_documented": f"Noronha\\sounds\\{sound_id}" in provenance_paths})
    vanilla = sorted(set(VANILLA_RE.findall(world)))
    return {"prefix": prefix, "prefix_correct": prefix == "Noronha\\sounds", "custom_sounds": entries,
            "vanilla_references": vanilla,
            "errors": [entry["id"] for entry in entries if not entry["exists"] or not entry["case_correct"]],
            "warnings": [entry["id"] for entry in entries if not entry["provenance_documented"] or entry["ogg"] is None or entry["bytes"] == 0]}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--provenance", type=Path, default=root / "docs" / "ASSET_PROVENANCE.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.root, args.provenance)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"custom={len(report['custom_sounds'])} errors={len(report['errors'])} warnings={len(report['warnings'])}")
    return 1 if report["errors"] or not report["prefix_correct"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
