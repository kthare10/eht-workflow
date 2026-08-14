# SPEC: EHT M87 Black Hole Imaging Workflow (Clean-Room Reproduction)

## 1. Goal

Independently reproduce the first image of the M87\* black hole as a **Pegasus
WMS workflow**, using **only the artifacts publicly released by the Event
Horizon Telescope (EHT) Collaboration** — their data, their code, their
documentation. The reproduction must be built from scratch in this repository.

The Patel et al. 2023 reproducibility paper
(`references/Reproducibility_of_the_First_Image_of_a_Black_Hole...pdf`,
DOI 10.1109/MCSE.2023.3241105) is used **only** as:

1. A source of *expected outcomes* and *validation targets* (what a successful
   reproduction looks like, which discrepancies are known/acceptable).
2. A *comparison baseline* after our results exist: we compare our images and
   statistics against what they reported, to see whether an independent
   clean-room effort converges to the same result.

**None of that paper's software artifacts may be used.** See §3 and
`CLAUDE.md`.

## 2. Allowed sources (EHT Collaboration only)

| Artifact | Source |
|---|---|
| Calibrated visibility data (`.uvfits`, `.csv`, `.txt`) — "First M87 EHT Results, Apr 2019" | CyVerse Data Commons: `commons_repo/curated/EHTC_FirstM87Results_Apr2019` |
| Raw 2017 observation data (released 2022; optional, see §4) | CyVerse Data Commons: `commons_repo/curated/EHTC_2017L1_May2022` |
| Imaging pipeline scripts and parameters | GitHub: `eventhorizontelescope/2019-D01-02` |
| EHT-Imaging library (EHTIM) | GitHub: `achael/eht-imaging` |
| SMILI library | GitHub: `astrosmili/smili` |
| DIFMAP | Caltech: `ftp://ftp.astro.caltech.edu/pub/difmap/` |
| Official EHT container images (if any fit) | Docker Hub: `hub.docker.com/u/eventhorizontelescope` |
| Methods documentation | EHT Papers I–VI (see DOIs below); EHT-HOPS paper (Blackburn et al., ApJ 882 23) |
| EHT Data Products page | eventhorizontelescope.org |

### Primary references (EHT Collaboration et al. 2019, ApJL 875)

PDFs of all papers below are archived in `references/` (Papers I–II from
IOP open access; III–VI and EHT-HOPS from their arXiv postings
1906.11240–11243 and 1903.08832).

