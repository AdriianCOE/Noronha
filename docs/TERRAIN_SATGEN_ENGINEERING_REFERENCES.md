# TerrainSatGen engineering references — read-only audit

**Scope.** Read-only audit on 2026-09-03. It does not authorize Terrain
Builder regeneration, game execution, EMF export, conversion or a feature.

## A. Bohemia satellite/mask reference

Primary reference: [Making Satellite Texture and Mask](https://community.bistudio.com/wiki/Making_Satellite_Texture_and_Mask).
It is historical Visitor / Armed Assault documentation, not DayZ runtime proof.

| Finding | Classification | Boundary |
|---|---|---|
| A hand-authored satellite is appropriate for a fictional layout; aerial imagery plus matching DEM can be reference. | `OFFICIAL_REFERENCE` | Sahrani workflow, not a DayZ renderer requirement. |
| Editable source layers help when roads, cities, vegetation, peaks and coastline change during development. | `LEGACY_VISITOR_REFERENCE` | Visitor/Photoshop project-management guidance. |
| Terrain extent is grid count × terrain cell size; Sahrani's example is 2048² × 10 m = 20480 m and a 20480² raster at 1 px/m. | `OFFICIAL_REFERENCE` | Example arithmetic, not a fixed universal size. |
| Visitor cuts the separate satellite and mask inputs into overlapping smaller squares. | `LEGACY_VISITOR_REFERENCE` | Visitor behavior only. |
| Sahrani's cited square is 512² px and its cited shared border is 16 px. | `LEGACY_VISITOR_REFERENCE` | Project example, not a universal value. |
| A mask square may contain at most four surface types, including overlap. | `CONFIRMED_IN_NORONHA_TB` | Noronha's own 484-segment audit independently observes the same gate. |
| Whole-mask RGB maps to surface definitions in `Layers.cfg`; generated segments reduce to four discrete RGB slots. | `LEGACY_VISITOR_REFERENCE` | Explains the historical constraint. |
| Satellite appearance and categorical surface mask are distinct source representations. | `OFFICIAL_REFERENCE` | Does not define a final-satellite art algorithm. |

### Bounded authoring implication

The source supports a workflow principle, not a current-engine claim:

```text
geographic/aerial reference + surface semantics + editable project structure
    -> authored satellite source
```

It supports `MASK_CATEGORICAL != SATELLITE_FINAL_APPEARANCE`. TerrainSatGen's
relative read-only previews follow that principle, but the reference does not
prove that any output may be promoted without Noronha's existing TB gates.

## B. Noronha correspondence

| Concept | Bohemia reference | Noronha actual | Status |
|---|---|---|---|
| Terrain extent | grid × cell size | 1024² × 10 m = 10240 m | `CONFIRMED_IN_NORONHA_TB` |
| Satellite/mask resolution | Sahrani example: 1 px/m | 10240² over 10240 m = 1 m/px | `CONFIRMED_IN_NORONHA_TB` |
| Source pair | Separate satellite and mask | Separate `gtt_satmap.bmp` and `gtt_mask_osm.bmp` | `CONFIRMED_IN_NORONHA_TB` |
| Segment texture edge | Sahrani example: 512 px | 512 px | `CONFIRMED_IN_NORONHA_TB` |
| Shared border | Sahrani example: 16 px | desired 16 px per side; observed shared overlap 32 px | `CONFIRMED_IN_NORONHA_TB` |
| Effective stride/core | No universal stated value | 480 px; 22 tiles per row | `CONFIRMED_IN_NORONHA_TB` |
| Surface cap | Four including overlap | Four materials per sampled segment | `CONFIRMED_IN_NORONHA_TB` |
| Texture layer | Tutorial example: 40 m | 40 m | `CONFIRMED_IN_NORONHA_TB` |
| Promotion from preview | Not documented | Explicitly blocked pending TB gates | `NOT_APPLICABLE` |

The correspondence validates the segment audit's purpose; it does not replace
observed Terrain Builder behavior with historical Sahrani arithmetic.

## C. Historical topography export

Source: [Killzone Kid — How To Export Topography](https://killzonekid.com/arma-scripting-tutorials-how-to-export-topography/), 2015.

| Tutorial statement | Classification |
|---|---|
| ArmA topography can be exported to `.emf`, described as a vector-rasterisation file. | `HISTORICAL_ARMA3_BEHAVIOR` |
| BIS `EmfToPng.exe` converts EMF to PNG and accepts an optional zoom/resolution parameter. | `HISTORICAL_ARMA3_BEHAVIOR` |
| The converter is described as being in ArmA 3 Tools' Visitor 3 folder. | `HISTORICAL_ARMA3_BEHAVIOR` |
| Activation is described via the ArmA 3 editor's hidden `topography` cheat; `topographz` is noted for QWERTZ. | `HISTORICAL_ARMA3_BEHAVIOR` |
| Initial output could have an incorrect grid, omit airports, and artifact at zoom > 1 on large maps. | `HISTORICAL_ARMA3_BEHAVIOR` |
| A later edit says ArmA 3 1.43.129765 added `ExportNoGrid`, wrote `_nogrid.emf`, and both paths included airports. | `HISTORICAL_ARMA3_BEHAVIOR` |

None establishes `CURRENT_DAYZ_BEHAVIOR`.

## D. Current DayZ and local-tool evidence

| Evidence | Result | Classification |
|---|---|---|
| Local DayZ manifest | App `221100`, build `24689949`; `DayZ_x64.exe` SHA-256 `6E1719275798A69D61DA4F80FA57FB5F2B8D1910C95477ACF1CDC73DA9AF3129`. | `CURRENT_LOCAL_INSTALL_EVIDENCE` |
| Current executable strings | No `ExportNoGrid`, `topographz`, `topography`, `EmfToPng`, or `.emf` string in `DayZ_x64.exe`, `DayZDiag_x64.exe`, or `DayZ_BE.exe`. | `BINARY_STRING_EVIDENCE`; absence is not proof of absence. |
| Local DayZ Tools manifest | App `830640`, build `24570400`; `terrainBuilder.exe` SHA-256 `290102EF3CC2CADF579664295C9410B30772CD0233DE1B4D63A09DC760313966`. | `CURRENT_LOCAL_INSTALL_EVIDENCE` |
| Local tools/text search | No `EmfToPng.exe`, named EMF/topography/export tool, or matching text in `P:\DZ`, `P:\scripts`, DayZ Tools, TB logs or Buldozer logs. | `LOCAL_SEARCH_EVIDENCE` |
| Current Tool binary strings | `terrainBuilder.exe` has no searched export token; `gdal16.dll` has generic `topography`. | `BINARY_STRING_EVIDENCE`; generic GDAL text does not prove an export feature. |

**DayZ support classification: `ARMA3_ONLY_NO_DAYZ_EVIDENCE`.** This is not a
claim that another build or a manual workflow cannot support it.

## E. Optional structure-reference design

If a manual future experiment proves a DayZ-compatible gridless export, it is
an `OPTIONAL_STRUCTURE_REFERENCE`, never a satellite replacement:

```text
satellite -> geographic visual structure
mask      -> surface semantics
topography export (optional) -> roads / settlement / runway reference
procedural -> authored variation
```

Potential uses are road/readability diagnostics, settlement/runway comparison,
map-line preservation checks and studies of official satellite maps against an
independent export. It must never provide reference pixels, geometry, palette
values or automatic edits.

## F. Alignment requirements

No pixel equivalence is presumed. A future export must prove dimensions, pixel
scale, bounds, X/Y orientation, offset, grid status, clipping and coastline
correspondence. Minimum registration: identify Airport and Porto in both
rasters; test candidate axis/orientation; calculate scale/translation from the
two landmarks; then independently check coastline and road agreement. Failure
of the independent check rejects the export.

## G. Manual sandbox plan — do not execute automatically

1. Use an isolated manual DayZ session and temporary output, never the official map/workspace.
2. First prove an official DayZ export invocation and whether gridless mode exists.
3. Export Noronha topography only to temp; record command, build, file, bytes and SHA-256.
4. Convert only with a locally proven tool; record path, version/help evidence and SHA-256.
5. Record PNG dimensions/mode; compare Airport and Porto, then an independent coast/road check.
6. Keep the artifact diagnostic-only; never feed it into TerrainSatGen or TB automatically.

**PASS:** supported origin/tool, grid state explicit, two landmarks plus an
independent feature agree under one transform, inputs unchanged. **FAIL:**
unsupported invocation, unknown converter, grid/clipping ambiguity or failed
independent registration. A failure ends the experiment without pipeline work.

## H. Risks and recommendation

- The Bohemia material source is valuable engineering history, not current DayZ proof.
- Two landmarks propose a transform; they do not prove all projection properties.
- Binary-string scans cannot prove runtime support or lack of it.
- An export may be structurally useful but stylistically unlike satellite data.

`TOPOGRAPHY_REFERENCE_WORTH_TESTING = UNKNOWN` until a manual DayZ-compatible
export path is independently demonstrated. Phase 3.3 retained roads, coast and
port structure in its regional review, therefore
`STRUCTURE_REFERENCE_PRIORITY = LOW` unless later visual review identifies a
specific structural failure.
