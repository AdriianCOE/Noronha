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

The checked-in Noronha preset points to the audited read-only inputs. Default
inspection is `STRICT_RGB`: it is expected to produce `FAIL` because four RGB
values do not match the Legend byte-for-byte. Inspect completes the full report
before returning exit code 1.

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

Nearest RGB is diagnostic only. TerrainSatGen never creates aliases
automatically or modifies the mask. `--tb-compat` activates only the explicit
aliases declared by the selected preset; it reports them as `explicit_alias`.
Exact Legend RGB always remains exact, and an alias cannot shadow an exact RGB
or reference a missing surface.

The Noronha preset records four Terrain Builder-compatible, off-by-one aliases.
They describe the existing project semantics; they do not rewrite pixels. Use
this explicit mode only when inspecting that known Terrain Builder contract:

```powershell
python -m terrainsat inspect --preset presets\noronha.toml --tb-compat
```

### Terrain Builder surface-segment audit

`--surface-segment-audit` adds a read-only audit over the configured Terrain
Builder sampler model. For Noronha it evaluates 22 x 22 windows from a 512 px
tile, 480 px core stride, 16 px border per side and 32 px shared overlap. The
last core is partial and exterior windows are clipped to the source image.
Counts are distinct resolved surface materials, not raw RGB values. Unknown RGB
produces `UNKNOWN`; more than four materials produces `FAIL`. The full segment
records are available in optional JSON output.

```powershell
python -m terrainsat inspect --preset presets\noronha.toml --tb-compat --surface-segment-audit
```

`--segment-diagnostics` implies the segment audit and writes read-only QA crops
for failing TB-compatible windows beneath `out/tb-segment-audit/`. Each tile
gets the raw mask crop, a clearly labelled diagnostic surface image, a satellite
context crop, an overlay of core/border/highlighted surface and a JSON report.
Those images are evidence only; `mask_resolved.png` is never a valid Terrain
Builder mask or a renderer output.

```powershell
python -m terrainsat inspect --preset presets\noronha.toml --tb-compat --segment-diagnostics
```

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
