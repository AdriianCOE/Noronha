# TerrainSatGen

TerrainSatGen is a developer tool for inspecting the inputs used to author a
DayZ terrain satellite map. Version 0.1 is intentionally inspect-only: it reads
`layers.cfg`, an ESRI ASCII heightmap, a satellite image and a surface mask,
then reports alignment, color usage, vanilla references and SHA-256 hashes.

It does not render, recolor or replace terrain assets. It does not invoke
Terrain Builder, RaG, Binarize or DayZ.

## Development installation

Python 3.11 or newer is required.

```powershell
cd P:\Noronha\tools\terrain_satgen
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\Activate.ps1
```

Only NumPy and Pillow are runtime dependencies.

## Usage

After an editable install:

```powershell
terrainsat inspect --preset presets\noronha.toml
python -m terrainsat inspect --preset presets\noronha.toml
```

The checked-in Noronha preset points to the audited read-only inputs. The
current mask is expected to produce `FAIL` because four RGB values do not match
the Legend exactly. Inspect completes the full report before returning exit
code 1.

An optional JSON manifest must be named relative to the tool-owned `out/`
directory:

```powershell
terrainsat inspect --preset presets\noronha.toml --json-out inspect\noronha.json
```

Without `--json-out`, inspect creates no files. Absolute paths, `..` escapes,
symlink escapes and destinations that resolve to an input are rejected before
directories are created. JSON is written to a temporary file and promoted
atomically.

## Statuses

- `PASS`: the check succeeded.
- `WARNING`: inspection completed with a non-blocking finding.
- `FAIL`: a configured validation rule failed; the command returns exit code 1.

Nearest RGB is diagnostic only. TerrainSatGen never treats it as an exact match,
creates aliases automatically or modifies the mask. Noronha's preset contains
no active aliases pending `MANUAL_TB_REVIEW`.

Every report retains `MANUAL_TB_REVIEW` and `RUNTIME_VISUAL_REVIEW`: offline
inspection cannot prove Terrain Builder import behavior or DayZ visuals.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests generate small BMP files in temporary directories. No binary fixtures are
versioned.

## Scope

Preview, generation, comparison, procedural fields, distance fields,
height-aware effects, coastal effects and style analysis are future phases.
They are not registered as commands or represented by empty modules in this
MVP.
