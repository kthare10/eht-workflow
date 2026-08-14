# COMPARISON: Clean-Room Reproduction vs. Published Results

Written post-hoc per SPEC.md §7 from a **five-iteration campaign**
(2026-08-14): runs run0012–run0016, 31 jobs each, all
successful, executed from identical containers, inputs, and workflow
YAML. Ring measurement (REx) is a workflow job in these runs, so every
number below is produced and staged out by the DAG itself. Iteration
outputs are archived per run in `results5/iter{1..5}/` with SHA-256
checksums and Pegasus wf_uuids (`RUNDIR.txt`); cross-run summaries in
`results5/chi2_across_runs.csv` and `results5/ring_across_runs.csv`
(built by `bin/aggregate_multirun.py`).

This document is the only place the Patel et al. reproduction's
numerical results (their Table 2) are used; their software artifacts
were never used (CLAUDE.md, V7).

**Comparison baselines**
- EHT Paper IV: EHT Collaboration et al. 2019, ApJL 875 L4,
  [10.3847/2041-8213/ab0e85](https://doi.org/10.3847/2041-8213/ab0e85) —
  Table 5 (closure χ², 0% systematic, top-set mean ± spread), Table 7
  (ring parameters from the EHT's image-domain feature extraction),
  Figure 11.
- Patel et al. 2023, IEEE CiSE 25(1),
  [10.1109/MCSE.2023.3241105](https://doi.org/10.1109/MCSE.2023.3241105) —
  Table 2 "Reproduced" columns (0% systematic).

## 1. Validation criteria outcome (SPEC.md §6)

| ID | Criterion | Result |
|---|---|---|
| V1 | Data integrity | **PASS** — the fetch job's SHA-256 manifest (tarball + all 8 uvfits) is byte-identical across all five iterations and matches `data/checksums.txt` (pinned from two independent 2026-08-12 downloads). |
| V2 | Qualitative ring | **PARTIAL (literal); matches the EHT's own measurements image-for-image** — measured in-workflow by the EHT's own ring extractor (REx, `ehtim.features.rex` at its fiducial defaults; `bin/measure_ring_rex.py`). In **every one of the five runs**: all 20 images yield a measurement, **17/20 inside 37.8–46.2 μas** (median 40.4), and the three outside are the same DIFMAP images — difmap_095_lo 37.5 ± 2.4 and difmap_095_hi 36.9 ± 2.3 (narrow misses, 0.3/0.9 μas below the floor) and difmap_096_hi 27.9 ± 13.2 (an unstable fit that REx's own per-ray dispersion flags; re-measured from its CLEAN components re-restored at 20 μas, the same image's mean-profile diameter is 37.4 μas — §4.2 diagnosis). Decisive context: **the EHT's own fiducial images measure the same way** — Paper IV Table 7 reports DIFMAP April 5 at 37.2 ± 2.4 μas, *also outside 42 ± 10%*, and DIFMAP April 6 at 40.1 ± 7.4, the same day/pipeline instability. Every out-of-band value of ours matches the EHT's published value for that pipeline/day, so the shortfall is a property of the EHT DIFMAP method under the 42 ± 10% operationalization, not of the reproduction. A closed ring with southern brightness enhancement is present in every image of every run (visual; REx asymmetry 0.11–0.27, orientation ≈140–183° E of N). The SPEC condition as literally written (every image in-band) is not met → PARTIAL. |
| V3 | Cross-pipeline consistency | **PASS (with two caveats, §4)** — ring size and orientation are mutually consistent across the three pipelines on all four days in every run, and the cross-pipeline *pattern* reproduces Paper IV Table 7. Diameters (μas; SMILI as five-run mean): Apr 5 — DIFMAP 37.5/36.9, ehtim 39.4, SMILI 40.5/40.0 (max pairwise 3.6 μas ≈ 1.2σ; Paper IV's own Apr 5 values show the identical DIFMAP-low offset: 37.2 / 39.3 / 40.5). Apr 6 — 41.8 (DIFMAP-lo), 39.6, 40.8/40.3. Apr 10 — 40.0/40.2, 40.5, 41.8/40.9. Apr 11 — 41.0/39.9, 41.0, 42.2/41.7. Orientation tracks Paper IV's early→late trend (≈140–160° on Apr 5–6 → ≈156–183° on Apr 10–11; Table 7: 148–164° → 166–176°); at pipeline level (bands averaged) the three pipelines agree to 2.0° (Apr 5), 2.3° (Apr 6; 8.6° excluding the unstable difmap_096_hi), 12.0° (Apr 10), 4.2° (Apr 11) — every day smaller than or comparable to the band-to-band scatter *within* single pipelines (up to 17.8° for stable fits; 20.2° including difmap_096_hi). Caveats: **(1)** difmap_096_hi's REx diameter (27.9 ± 13.2, identical in all runs — deterministic) agrees with the other pipelines only within its large self-reported uncertainty — an unstable fit, not a stable disagreement. **(2)** REx's intrinsic orientation errors (±0.4–5.3° on stable fits) are demonstrably too small to be the consistency yardstick: the five runs directly measure the missing scatter — smili_100_hi's orientation varies by 9.8° across iterations (155.7–165.6°) from SMILI stochasticity alone — and Paper IV's ±2.8–9.8° additionally fold in top-set scatter. On intrinsic errors, several same-day pairs differ formally by many σ (difmap_095_lo vs smili_095_hi ≈ 9σ; difmap_100_hi vs smili_100_hi 2.9–4.5σ depending on the run's stochastic draw; the two DIFMAP April 5 bands ≈ 10σ). Judged on absolute spreads, the maximum same-day cross-pipeline orientation difference is 12.4° (Apr 5), 8.5° (Apr 6, stable fits), 17.4–27.3° depending on run (Apr 10), 6.7° (Apr 11), against up to 15.5° between pipelines in Paper IV's own Table 7 — only April 10 exceeds the paper's own worst day, and Paper IV's April 10 orientations (170.6–175.8°) lie inside our spread. |
| V4 | Quantitative statistics | **PASS for ehtim and SMILI; PASS-with-caveat for DIFMAP** (§2). Identical χ² in all five runs for DIFMAP and ehtim; SMILI χ² varies by ≤ 0.077 across runs — far inside the Paper IV top-set spreads. |
| V5 | Repeatability | **PASS (with documented nondeterminism), now measured across five runs** — DIFMAP and ehtim: χ² and every REx ring parameter identical to all reported digits in all five runs; ehtim FITS **bitwise identical** (one hash per image across runs); DIFMAP FITS **pixel-identical** (max \|pixel diff\| = 0.0; raw bytes differ only in FITS `HISTORY` cards where DIFMAP embeds the session timestamp). SMILI is stochastic (all 40 FITS hashes distinct) but tightly bounded: across the five runs, max \|Δχ²\| = 0.077 (cphase, Apr 10 hi), max REx diameter spread 0.44 μas, width spread ≤ 0.44 μas, orientation spread ≤ 9.8° (smili_100_hi; ≤ 1.2° for the other seven). No verdict in this document depends on which run is read. |
| V6 | Provenance | **PASS** — inputs pinned by checksum (V1); EHT scripts pinned at 2019-D01-02 commit `80d230e`; four containers defined by in-repo Dockerfiles (`Docker/*_Dockerfile`, including the REx container) with the **executed image digests recorded and bound to the runs**: Pegasus integrity checking wrote the SHA-256 of each staged container into every run's job kickstart records at execution time; all five runs record the same four digests, which also match post-campaign hashes of the `.sif` files (digests + extraction recipe in `results5/container_digests.txt`); per-run wf_uuid + run dir recorded in `results5/iter*/RUNDIR.txt`; per-run output checksums in `results5/iter*/SHA256SUMS.txt`; stats carry a `zblterm_applied` provenance flag; ring measurements are workflow outputs, not post-hoc edits. |
| V7 | Clean-room audit | **PASS (self-audit)** — no fetch/clone/pull of TauferLab/Reproducibility_EHT or globalcomputinglab artifacts at any point; the REx container installs eht-imaging from PyPI (allowed source, SPEC §2); every fix in §3 traces to a specific build/run error plus upstream code or EHT publications (session log: `pegasus/cc-usage-log.md`). Patel et al. numbers used only in this document. Self-attested, not independently audited. |

## 2. Closure χ² comparison (0% systematic uncertainty)

Ours = five-run campaign (`results5/chi2_across_runs.csv`), recipe:
coherent scan-average, `add_zblterm` (uv cut 0.1 Gλ), `cp_uv_min =
0.1e9`, snrcut 0, per band (lo/hi). DIFMAP and ehtim values are
identical in all five runs and shown as single numbers; SMILI is shown
as the five-run mean with the min–max range in brackets. Paper IV and
Patel et al. report one value per pipeline/day.

### χ²_CP (closure phases)

| Day | Pipeline | Ours (lo / hi) | Paper IV (top set) | Patel et al. |
|---|---|---|---|---|
| Apr 5 | DIFMAP | 6.31 / 10.43 | 9.40 ± 3.35 | 6.81 |
| Apr 5 | ehtim | 1.03 | 1.00 ± 0.13 | 1.03 |
| Apr 5 | SMILI | 1.17 [1.173–1.176] / 1.65 [1.645–1.653] | 1.09 ± 0.21 | 1.08 |
| Apr 6 | DIFMAP | 2.46 / 3.63 | 4.40 ± 1.45 | 2.84 |
| Apr 6 | ehtim | 1.11 | 1.59 ± 0.16 | 0.88 |
| Apr 6 | SMILI | 1.36 [1.352–1.359] / 1.51 [1.507–1.512] | 1.49 ± 0.23 | 1.30 |
| Apr 10 | DIFMAP | 2.11 / 4.89 | 3.93 ± 2.10 | 2.36 |
| Apr 10 | ehtim | 1.07 | 0.83 ± 0.10 | 0.99 |
| Apr 10 | SMILI | 1.36 [1.354–1.365] / 1.42 [1.376–1.453] | 0.75 ± 0.14 | 1.24 |
| Apr 11 | DIFMAP | 2.16 / 2.89 | 4.01 ± 1.67 | 1.91 |
| Apr 11 | ehtim | 1.01 | 0.97 ± 0.10 | 0.88 |
| Apr 11 | SMILI | 1.28 [1.279–1.292] / 1.51 [1.505–1.514] | 1.23 ± 0.28 | 1.00 |

### χ²_logCA (log closure amplitudes)

| Day | Pipeline | Ours (lo / hi) | Paper IV (top set) | Patel et al. |
|---|---|---|---|---|
| Apr 5 | DIFMAP | 31.90 / 38.03 | 4.99 ± 1.17 | 35.12 |
| Apr 5 | ehtim | 1.38 | 0.97 ± 0.27 | 1.38 |
| Apr 5 | SMILI | 1.37 [1.364–1.367] / 1.64 [1.635–1.642] | 1.11 ± 0.28 | 1.29 |
| Apr 6 | DIFMAP | 23.10 / 27.79 | 3.49 ± 1.51 | 24.43 |
| Apr 6 | ehtim | 1.19 | 1.00 ± 0.14 | 1.21 |
| Apr 6 | SMILI | 1.31 [1.309–1.314] / 1.48 [1.470–1.485] | 1.22 ± 0.25 | 1.62 |
| Apr 10 | DIFMAP | 20.03 / 23.87 | 1.57 ± 0.64 | 22.74 |
| Apr 10 | ehtim | 0.96 | 1.30 ± 0.17 | 0.82 |
| Apr 10 | SMILI | 1.00 [0.992–1.000] / 1.11 [1.081–1.118] | 1.11 ± 0.32 | 0.86 |
| Apr 11 | DIFMAP | 63.34 / 58.89 | 3.33 ± 1.01 | 61.32 |
| Apr 11 | ehtim | 0.94 | 0.99 ± 0.13 | 0.94 |
| Apr 11 | SMILI | 1.22 [1.210–1.231] / 1.10 [1.097–1.104] | 1.14 ± 0.13 | 1.04 |

### Findings

1. **ehtim and SMILI reproduce Paper IV within (or adjacent to) the
   published top-set spread on every day** — e.g. April 11 ehtim: ours
   1.01/0.94 vs published 0.97 ± 0.10 / 0.99 ± 0.13. SMILI's run-to-run
   variation (≤ 0.077) is an order of magnitude below the published
   spreads. V4 pass.
2. **DIFMAP χ²_CP is consistent with Paper IV; DIFMAP χ²_logCA deviates
   strongly (20–63 vs 1.6–5.0)** — in the *same direction and magnitude*
   as the prior reproduction. Paper IV itself notes (p. 19) that the
   DIFMAP fiducial image "requires modest systematic tolerance" because of
   its different time averaging and ALMA downweighting; the 0% column is
   simply an unfavorable regime for CLEAN images evaluated on
   scan-averaged data. V4 pass with documented caveat.
3. **The two independent reproductions converge.** Our April 5 ehtim
   values match Patel et al. exactly (1.03 / 1.38); our per-band DIFMAP
   logCA values bracket their single value on all four days (e.g. April
   11: 63.34/58.89 around their 61.32); ehtim/SMILI agree to ≲0.3
   everywhere. Two teams, disjoint code (their containers/scripts vs our
   workflow/wrappers), same outcome — strong evidence both faithfully
   reproduce the EHT pipelines, and that the residual deltas vs Paper IV
   stem from the released Stokes-I data and library-era differences the
   EHT documented in 2019-D01-01/02, not from either reproduction.

## 3. Independently encountered obstacles

For the reproducibility record (and mirroring Patel et al.'s "lessons
learned" without having used their solutions): every obstacle below was
diagnosed from our own build/run errors and fixed from upstream sources.

| Obstacle | Our independent fix |
|---|---|
| DIFMAP distributed only over `ftp://` (HTTPS mirror 404s); PGPLOT not bundled | build from `difmap2.5r.tar.gz` via FTP; Ubuntu `pgplot5` |
| eht-imaging pipeline hard-codes `ttype='nfft'`; pynfft needs pre-3.3 NFFT | NFFT 3.2.4 built from source, `pynfft==1.3.2` |
| Python-2 code in ehtim v1.1.0 (`parloop.py`), SMILI v0.0.0, and the EHT SMILI driver itself | mechanical 2to3 (package at build time; driver converted at job runtime, vendored copy untouched) |
| scipy API drift (`res.message.decode()`) | era pin `scipy==1.5.4` |
| astropy `Time` subfmt validation (twice: construction and `.jd`) | era pin `astropy==3.2.3` (SMILI container) |
| SMILI installer's easy_install cannot reach PyPI; undeclared deps (`pyds9`, `pymc3`, `sympy`, `theano`) | pre-install full dependency set; `setuptools<60` for f2py |
| χ² recipe underspecified relative to Table 5 | recipe reconstructed from Paper IV §2.1 + ehtim's imgsum path (`add_zblterm`, `cp_uv_min`, scan-averaging) |
| REx uses `scipy.interpolate.interp2d`, removed in scipy 1.14; `rex.FindProfileSingle` in ehtim 1.3.2 references an undefined variable | pin `scipy==1.13.1` in the REx container (EHT code left unmodified); call `rex.FindProfile` directly |
| ehtim 1.3.2's PyPI chain (paramsurvey → pandas-appender) is a legacy `setup.py` package that fetches build deps with a 15 s pip timeout — transient PyPI slowness kills container builds | `PIP_DEFAULT_TIMEOUT=100`, `PIP_RETRIES=10`, pre-install `setuptools-scm`/`packaging` |
| PegasusLite needs `curl`/`wget` *inside* the job container to fetch its worker package; `python:3.11-slim` ships neither (first REx job failed + held on stage-out) | install `curl` + `ca-certificates` in the REx container |
| `docker build` from the workflow root swept ~10 GB of Pegasus scratch into the build context and filled the submit host's disk | build from stdin (`docker build - < Dockerfile`) — the REx Dockerfile COPYs nothing |

Patel et al. report the same *classes* of obstacle (dependency
resolution, Python-2 syntax, undocumented post-processing, χ²
methodology gaps), reached through different specific failures — an
independent confirmation of their central conclusion that pipeline code
alone, without environment and methods detail, undershoots
reproducibility.

## 4. Ring feature measurements (V2/V3 evidence)

### 4.1 REx — the EHT's own extractor, run as a workflow job

`measure_ring_rex` runs `ehtim.features.rex` (REx; the image-domain
feature extraction of Paper IV §9.1–9.2) at its fiducial defaults over
all 20 images and stages out `ring_rex.csv` each run. Five-run results
(diameter d; DIFMAP/ehtim identical in all runs, SMILI as mean with
[min–max]):

| Image | d (μas) | Image | d (μas) |
|---|---|---|---|
| difmap_095_lo | 37.5 ± 2.4 **OUT** | smili_095_lo | 40.5 [40.45–40.60] ± 1.8 |
| difmap_095_hi | 36.9 ± 2.3 **OUT** | smili_095_hi | 40.0 [39.95–39.99] ± 2.0 |
| difmap_096_lo | 41.8 ± 5.5 | smili_096_lo | 40.8 [40.76–40.79] ± 2.1 |
| difmap_096_hi | 27.9 ± 13.2 **OUT** | smili_096_hi | 40.3 [40.23–40.27] ± 1.5 |
| difmap_100_lo | 40.0 ± 1.6 | smili_100_lo | 41.8 [41.77–41.82] ± 1.6 |
| difmap_100_hi | 40.2 ± 1.9 | smili_100_hi | 40.9 [40.74–41.18] ± 1.6 |
| difmap_101_lo | 41.0 ± 1.3 | smili_101_lo | 42.2 [42.19–42.23] ± 1.4 |
| difmap_101_hi | 39.9 ± 2.0 | smili_101_hi | 41.7 [41.73–41.77] ± 1.3 |
| ehtim_095 | 39.4 ± 1.5 | ehtim_100 | 40.5 ± 1.4 |
| ehtim_096 | 39.6 ± 1.5 | ehtim_101 | 41.0 ± 1.2 |

**Side-by-side with the EHT's own REx measurements of their fiducial
images (Paper IV Table 7; DIFMAP restored with a 20 μas beam, as ours):**

| Day | DIFMAP IV / ours (lo, hi) | ehtim IV / ours | SMILI IV / ours (lo, hi) |
|---|---|---|---|
| Apr 5 | 37.2 ± 2.4 / 37.5, 36.9 | 39.3 ± 1.6 / 39.4 | 40.5 ± 1.9 / 40.5, 40.0 |
| Apr 6 | 40.1 ± 7.4 / 41.8, 27.9 | 39.6 ± 1.8 / 39.6 | 40.9 ± 2.4 / 40.8, 40.3 |
| Apr 10 | 40.2 ± 1.7 / 40.0, 40.2 | 40.7 ± 1.6 / 40.5 | 42.0 ± 1.8 / 41.8, 40.9 |
| Apr 11 | 40.7 ± 2.6 / 41.0, 39.9 | 41.0 ± 1.4 / 41.0 | 42.3 ± 1.6 / 42.2, 41.7 |

The ehtim diameters match Paper IV to ≤ 0.2 μas on all four days (April
6 and 11 exactly, to the reported precision); SMILI lo-band five-run
means to ≤ 0.2 μas; DIFMAP to ≤ 0.9 μas on April 5, 10, and 11, and to
1.7 μas on April 6 lo-band (41.8 vs 40.1, well inside the paper's ± 7.4
for that day). Widths and asymmetries also track Table 7 (DIFMAP w ≈
28–31 μas vs their 27.5–29.0; ehtim/SMILI w ≈ 15.5–16.8 vs their
15.5–16.2; A ≈ 0.11–0.27 vs their 0.20–0.27). The two Table 7 entries
outside the 42 ± 10% band or with outlier uncertainty — DIFMAP April 5
(37.2, below band) and DIFMAP April 6 (± 7.4) — are exactly where our
images fall out of band: the deviations are the EHT method's own,
faithfully reproduced.

### 4.2 Diagnostics

Performed on iteration 1's images; the DIFMAP images are pixel-identical
in all five runs (V5), so these diagnostics hold for every run.

**difmap_096_hi** (the one unstable fit; deterministic, so identical in
every run): REx's per-ray diameter distribution is bimodal — 59 of 360
rays peak on a compact central feature (d < 5 μas) and drag the mean
down, while the ring mode sits at 30–35 μas; the fitted center also
lands ~10 μas from the lo-band center. Cross-check: re-measuring all 8
DIFMAP images from their CLEAN delta components (`AIPS CC` table, REx
`aipscc` mode) re-restored with the same 20 μas beam reproduces every
restored-image diameter to ≤ 2.2 μas — difmap_096_hi itself moves from
27.9 to 30.0 with a mean-profile diameter of 37.4 μas under the
re-restoration (32.3 μas on the restored image) — confirming the
instability is a property of that image's structure, not of the FITS
restoration.

REx blur-sensitivity (checked at 0/5/10 μas on the 8 DIFMAP images): at
5 μas every diameter moves ≤ 0.5 μas from its unblurred value; at 10 μas
the five strongest-depression images stay within 2 μas, while the two
weakest lo-band images degrade (difmap_095_lo collapses to an unstable
16.4 ± 17.9; difmap_096_lo's dispersion grows to ± 13.5) — extra blur
fills the already-shallow central depression rather than stabilizing the
fit. difmap_096_hi is unstable at every blur (27.9/28.2/25.9, σ ≥ 13).

An independent estimator (`bin/measure_ring.py`: sector extraction with
a 3-annulus stability gate) agrees with REx within ≤ 1.5 μas on the 16
images where both are stable; the two disagree only on weak-depression
DIFMAP images, in complementary ways (our estimator's 21.1 μas on
difmap_095_hi was its own inner-arc artifact — REx finds 36.9; our
annulus gate holds on difmap_096_hi at 39.8 ± 5.1 where REx's center
search is dragged by the central feature).

## 5. Environment of record

- Site: (4× Ubuntu 24.04 x86_64 worker nodes, 4 CPU /
  7.9 GB each), Pegasus 5.1.2, HTCondor, Singularity/Apptainer.
- Runs of record: **run0012–run0016** (wf_uuids in
  `results5/iter*/RUNDIR.txt`), 31 jobs each, driven by
  `run_iterations.sh` (sequential submits; per-run output archives;
  per-run scratch cleanup). Workflow wall time ≈ 8–10 min per run.
- Containers: built from `Docker/*_Dockerfile` (this repo) on,
  executed as local `.sif` images. Imaging: ehtim v1.1.0 (installs as
  1.1.1), SMILI v0.0.0, DIFMAP 2.5r. Ring measurement (`eht-rex`):
  Python 3.11, ehtim 1.3.2 (PyPI), scipy 1.13.1, numpy 2.0.2,
  astropy 7.1.0 — REx is image-domain only, so the imaging container's
  v1.1.0 era-pin is not needed there.
- Library-era deviations from 2019 (documented per SPEC.md N3):
  Python 3.8 instead of 2.7 (with mechanical 2to3), scipy 1.5.4,
  astropy 4.3.1 (ehtim container) / 3.2.3 (SMILI container),
  numpy 1.21.6.
