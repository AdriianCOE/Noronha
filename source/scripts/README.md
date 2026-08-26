# Noronha authoring placement tools

`coastal_placement.py` is an **offline authoring tool**. It is not loaded by DayZ and does not belong to a runtime script PBO.

The generator reads a heightmap plus surface mask, places configured object categories, and exports Terrain Builder and DayZ Editor files. Placement behavior is stored in `placement_profiles.json` so terrain authors can tune density, height, slope, surface colors, spacing, model pools, and seed without rewriting Python.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Basic usage

```powershell
python coastal_placement.py `
  --heightmap "P:\Noronha_Workspace\terrain\<heightmap>.asc" `
  --surfacemap "P:\Noronha_Workspace\terrain\<surface-mask>.png" `
  --output "P:\Noronha_Workspace\generated\coastal\noronha_coastal"
```

The command writes:

- `<output>_all_tb.txt`
- `<output>_editor.json`
- `<output>_<category>_tb.txt`
- `<output>_stats.json`

Nothing is imported into Terrain Builder automatically.

## Safe iteration

Use a dry run before creating new placement exports:

```powershell
python coastal_placement.py `
  --heightmap "<heightmap.asc>" `
  --surfacemap "<surface-mask.png>" `
  --output "<output-prefix>" `
  --dry-run `
  --stats "<stats.json>"
```

Generate only selected categories when tuning:

```powershell
python coastal_placement.py ... --categories stones,shrubs
```

Override the deterministic seed for an experiment:

```powershell
python coastal_placement.py ... --seed 20260825
```

## Profiles

`placement_profiles.json` is the source of placement behavior. The initial `noronha_coast_v1` profile preserves the existing model pools while removing the old duplicated coastal checks that unintentionally forced reeds, stones, and shrubs back onto the coastal color.

The same profile now declares conceptual biomes (`beach`, `rocky_coast`,
`dry_coast`, `dry_shrub`, `green_shrub`, `wetland`, and `urban_edge`) using
only existing surface-mask colors. They are validated metadata for future
profiles; they do not change `noronha_coast_v1` generation until a category is
explicitly assigned to one.

The current vegetation and moss-stone model pools are **placeholders**, not a statement that those species belong in the final Noronha art direction. Replace model pools only after candidate DayZ/custom assets have been inspected in Terrain Builder/Buldozer.

Future profiles can be added without replacing the current one. Prefer a new profile for a large visual experiment instead of silently rewriting a known-good profile.

## Tests

From this directory:

```powershell
python -m unittest test_coastal_placement.py
```

The tests cover surface matching, non-square surface-map coordinates, spacing, coast detection, and profile validation.
