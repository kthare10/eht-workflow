# Provenance of vendored EHT pipeline files

All files in this directory are **verbatim copies** from the EHT
Collaboration's official imaging-pipelines release (an allowed source per
SPEC.md §2). Do not modify them; wrappers in `bin/` adapt around them.

- **Source repository**: https://github.com/eventhorizontelescope/2019-D01-02
- **Commit**: `80d230e76c08edd31548e7cfe61dc7cf94300780`
- **Vendored on**: 2026-08-12
- **License**: GPLv3 (per the headers in the EHT scripts; full text in `LICENSE` in this directory)

| File | Origin path in source repo | Role |
|---|---|---|
| `EHT_Difmap` | `difmap/EHT_Difmap` | DIFMAP CLEAN imaging script (fiducial parameters) |
| `CircMask_r30_x-0.002_y0.022.win` | `difmap/CircMask_r30_x-0.002_y0.022.win` | DIFMAP cleaning-window mask |
| `eht-imaging_pipeline.py` | `eht-imaging/eht-imaging_pipeline.py` | eht-imaging (EHTIM) RML pipeline |
| `smili_imaging_pipeline.py` | `smili/smili_imaging_pipeline.py` | SMILI RML pipeline |

Fiducial DIFMAP calling sequence (from the EHT README, used by
`bin/run_difmap.py`):

```
@EHT_Difmap <uvfits-basename>,CircMask_r30_x-0.002_y0.022,-10,0.5,0.1,2,-1
```
