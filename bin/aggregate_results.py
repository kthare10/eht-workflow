#!/usr/bin/env python3

"""Aggregate per-day statistics into a CSV table and a markdown report.

Compares our closure chi^2 values against the published EHT Paper IV Table 5
fiducial/top-set values (0% systematic uncertainty) embedded below. The
published values are EHT Collaboration results (allowed source, SPEC.md §2);
comparison against the Patel et al. reproduction is done separately and only
post-hoc (SPEC.md §7).
"""

import argparse
import csv
import json
import sys

# EHT Paper IV Table 5, top-set mean +/- spread at 0% systematic uncertainty:
# (chi2_CP, spread, chi2_logCA, spread)
PAPER_IV_TABLE5 = {
    ("April 5", "difmap"): (9.40, 3.35, 4.99, 1.17),
    ("April 5", "ehtim"): (1.00, 0.13, 0.97, 0.27),
    ("April 5", "smili"): (1.09, 0.21, 1.11, 0.28),
    ("April 6", "difmap"): (4.40, 1.45, 3.49, 1.51),
    ("April 6", "ehtim"): (1.59, 0.16, 1.00, 0.14),
    ("April 6", "smili"): (1.49, 0.23, 1.22, 0.25),
    ("April 10", "difmap"): (3.93, 2.10, 1.57, 0.64),
    ("April 10", "ehtim"): (0.83, 0.10, 1.30, 0.17),
    ("April 10", "smili"): (0.75, 0.14, 1.11, 0.32),
    ("April 11", "difmap"): (4.01, 1.67, 3.33, 1.01),
    ("April 11", "ehtim"): (0.97, 0.10, 0.99, 0.13),
    ("April 11", "smili"): (1.23, 0.28, 1.14, 0.13),
}


def pipeline_of(label):
    """Map an image label like 'difmap_lo' or 'ehtim' to its pipeline key."""
    return label.split("_")[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", action="append", required=True,
                        help="Per-day stats JSON (repeatable)")
    parser.add_argument("--csv-output", required=True, help="Output CSV table")
    parser.add_argument("--report-output", required=True, help="Output markdown report")
    args = parser.parse_args()

    rows = []
    for path in args.input:
        try:
            with open(path) as f:
                day_stats = json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"WARNING: could not read {path}: {e}", file=sys.stderr)
            continue
        date = day_stats.get("date", "?")
        for label, entry in day_stats.get("images", {}).items():
            ref = PAPER_IV_TABLE5.get((date, pipeline_of(label)))
            rows.append({
                "date": date,
                "day": day_stats.get("day", "?"),
                "image": label,
                "zblterm_applied": entry.get("zblterm_applied"),
                "chisq_cphase": entry.get("chisq_cphase"),
                "chisq_logcamp": entry.get("chisq_logcamp"),
                "paperIV_cphase": ref[0] if ref else None,
                "paperIV_cphase_spread": ref[1] if ref else None,
                "paperIV_logcamp": ref[2] if ref else None,
                "paperIV_logcamp_spread": ref[3] if ref else None,
                "error": entry.get("error", ""),
            })

    if not rows:
        print("ERROR: no statistics could be aggregated", file=sys.stderr)
        sys.exit(1)

    fields = list(rows[0].keys())
    with open(args.csv_output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with open(args.report_output, "w") as f:
        f.write("# EHT M87 Reproduction — Closure Statistics Summary\n\n")
        f.write("Reference values: EHT Paper IV Table 5, top-set mean ± spread, "
                "0% systematic uncertainty.\n\n")
        f.write("| Date | Image | χ² CP (ours) | χ² CP (Paper IV) "
                "| χ² logCA (ours) | χ² logCA (Paper IV) |\n")
        f.write("|---|---|---|---|---|---|\n")
        raw_flagged = unknown_flagged = False
        for r in rows:
            # Only zblterm_applied == True counts as recipe-corrected.
            # False = computed on the RAW image (fallback path); a missing
            # key (None) = stats produced without provenance tracking —
            # both must be marked so they are never read as corrected.
            if r["zblterm_applied"] is True:
                mark = ""
            elif r["zblterm_applied"] is False:
                mark, raw_flagged = " \\*", True
            else:
                mark, unknown_flagged = " \\†", True
            cp = (f"{r['chisq_cphase']:.2f}{mark}"
                  if r["chisq_cphase"] is not None else "FAILED")
            ca = (f"{r['chisq_logcamp']:.2f}{mark}"
                  if r["chisq_logcamp"] is not None else "FAILED")
            ref_cp = (f"{r['paperIV_cphase']:.2f} ± {r['paperIV_cphase_spread']:.2f}"
                      if r["paperIV_cphase"] is not None else "-")
            ref_ca = (f"{r['paperIV_logcamp']:.2f} ± {r['paperIV_logcamp_spread']:.2f}"
                      if r["paperIV_logcamp"] is not None else "-")
            f.write(f"| {r['date']} | {r['image']} | {cp} | {ref_cp} | {ca} | {ref_ca} |\n")
        if raw_flagged:
            f.write("\n\\* computed on the raw image — add_zblterm failed, "
                    "so these values are NOT recipe-corrected and are not "
                    "comparable to Paper IV Table 5.\n")
        if unknown_flagged:
            f.write("\n\\† recipe provenance unknown — stats file predates "
                    "zblterm tracking; rerun compute_stats before comparing "
                    "to Paper IV Table 5.\n")
        f.write("\nSee SPEC.md §6 for pass criteria (V4) and §7 for the "
                "post-hoc comparison plan.\n")

    print(f"Aggregated {len(rows)} rows -> {args.csv_output}, {args.report_output}")


if __name__ == "__main__":
    main()
