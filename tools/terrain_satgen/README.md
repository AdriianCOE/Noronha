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

## Real regional preview

`real-preview` is the Phase 3, read-only renderer for bounded Noronha regions.
It crops the registered current satellite and mask, uses only explicit aliases
when `--tb-compat` is selected, separates a broad structure component with a
haloed Gaussian blur, and applies small world-space recipes per resolved
surface. It never writes an input, runs Terrain Builder, generates layers or
renders the full 10240 x 10240 map.

`original` is a faithful satellite-only crop; it does not require mask aliases
or height context. `subtle`, `balanced`, and `authored`
respectively reduce high-frequency photographic detail and increase the
surface-recipe contribution. Since Phase 3.2, the source crop is decomposed
with two haloed Gaussian low passes: `macro = blur(large)`,
`meso = blur(small) - blur(large)`, and `micro = original - blur(small)`.
Each variant has explicit preservation weights for those three components.
`balanced` keeps macro fully, favors meso, and suppresses micro more strongly;
it therefore preserves real paths, clearings and field breakup before adding
any procedural variation. In Phase 3.1+ those recipes are **relative
modulations** of the satellite (luminance, saturation, warmth and bounded
world-space variation), not replacement RGB colours. They retain local source
luminance and taper inside a bounded feather zone at material boundaries.

The Noronha preset samples the authoritative ASC read-only using the confirmed
Mapframe/ASC lower-left origin. It derives only `WATER`, `COAST_TRANSITION` and
`LAND`; `cp_gravel` in water therefore preserves the original satellite instead
of receiving a terrestrial treatment. This is preview context only: neither
the ASC nor the mask is changed and it is not a Terrain Builder promotion rule.

```powershell
python -m terrainsat real-preview --preset presets\noronha.toml `
  --x 5200 --y 3300 --width-m 1024 --height-m 1024 --meters-per-pixel 1 `
  --variant balanced --tb-compat --diagnostics --output previews\field-balanced.bmp
```

The coordinate convention is the registered Terrain Builder world system: `x`
and `y` are the crop's lower-left origin in metres and must align to its 1 m/px
source grid. The renderer converts that lower-left Y convention to top-down
image rows. Outputs are bounded to 2048² pixels and must be relative to `out/`.
The blur reads a three-radius halo around each crop. The bounded boundary
feather reads a mask halo equal to its largest configured width. Thus a nested
regional crop matches the same pixels from its containing render. `STRICT_RGB` remains a
diagnostic option and correctly rejects Noronha's four off-by-one RGB values.
`--diagnostics` also writes the macro, signed-meso and signed-micro diagnostics
(the latter two are centred at neutral grey only for inspection), plus a small
JSON sidecar that records the selected world region, variant and mask mode; it never records or writes source pixels. Its
`mask_resolved` image is a flat, deterministic surface-class diagnostic, not a
procedural recipe layer or a valid Terrain Builder mask. The optional `boundary`
diagnostic shows only the renderer's feather zone; it is not a mask output.

Phase 3.3 adds an opt-in `--art-pass` for controlled material motifs. It keeps
the Phase 3.2 renderer as the default comparison path, then adds mild warped
world-space patches and source-adaptive modulation: uniform source areas receive
somewhat more material variation while roads, field breakup and other existing
local structure receive less, never zero, modulation. Recipes remain relative
to the original satellite; they do not use reference pixels, edit inputs or
infer a new mask. The art-pass diagnostics additionally include source
uniformity, patch identity, warped meso field, forest motif and final adaptive
strength. Stubble anisotropy is configured at zero in the Noronha preset.

```powershell
python -m terrainsat real-preview --preset presets\noronha.toml `
  --x 3600 --y 4500 --width-m 1024 --height-m 1024 --meters-per-pixel 1 `
  --variant balanced --tb-compat --art-pass --diagnostics `
  --output previews-phase33\natural-balanced-33.bmp
```

### Local style references

Named local reference images may be analyzed only for derived statistics. The
tool never copies their pixels into an output or the repository. Frequencies
remain normalized sample pixels unless the reference's physical scale is
separately proven. This command writes only JSON beneath `out/`:

```powershell
python -m terrainsat reference-analysis `
  --reference P:\chernarus-satmap.png --reference P:\livonia-satmap.png `
  --image previews\field-original.bmp --image previews\field-balanced.bmp
```

The bounded analysis records RGB/luminance/saturation distributions, local
contrast, clipping, an edge-persistence proxy, and deterministic
macro/meso/micro energy bands. They are diagnostic comparisons, not a synthetic
quality score or a palette source. Reference physical scale is never inferred.
For confirmed Noronha 1 m/px outputs, pass `--image-meters-per-pixel 1` to also
record the band radii in metres.

Optional author-named reference ROIs can live only below the ignored `out/`
directory, for example `out/reference-analysis/local-rois.toml`:

```toml
[livonia.rural_mixed]
source = "P:/local/livonia-satmap.png"
x = 100
y = 200
width = 1024
height = 1024
```

They are read-only crops: neither the ROI paths, coordinates nor source pixels
are versioned. The tool does no semantic classification; without this local
file it marks global reference statistics as provisional.

```powershell
python -m terrainsat reference-analysis `
  --reference P:\chernarus-satmap.png --reference P:\livonia-satmap.png `
  --image previews-phase32\natural-balanced.bmp `
  --image-meters-per-pixel 1 `
  --local-roi-config reference-analysis\local-rois.toml `
  --output reference-analysis\phase32.json
```

## Scope

TerrainSatGen is intentionally not a terrain generation or Terrain Builder
promotion pipeline. WRP/navmesh, source satellite and mask files, Terrain
Builder, roads, height/slope/aspect/curvature/moisture/coastal systems, PAA
export and runtime integration remain outside its contract.
