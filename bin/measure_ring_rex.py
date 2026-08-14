#!/usr/bin/env python3

"""Measure ring parameters with REx, the EHT's own ring extractor (V2/V3).

Runs `ehtim.features.rex` (Chael et al., eht-imaging; the image-domain
feature-extraction method of EHT Paper IV §9.1–9.2) on reconstructed M87
images, with REx's fiducial defaults: regrid to a 160 μas / 160 px FOV,
threshold the center-search image at 5% of peak, grid-search the ring
center that minimizes the relative dispersion of per-ray peak radii,
then measure 360 radial profiles between r = 5 and 50 μas.

Reported per image (matching Paper IV Table 7 columns):
  d   = REx `ring_diameter` (RingSize1): mean of the 360 per-ray peak
        diameters ± their standard deviation (Paper IV eqs. 17–18);
  w   = ring width (mean per-ray FWHM ± std);
  eta = orientation angle, east of north (circular mean ± circular std);
  A   = asymmetry (mean first-angular-mode amplitude ± std).

Unlike bin/measure_ring.py (our own estimator, kept for comparison),
this uses the EHT's published implementation unmodified. Requires
scipy < 1.14 (REx uses the legacy scipy.interpolate.interp2d). We call
rex.FindProfile directly because rex.FindProfileSingle in ehtim 1.3.2
references an undefined variable (`im` vs `im_raw`) and cannot run.

Usage: measure_ring_rex.py [--csv out.csv] <image.fits> [more.fits ...]
"""

import contextlib
import importlib.metadata
import io
import os
import sys

import numpy as np

with contextlib.redirect_stdout(io.StringIO()):
    import ehtim as eh
    import ehtim.features.rex as rex

TOL_LO, TOL_HI = 37.8, 46.2  # SPEC.md V2: 42 uas +- 10%


def measure(path):
    """Run REx on one FITS image; return a dict of ring parameters."""
    im = eh.image.load_fits(path)
    with contextlib.redirect_stdout(io.StringIO()):
        pp = rex.FindProfile(im)
    return {
        "image": os.path.splitext(os.path.basename(path))[0],
        "d": pp.RingSize1[0], "d_sigma": pp.RingSize1[1],
        "d_meanprof": pp.RingSize2[0],
        "w": pp.RingWidth[0], "w_sigma": pp.RingWidth[1],
        "eta_deg": np.degrees(pp.RingAngle1[0]) % 360.0,
        "eta_sigma_deg": np.degrees(pp.RingAngle1[1]),
        "asym": pp.RingAsym1[0], "asym_sigma": pp.RingAsym1[1],
    }


def main():
    argv = sys.argv[1:]
    csv_path = None
    if argv and argv[0] == "--csv":
        csv_path, argv = argv[1], argv[2:]
    if not argv:
        print(__doc__)
        sys.exit(2)

    version = importlib.metadata.version("ehtim")
    print(f"REx (ehtim {version})  tolerance {TOL_LO}-{TOL_HI} uas")
    print(f"{'image':16s} {'d(uas)':>7s} {'+-':>4s} {'w(uas)':>7s} {'+-':>4s} "
          f"{'eta(deg)':>8s} {'+-':>5s} {'asym':>5s}")
    rows = []
    for path in argv:
        r = measure(path)
        rows.append(r)
        ok = "OK" if TOL_LO <= r["d"] <= TOL_HI else "OUT"
        print(f"{r['image']:16s} {r['d']:7.1f} {r['d_sigma']:4.1f} "
              f"{r['w']:7.1f} {r['w_sigma']:4.1f} "
              f"{r['eta_deg']:8.1f} {r['eta_sigma_deg']:5.1f} "
              f"{r['asym']:5.2f}  {ok}")

    ds = np.array([r["d"] for r in rows])
    n_ok = int(np.sum((ds >= TOL_LO) & (ds <= TOL_HI)))
    print(f"\nmeasured {len(ds)}/{len(ds)}  mean {ds.mean():.1f}  "
          f"median {np.median(ds):.1f}  in-tolerance {n_ok}/{len(ds)}")

    if csv_path:
        cols = list(rows[0].keys())
        with open(csv_path, "w") as f:
            f.write("# REx (ehtim " + version + "), fiducial defaults\n")
            f.write(",".join(cols) + "\n")
            for r in rows:
                f.write(",".join(
                    r[c] if isinstance(r[c], str) else f"{r[c]:.3f}"
                    for c in cols) + "\n")
        print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
