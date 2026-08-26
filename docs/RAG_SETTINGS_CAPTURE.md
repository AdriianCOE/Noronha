# RaG settings capture

No RaG wrapper is created until a known-good GUI build is captured. Record the
following values from that successful run; leave unknown fields blank rather
than guessing them.

| Field | Captured value |
| --- | --- |
| RaG version | |
| project root | |
| source per addon | |
| output directory | |
| temporary directory | |
| CfgConvert | |
| Binarize | |
| ImageToPAA | |
| excluded extensions/folders | |
| signing enabled | |
| private-key handling | |
| preflight sequence | |
| parallelism | |

After capture, validate the resulting PBO directory with
`Noronha_Workspace/tools/validate_build.py` before considering automation.
