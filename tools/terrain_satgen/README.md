# TerrainSatGen

TerrainSatGen is a developer tool for inspecting the inputs used to author a
DayZ terrain satellite map and rendering explicitly synthetic previews. It reads
`layers.cfg`, an ESRI ASCII heightmap, a satellite image and a surface mask,
then reports alignment, color usage, vanilla references and SHA-256 hashes.

It never renders, recolors or replaces the Noronha assets. It does not invoke
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

## Synthetic procedural preview

`preview` accepts only a TOML file whose top level is `mode = "synthetic"`.
It rejects the Noronha inspection preset before it can create an output. The
fixture has four deliberately distinct, irregular procedural regions: grass,
forest, dirt and rock. It is a test pattern, not a reconstruction of Noronha.

```powershell
terrainsat preview --preset tests\fixtures\procedural.toml --x 0 --y 0 `
  --width-m 1024 --height-m 1024 --meters-per-pixel 1 --output preview.bmp
```

The output is written to `tools\terrain_satgen\out\preview.bmp`; `--output`
is always relative to that directory. `--debug-layers` additionally writes
`preview.base.bmp`, `preview.macro.bmp`, `preview.medium.bmp`,
`preview.local.bmp` and `preview.surface_map.bmp` beside it. Output promotion
is atomic.

Synthetic previews are intentionally bounded to 4,194,304 pixels (the tested
2048² maximum), preventing accidental 10K/20K renders before their arrays are
allocated.

All samples use the pixel-centre coordinate convention
`origin + (pixel + 0.5) * metres-per-pixel`, including tiles and regional
crops. The BLAKE2-derived seeds and absolute metre coordinates make a 1 m/px
sample agree with the matching 0.5 m/px sample and make aligned regional crops
match a full render. No filter is applied, so tiles require no halo.

Preview bands are independently enabled in the synthetic TOML. Their macro,
medium and local value-noise fields are vectorized NumPy hash-grid samples;
there is no Python per-pixel random loop or external noise package. Float32
layers are composited before final clamping, and the command reports the count
of clipped pixels.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests generate small BMP files in temporary directories. No binary fixtures are
versioned.

## Scope

The synthetic preview is intentionally not a terrain generation pipeline.
Real Noronha satellite input, masks, aliases, Terrain Builder, WRP/navmesh,
roads, height/slope/aspect/curvature/moisture/coastal fields, PAA export and
runtime integration remain outside its contract.
