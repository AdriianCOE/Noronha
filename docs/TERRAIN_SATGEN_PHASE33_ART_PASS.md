# TerrainSatGen Phase 3.3 material procedural art pass

## Scope and baseline

Phase 3.2 `balanced` remains the accepted baseline and is still rendered when
`real-preview` is invoked without `--art-pass`. Phase 3.3 is a bounded,
read-only comparison mode; it neither changes the source satellite/mask nor
adds Terrain Builder work, terrain analysis, roads, buildings or a full-map
render.

## Diagnosis before the change

The former recipe layer was deliberately small and safe, but its three value
noise bands were isotropic, smooth and equally strong wherever a material was
resolved. This made broad regions coherent but could read as soft cloud-like
variation. It also meant a uniform field and a source region already containing
paths, clearings or field breakup received the same procedural opportunity.

The Phase 3.2 macro/meso/micro source split is retained unchanged. The gap in
this pass is material character and controlled regional coherence, not a reason
to replace the renderer or restore raw orthophoto detail.

## Bounded model

With `--art-pass`, each material can add a small relative patch and motif term:

```
source satellite structure
  + Phase 3.2 frequency preservation
  + relative material modulation
      * source-adaptive strength
```

The patch field combines two world-space value fields after a mild deterministic
domain warp. Its three-band identity image is only a diagnostic; it is not a
new mask, grid or replacement colour. The continuous patch signal is used in
the render so that material regions break organically instead of becoming hard
cells. All seeds include the existing world seed and surface name, so results
are deterministic, crop-consistent and independent of procedural tile size.

Source uniformity is the inverse of a bounded local luminance residual against
a haloed blur. Uniform source regions therefore receive more procedural
influence, while source detail receives less. The configured lower multiplier
is positive: roads and other detail are not turned into an all-or-nothing
classification.

Recipes express different restrained priorities: grass uses dry/lush patches;
forest receives broader internal pockets without individual-tree synthesis;
soil and stubble receive irregular terrestrial breakup; gravel is small and
still protected by the existing water context; concrete is intentionally near
minimal. Stubble anisotropy exists as an optional capability but remains zero
for Noronha in this pass.

## Validation contract

The comparison set is fixed to the confirmed real regions at 1 m/px:

- natural: `(3600, 4500)`, `1024 x 1024 m`;
- airport: `(4800, 5916)`, `1024 x 1024 m`;
- port: `(8500, 7796)`, `1024 x 1024 m`.

The large natural check uses `(3088, 3988)`, `2048 x 2048 m`. Generated
outputs remain below `tools/terrain_satgen/out/`; local reference imagery stays
reference-only and does not contribute pixels or palette values to Noronha.
