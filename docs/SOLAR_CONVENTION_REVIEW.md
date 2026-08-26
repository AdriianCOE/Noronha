# Solar convention review

## Status

`UNVERIFIED_SEMANTICS` — Noronha retains `latitude=-3.84` and
`longitude=-32.42` unchanged.

## Evidence checked

- `world/config.cpp` is explicit about the intended real-world coordinates.
- The locally available Nyheim source contains only commented latitude and
  longitude examples; it does not document the engine's sign convention.
- No local vanilla `WorldData` or solar-position implementation was available
  to establish whether DayZ follows geographic latitude signs directly.

Consequently, changing the sign would be an unsupported visual/geographic
guess, not an engineering correction.

## Required DayZ review

Use `23/02/2026` and record screenshots plus compass direction at:

| Time | Verify |
| --- | --- |
| 06:00 | sunrise direction and horizon visibility |
| 09:00 | rising sun trajectory |
| 12:00 | sun side and shadow direction |
| 15:00 | descending trajectory |
| 18:00 | sunset direction and twilight |

Run the same test on a confirmed vanilla world only as an engine-control
comparison. Do not change Noronha's signs unless the observed DayZ convention
and the target southern-hemisphere behavior are both documented.
