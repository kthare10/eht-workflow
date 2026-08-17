# EHT M87 Black Hole Imaging Workflow

A Pegasus WMS workflow that reproduces the first image of the M87\* black
hole from the Event Horizon Telescope's public 2017 data release — built
clean-room from **EHT Collaboration sources only** (see `SPEC.md` for scope
and `CLAUDE.md` for the sourcing rules).

## Pipeline

```
fetch_data (2019-D01-01 uvfits + SHA-256 verification)
    │
    ├── per day (April 5 / 6 / 10 / 11, 2017):
    │     ├── difmap_lo, difmap_hi     (DIFMAP CLEAN, per band)
    │     ├── ehtim                    (eht-imaging RML, lo+hi)
    │     ├── smili_lo, smili_hi       (SMILI RML, per band)
    │     ├── render  → m87_<day>_panel.png
    │     └── stats   → stats_<day>.json  (closure χ²_CP, χ²_logCA)
    │
    ├── aggregate → stats_summary.csv + summary_report.md
    └── measure_ring_rex (all 20 images) → ring_rex.csv
          (REx — the EHT's own ring extractor, Paper IV §9)
```

The three imaging jobs run the EHT's own fiducial driver scripts, vendored
verbatim in `eht-pipelines/` (pinned commit — see
`eht-pipelines/PROVENANCE.md`). Everything else (`bin/`, `Docker/`) is
written for this project.

![Workflow DAG](workflow.png)

## Prerequisites

- Pegasus WMS + HTCondor (or a Kiso-provisioned site)
- Apptainer on the submit host (to build) and on the worker nodes (to run)
- Containers (build once; no registry push, Pegasus stages the `.sif` files):

```sh
apptainer build Apptainer/eht-difmap.sif Apptainer/eht-difmap.def
apptainer build Apptainer/eht-ehtim.sif  Apptainer/eht-ehtim.def
apptainer build Apptainer/eht-smili.sif  Apptainer/eht-smili.def
apptainer build Apptainer/eht-rex.sif    Apptainer/eht-rex.def
```

`workflow_generator.py` resolves each container as `<sif-dir>/eht-<name>.sif`,
and `--sif-dir` defaults to `Apptainer/` — so the filenames above matter. Pass
`--sif-dir ''` to fall back to pulling `docker://kthare10/eht-*:latest` from
Docker Hub instead.

`./deploy_pegasus.sh` does the whole sequence: builds any missing `.sif`,
generates the workflow, plans and submits.

**Apptainer cannot build on macOS**, and a `.sif` has no multi-arch manifest —
one file, one architecture. `eht-smili` and `eht-ehtim` in particular compile
NFFT and SMILI from source, so build them on a Linux host matching the worker
nodes. See `../APPTAINER.md`. The legacy `Docker/*_Dockerfile` files are kept as
a fallback.

## Usage

```sh
# Generate the DAG (all 4 days, all 3 pipelines + ring measurement: 31 jobs)
python3 workflow_generator.py --output workflow.yml

# Smaller test: one day, no SMILI
python3 workflow_generator.py --days 101 --skip-smili --output workflow.yml

# Submit and monitor
pegasus-plan --submit -s condorpool -o local workflow.yml
pegasus-status <run-dir>
```

Options: `--days {095,096,100,101}`, `--skip-difmap`, `--skip-ehtim`,
`--skip-smili`, `--smili-nproc N`, `--exec-site NAME`, `--skip-sites-catalog`.

## Outputs (in `output/`)

| File | Content |
|---|---|
| `checksums_manifest.txt` | SHA-256 of every downloaded input (validation V1/V6) |
| `difmap_<day>_<band>.fits` / `.stat` | DIFMAP CLEAN image + fit statistics |
| `ehtim_<day>.fits` | eht-imaging reconstruction (lo+hi) |
| `smili_<day>_<band>.fits` | SMILI reconstruction |
| `m87_<day>_panel.png` | Side-by-side panel of all reconstructions |
| `stats_<day>.json` | Closure χ² per image vs both bands |
| `stats_summary.csv`, `summary_report.md` | Aggregate vs EHT Paper IV Table 5 |
| `ring_rex.csv` | REx ring diameter/width/orientation/asymmetry per image (V2/V3) |

## Validation

Expected result: a ~42 μas ring, brighter in the south, on every day from
every pipeline, with closure χ² consistent with EHT Paper IV Table 5.
Full criteria in `SPEC.md` §6; the post-hoc comparison against the
reproducibility literature is in `COMPARISON.md` (§7), based on a
five-iteration campaign whose per-run outputs, checksums, wf_uuids, and
container digests are archived under `results5/`. Repeat it with
`./run_iterations.sh 5` and `bin/aggregate_multirun.py results5`.

## Local smoke test

`./run_manual.sh` runs fetch + eht-imaging + render + stats for one day
without Pegasus (inside the ehtim container or a matching venv).

## License

Apache License 2.0 (see `LICENSE`) for everything written for this project
(`workflow_generator.py`, `bin/`, `Docker/`, scripts, documentation).
The vendored EHT pipeline files in `eht-pipelines/` are the EHT
Collaboration's own and remain under **GPLv3** per their headers — the
full GPLv3 text is included at `eht-pipelines/LICENSE` as its terms
require (see `eht-pipelines/PROVENANCE.md` for origin and pinning).
