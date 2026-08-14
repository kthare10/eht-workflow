#!/usr/bin/env python3

"""Compute closure-quantity chi-squared statistics for reconstructed images.

Follows the evaluation recipe of the EHT's own tooling (Paper IV Section 2.1
and Table 5; the imgsum path in ehtim and the fiducial eht-imaging pipeline):

- observations are coherently scan-averaged;
- a large-scale Gaussian zero-baseline component is added to each image
  (``add_zblterm``, uv cut 0.1 Glambda) so intra-site baselines that carry
  extended flux are modeled rather than inflating the statistics;
- closure phases exclude intra-site baselines (``cp_uv_min = 0.1e9``);
- 0% systematic uncertainty, matching the Table 5 column targeted by
  SPEC.md V4. Per Paper IV, DIFMAP values are expected to need systematic
  tolerance (different time averaging), so larger DIFMAP deviations are
  anticipated at 0%.

Best-effort per image: a failing image is recorded with an error and nulls;
the job fails only if every image fails.
"""

import argparse
import json
import sys

import ehtim as eh

UV_ZBLCUT = 0.1e9  # uv-distance separating intra-site baselines (Paper IV)


def load_obs(path):
    obs = eh.obsdata.load_uvfits(path)
    try:
        obs.add_scans()
        obs = obs.avg_coherent(0.0, scan_avg=True)
    except Exception as e:  # noqa: BLE001
        print(f"WARNING: scan-averaging failed for {path} ({e}); "
              f"using unaveraged data", file=sys.stderr)
    return obs


def eval_image(obs, im):
    """Image as evaluated by the EHT tooling: with the zero-baseline
    large-scale component added. Returns (image, zblterm_applied) — on
    failure the raw image is used and flagged, so the results are never
    presented as recipe-corrected when they are not."""
    try:
        return im.add_zblterm(obs, UV_ZBLCUT, debias=True), True
    except Exception as e:  # noqa: BLE001
        print(f"WARNING: add_zblterm failed ({e}); evaluating raw image",
              file=sys.stderr)
        return im, False


def chisq(obs, im, dtype):
    kwargs = {"ttype": "nfft", "systematic_noise": 0, "snrcut": 0}
    if dtype == "cphase":
        kwargs.update(systematic_cphase_noise=0, cp_uv_min=UV_ZBLCUT)
    try:
        return float(obs.chisq(im, dtype=dtype, **kwargs))
    except TypeError:
        # Older chisq signature without the extended kwargs
        return float(obs.chisq(im, dtype=dtype, ttype="nfft"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--obs-lo", required=True, help="Low-band uvfits")
    parser.add_argument("--obs-hi", required=True, help="High-band uvfits")
    parser.add_argument("--image", action="append", required=True,
                        metavar="LABEL=FITS", help="Labeled image (repeatable)")
    parser.add_argument("--day", required=True, help="Day tag, e.g. 095")
    parser.add_argument("--date", required=True,
                        help="Observation date, underscored (e.g. April_5)")
    parser.add_argument("--output", required=True, help="Output JSON")
    args = parser.parse_args()

    bands = {"lo": load_obs(args.obs_lo), "hi": load_obs(args.obs_hi)}

    date = args.date.replace("_", " ")
    results = {"day": args.day, "date": date, "systematic": 0.0,
               "recipe": "scan-avg, add_zblterm, cp_uv_min=0.1e9, snrcut=0",
               "images": {}}
    failures = 0
    for spec in args.image:
        label, _, path = spec.partition("=")
        entry = {"fits": path}
        try:
            im = eh.image.load_fits(path)
            zbl_ok = True
            for band, obs in bands.items():
                im_eval, applied = eval_image(obs, im)
                zbl_ok = zbl_ok and applied
                entry[f"chisq_cphase_{band}"] = chisq(obs, im_eval, "cphase")
                entry[f"chisq_logcamp_{band}"] = chisq(obs, im_eval, "logcamp")
            entry["chisq_cphase"] = (entry["chisq_cphase_lo"] + entry["chisq_cphase_hi"]) / 2
            entry["chisq_logcamp"] = (entry["chisq_logcamp_lo"] + entry["chisq_logcamp_hi"]) / 2
            entry["zblterm_applied"] = zbl_ok
            print(f"{label}: chi2_CP={entry['chisq_cphase']:.2f} "
                  f"chi2_logCA={entry['chisq_logcamp']:.2f}"
                  + ("" if zbl_ok else "  [RAW IMAGE — zblterm not applied]"))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: stats failed for {label} ({path}): {e}", file=sys.stderr)
            entry["error"] = str(e)
            failures += 1
        results["images"][label] = entry

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    if failures == len(args.image):
        print("ERROR: statistics failed for every image", file=sys.stderr)
        sys.exit(1)
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
