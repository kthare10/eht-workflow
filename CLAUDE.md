# CLAUDE.md — eht-workflow

Clean-room reproduction of the EHT M87 black hole image as a Pegasus workflow.
Read `SPEC.md` before doing any work in this directory.

## HARD RULE: Do NOT use the reproducibility paper's artifacts

The PDF in `references/` (Patel et al., "Reproducibility of the First Image of
a Black Hole in the Galaxy M87...", IEEE CiSE, DOI 10.1109/MCSE.2023.3241105)
describes a prior reproduction effort. This project must be independent of it.

**Never use, fetch, clone, copy, adapt, or consult:**

- `github.com/TauferLab/Reproducibility_EHT` — any file: scripts, notebooks,
  Dockerfiles, dependency lists, documentation.
- Docker Hub `globalcomputinglab/reproducibility-eht` — any container image.
- Any code fragment, install command, patch, plotting configuration, or
  dependency pin quoted or described in that paper.

If a problem arises that the paper also describes (missing dependency,
upstream syntax error, gray-scale post-processing), solve it independently
from upstream EHT code and documentation. Do not look up how the paper's
authors solved it. Do not reproduce their fix "from memory."

**The paper text may be used only for:**

1. Defining expected outcomes and validation thresholds (already captured in
   `SPEC.md` §5–§6 — prefer citing SPEC.md rather than re-reading the PDF).
2. The post-hoc comparison in `COMPARISON.md`, written only after our own
   results exist (SPEC.md §7).

When in doubt whether a source is allowed, check SPEC.md §2 (allowed) and §3
(forbidden). Allowed sources are EHT Collaboration releases only: CyVerse data
(`EHTC_FirstM87Results_Apr2019`), `github.com/eventhorizontelescope/2019-D01-02`,
`achael/eht-imaging`, `astrosmili/smili`, Caltech DIFMAP, EHT papers I–VI, and
generic public infrastructure (PyPI, conda-forge, base images, Pegasus/HTCondor).

## Working rules

- Follow the parent repo conventions in `../CLAUDE.md` (workflow layout,
  fetch-job gotchas, `add_env` for credentials, retry/fail-loud rules).
- Pipelines run the EHT's own driver scripts and fiducial parameters from
  `eventhorizontelescope/2019-D01-02`; everything else (fetch, checksum,
  post-processing, stats, figures) is written by us in `bin/`.
- Containers are built by us from `Apptainer/eht-*.def` into local `.sif` files
  that Pegasus stages (`--sif-dir`, default `Apptainer/`). The `Docker/` files
  and the `kthare10` Docker Hub images remain as a fallback. Never pull the
  forbidden containers above.
- Record checksums for every downloaded input in `data/checksums.txt`.
- Write `COMPARISON.md` last, only after validation criteria V1–V6 in SPEC.md
  are evaluated.
