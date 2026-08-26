# Runtime test matrix

Static checks do not prove DayZ behavior. Run these scenarios manually or with
future DEV-only DayZ-MCP support, recording screenshots, server/client logs and
the active world time/weather.

| Locations | Scenarios | Observe |
| --- | --- | --- |
| Remedios, Sancho, Sueste, Porto, Pico, Aeroporto, Radar | CLEAR_NOON, SUNRISE, SUNSET, OVERCAST, STORM, CLEAR_NIGHT, RAIN | lighting, fog/haze, terrain readability, names, coast transition, birds, insects and pollen |

For solar validation use the sequence in [SOLAR_CONVENTION_REVIEW.md](SOLAR_CONVENTION_REVIEW.md): 23/02 at 06:00, 09:00, 12:00, 15:00 and 18:00. Treat sound range/occlusion tests at 100, 300, 500, 800 and 1000 metres as `RUNTIME_AUDIO_REVIEW`.
