# World config audit

This is a source-level audit of `world/config.cpp`. It distinguishes static
evidence from behavior that must be observed in DayZ.

| Block | Classification | Decision |
| --- | --- | --- |
| `CfgPatches` | KEEP | `units`, `weapons`, required addons and explicit `worlds[]={"Noronha"}` are retained. |
| Coordinates / solar | UNVERIFIED_SEMANTICS | See [SOLAR_CONVENTION_REVIEW.md](SOLAR_CONVENTION_REVIEW.md); no sign change. |
| Map identity fields | SAFE_CHANGE | Labels are compact and the map description must remain diegetic, not describe the island as a jungle. |
| Map textures | MANUAL_ASSET_REQUIRED | Current Enoch references remain valid fallbacks until owned Noronha guide textures exist. |
| Outside terrain | MANUAL_ASSET_REQUIRED | Own outside satellite/tropical layer requires real assets and a visual test. |
| Navmesh config/path | KEEP | Path is present; `navmesh.nm` is protected and not regenerated. |
| Grid / center / plates | KEEP | No source evidence supports coordinate or formatting changes. |
| Lighting | RUNTIME_REVIEW | Existing tropical sequence is coherent source data but requires clear/noon/low-sun/night screenshots. |
| Weather W1-W12 | RUNTIME_REVIEW | Stages are intentionally incremental; do not bulk-retune static values. |
| VolFog / haze | UNVERIFIED_SEMANTICS | `UseDynamic=1` behavior and haze properties are not locally proven. |
| Night sky rotation | UNVERIFIED_SEMANTICS | Rotation does not prove southern-hemisphere correctness; review with the solar test. |
| World sounds | SAFE_CHANGE | Coast uses the locally verified vanilla coast loop. Sound controller/range changes need isolated runtime audio tests. |
| Sound map attenuation | RUNTIME_AUDIO_REVIEW | Test at 100, 300, 500, 800 and 1000 m in coast, settlement, vegetation and behind relief. |
| Ambient FX | RUNTIME_REVIEW | Rain/sea suppression for pollen is source-validated; FX density/species remain visual review. |
| Clutter | RUNTIME_REVIEW | Current values are retained pending popping and performance evidence. |
| Names include | KEEP | CfgConvert validates it; IDs and non-label fields are checked by tooling. |
| Character scenes | MANUAL_RUNTIME_CAMERA_REVIEW | Additional scenes need tested cameras; do not invent coordinates. |
| Intro cutscene | LEGACY_CANDIDATE | `data/scenes/intro.Noronha/init.c` is empty except a comment; remove only after confirming menu scenes work without it. |
| Airport ILS | MANUAL_TB_REVIEW | Runway direction and taxi points require WRP/object evidence. |
| Terrain materials | SAFE_CHANGE | Audit with the read-only surface tool; do not remove generated RVMATs/materials. |

## Surface declaration finding

`source/scripts/audit_surfaces.py` found one existing static discrepancy:
`DZ\surfaces_bliss\data\terrain\en_deforested.rvmat` is listed by
`UsedTerrainMaterials` but is not declared in `source/layers.cfg`. There are no
duplicate legend colours, duplicate layer materials, or missing `Noronha\...`
material files. This is a `MANUAL_TB_REVIEW`: changing `layers.cfg` or
regenerating tiles/RVMATs would exceed this code-only pass.

## Runtime review matrix

Use Remedios, Sancho, Sueste, Porto, Pico and Aeroporto under clear noon,
sunrise, sunset, overcast, storm and night. Capture weather, fog, sound and
camera observations separately so a later adjustment changes one subsystem at
a time.