| Paper | Role in this project | DOI |
|---|---|---|
| I. The Shadow of the Supermassive Black Hole (L1) | Overall result context | [10.3847/2041-8213/ab0ec7](https://doi.org/10.3847/2041-8213/ab0ec7) |
| II. Array and Instrumentation (L2) | Instrument background | [10.3847/2041-8213/ab0c96](https://doi.org/10.3847/2041-8213/ab0c96) |
| III. Data Processing and Calibration (L3) | Provenance of the calibrated data we consume (C1) | [10.3847/2041-8213/ab0c57](https://doi.org/10.3847/2041-8213/ab0c57) |
| IV. Imaging the Central Supermassive Black Hole (L4) | **Primary methods reference and validation target** (Table 5 → V4, Figure 11 → V2/V3) | [10.3847/2041-8213/ab0e85](https://doi.org/10.3847/2041-8213/ab0e85) |
| V. Physical Origin of the Asymmetric Ring (L5) | Interpretation context | [10.3847/2041-8213/ab0f43](https://doi.org/10.3847/2041-8213/ab0f43) |
| VI. The Shadow and Mass of the Central Black Hole (L6) | Downstream science (out of scope, N6) | [10.3847/2041-8213/ab1141](https://doi.org/10.3847/2041-8213/ab1141) |

EHT-HOPS pipeline (raw-data reduction, out of scope N1): Blackburn et al.
2019, ApJ 882 23, [10.3847/1538-4357/ab328d](https://doi.org/10.3847/1538-4357/ab328d).
Comparison-baseline paper (text-only use, §1/§3): Patel et al. 2023, IEEE
CiSE 25(1), [10.1109/MCSE.2023.3241105](https://doi.org/10.1109/MCSE.2023.3241105).

Generic public infrastructure (PyPI, conda-forge, Spack, base OS/Docker
images, Pegasus/HTCondor) is allowed — it is not an artifact of either paper.

## 3. Forbidden sources

Anything produced by the Patel et al. reproducibility study:

- GitHub: `TauferLab/Reproducibility_EHT` (any file, script, notebook, Dockerfile).
- Docker Hub: `globalcomputinglab/reproducibility-eht` (all containers).
- Their data-validation Jupyter notebooks, post-processing scripts, plotting
  configurations, installation scripts, or dependency lists.
- Copying their fixes verbatim. If we hit the same problems they describe
  (missing dependencies, syntax errors in EHT-Imaging/SMILI, gray-scale
  post-processing for DIFMAP/SMILI), we must derive our own fix from the
  upstream code and documentation. Knowing *that* a problem exists (from the
  paper text) is acceptable; taking their *solution code* is not.

## 4. Scope and constraints

### In scope (constraints — the workflow MUST)

- **C1**: Start from the EHT-released *calibrated* data (`.uvfits`) for the four
  observation days: 2017 April 5, 6, 10, 11 (low and high band).
- **C2**: Run all **three** independent EHT imaging pipelines, as the EHT did:
  - **DIFMAP** (CLEAN deconvolution),
  - **EHT-Imaging / EHTIM** (regularized maximum likelihood),
  - **SMILI** (regularized maximum likelihood),
  using the EHT's own pipeline driver scripts and fiducial parameters from
  `eventhorizontelescope/2019-D01-02`.
- **C3**: Be expressed as a Pegasus workflow (`workflow_generator.py` using
  `Pegasus.api`), following this repository's standard layout
  (`bin/`, `Docker/`, `README.md`).
- **C4**: Each pipeline runs in a container **we build ourselves** (Dockerfiles
  in `Docker/`), with all dependencies pinned and documented. Images published
  under the `kthare10` Docker Hub registry.
- **C5**: Validate input data integrity: record and check checksums (e.g.,
  md5/sha256) of every input file downloaded from CyVerse, so the run is
  verifiable and repeatable.
- **C6**: Produce per-day, per-pipeline final images plus the fiducial
  statistics the EHT reports (closure-phase χ²_CP and log closure-amplitude
  χ²_logCA), and write them to declared Pegasus outputs.
- **C7**: All post-processing (image rendering, figure generation, statistics
  extraction) implemented by us in `bin/`, from EHT documentation only.
- **C8**: Fetch/download jobs follow this repo's fetch-job rules (retry with
  backoff, credentials via `add_env` if ever needed, fail-loud for required
  inputs — write declared outputs before exiting non-zero).

### Out of scope (non-constraints — the workflow need NOT)

- **N1**: Reproduce the raw-data correlation and calibration stage
  (EHT-HOPS / a-priori / network calibration). We start from the released
  calibrated data, as the EHT imaging pipelines themselves do. (The 2022 raw
  data release makes this a possible future extension, not a requirement.)
- **N2**: Match the EHT's exact colormaps, figure styling, or layout. Rendering
  choices are cosmetic; validation is on morphology and statistics.
- **N3**: Achieve bit-identical output images. The EHT itself reports spread
  across parameter choices and library versions; we target consistency within
  that spread (§6).
- **N4**: Reproduce the EHT's parameter surveys / top-set selection. We run the
  fiducial (published) parameter sets only.
- **N5**: Run on any particular hardware. Commodity x86_64 (laptop or HTCondor
  pool) is sufficient; Power9/ARM portability is not required.
- **N6**: Reproduce downstream science (shadow diameter → mass estimation,
  Paper VI). Image reconstruction and its statistics are the end point.

## 5. Expected outcomes

- **E1**: For each of the 4 days × 3 pipelines (12 reconstructions): an image
  showing a **ring of ~40–45 μas diameter** with a **brightness asymmetry
  (brighter southern portion)**, consistent with EHT Paper IV Figure 11.
- **E2**: Closure χ² statistics per day/pipeline in the same range as EHT
  Paper IV Table 5 (0% systematic-uncertainty column).
- **E3**: A reproducible package: `workflow_generator.py`, containers,
  checksums, and a README such that a third party can rerun end-to-end with
  one submit command.
- **E4**: A written comparison report (`COMPARISON.md`) against both:
  - the original EHT Paper IV results, and
  - the Patel et al. reproduced values (their Table 2), noting agreement and
    divergence — produced only **after** our results exist.

## 6. Validation criteria

| ID | Criterion | Pass condition |
|---|---|---|
| V1 | Data integrity | Checksums of downloaded CyVerse files stable across two independent downloads; recorded in-repo. |
| V2 | Qualitative image check | Every day/pipeline image shows a closed ring, diameter ≈ 42 μas (±~10%), with south-side brightness enhancement; ring persists across all four days. |
| V3 | Cross-pipeline consistency | The three pipelines produce mutually consistent ring size and orientation for the same day (the EHT's own bias check). |
| V4 | Quantitative statistics | χ²_CP and χ²_logCA per day/pipeline within the spread the EHT reports for the top-set (Paper IV Table 5); exact match not required (N3). For DIFMAP, larger χ² deviations are acceptable if attributable to documented time-averaging differences. |
| V5 | Repeatability | Two runs of the same workflow from the same containers produce identical statistics (up to documented nondeterminism, if any). |
| V6 | Provenance | Every result traceable to: input checksum + container image digest + pipeline script commit hash + parameter file. |
| V7 | Clean-room audit | No file, dependency, or code fragment in this repo originates from the forbidden sources in §3 (spot-checked before comparison is written). |

## 7. Comparison plan (post-hoc)

Only after V1–V6 are evaluated:

1. Tabulate our χ²_CP / χ²_logCA next to EHT Paper IV Table 5 and Patel et
   al. Table 2; compute deltas.
2. Side-by-side image panels (ours vs. EHT Paper IV Fig. 11).
3. Note where our independent effort hit the same obstacles the paper reports
   (documentation gaps, dependency issues) vs. new ones — this is data for the
   AI-assisted-workflow-generation study, logged in `cc-usage-log.md` and the
   comparison report.

## 8. Deliverables

```
eht-workflow/
├── SPEC.md                  # this file
├── CLAUDE.md                # clean-room rules for AI assistance
├── workflow_generator.py    # Pegasus DAG generator
├── bin/                     # fetch, checksum, run-pipeline, post-process, stats scripts (ours)
├── Docker/                  # Dockerfile.difmap, Dockerfile.ehtim, Dockerfile.smili (ours)
├── data/checksums.txt       # recorded input checksums
├── README.md                # how to run
└── COMPARISON.md            # written last (§7)
```
