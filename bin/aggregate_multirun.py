#!/usr/bin/env python3

"""Aggregate stats and REx ring measurements across workflow iterations.

Reads results5/iter*/stats_summary.csv and results5/iter*/ring_rex.csv
(as archived by run_iterations.sh) and writes cross-run summary tables:

  results5/chi2_across_runs.csv  — per day/image: chi^2 mean, min, max,
                                   and max-min spread across iterations
  results5/ring_across_runs.csv  — per image: REx diameter/width/
                                   orientation/asymmetry mean, min, max
                                   across iterations

Values that are identical across all iterations (deterministic pipelines)
show spread 0. Usage: aggregate_multirun.py [results5_dir]
"""

import csv
import glob
import os
import sys


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(r for r in f if not r.startswith("#")))


def collect(base, name):
    """{iter_label: rows} for every iter*/name CSV under base."""
    out = {}
    for d in sorted(glob.glob(os.path.join(base, "iter*"))):
        p = os.path.join(d, name)
        if os.path.exists(p):
            out[os.path.basename(d)] = read_csv(p)
    return out


def summarize(rows_by_iter, key_cols, val_cols):
    """Per key tuple: {col: [values across iters]} preserving iter order."""
    acc = {}
    for it in sorted(rows_by_iter):
        for row in rows_by_iter[it]:
            key = tuple(row[k] for k in key_cols)
            acc.setdefault(key, {c: [] for c in val_cols})
            for c in val_cols:
                acc[key][c].append(float(row[c]))
    return acc


def write_summary(path, acc, key_cols, val_cols, n_iters):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        header = list(key_cols) + ["n_runs"]
        for c in val_cols:
            header += [f"{c}_mean", f"{c}_min", f"{c}_max", f"{c}_spread"]
        w.writerow(header)
        for key in sorted(acc):
            vals = acc[key]
            n = len(next(iter(vals.values())))
            row = list(key) + [n]
            for c in val_cols:
                v = vals[c]
                row += [f"{sum(v)/len(v):.4f}", f"{min(v):.4f}",
                        f"{max(v):.4f}", f"{max(v)-min(v):.4f}"]
            w.writerow(row)
    print(f"wrote {path} ({len(acc)} rows, {n_iters} iterations)")


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "results5"
    iters = sorted(glob.glob(os.path.join(base, "iter*")))
    if not iters:
        print(f"no iter*/ directories under {base}")
        sys.exit(1)

    stats = collect(base, "stats_summary.csv")
    if stats:
        acc = summarize(stats, ("day", "image"),
                        ("chisq_cphase", "chisq_logcamp"))
        write_summary(os.path.join(base, "chi2_across_runs.csv"),
                      acc, ("day", "image"),
                      ("chisq_cphase", "chisq_logcamp"), len(stats))

    ring = collect(base, "ring_rex.csv")
    if ring:
        acc = summarize(ring, ("image",),
                        ("d", "d_sigma", "w", "eta_deg", "asym"))
        write_summary(os.path.join(base, "ring_across_runs.csv"),
                      acc, ("image",),
                      ("d", "d_sigma", "w", "eta_deg", "asym"), len(ring))


if __name__ == "__main__":
    main()
