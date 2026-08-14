#!/usr/bin/env python3

"""Measure ring diameters of reconstructed M87 images (validation V2/V3).

REx-style image-domain feature extraction (cf. EHT Paper IV §9): the image
is lightly blurred, the ring center is grid-searched (±12 μas around the
brightness centroid) to minimize the relative dispersion of per-sector
peak radii within a constrained annulus (8–35 μas), and the diameter is
2 × median sector peak radius. Reported uncertainty is 2 × the sector
radius dispersion.

This is our own estimator, not the EHT's REx implementation. The center
search can lock onto a spurious small inner arc when the central
depression is weak (an ambiguous minimum), so every image is measured
with three annulus inner radii (8, 10, 12 μas) — a genuine ring
measurement must not depend on the annulus choice:

- all three agree (within AMBIG_TOL): STABLE, median reported;
- exactly two agree: the agreeing pair's median is reported, annotated
  "borderline" with the dissenting value shown;
- no two agree: AMBIGUOUS — no diameter is reported, so an unstable fit
  can never yield a confident wrong number.

Usage: measure_ring.py <image.fits> [more.fits ...]
"""

import sys

import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter

TOL_LO, TOL_HI = 37.8, 46.2  # SPEC.md V2: 42 uas +- 10%
RMINS = (8.0, 10.0, 12.0)    # annulus inner radii; diameter must not depend on this
RMAX = 35.0
AMBIG_TOL = 4.0              # max spread within an agreeing annulus cluster
BLUR_UAS = 5.0
NSEC = 24


def load(path):
    with fits.open(path) as h:
        arr = np.squeeze(h[0].data).astype(float)
        cd = abs(h[0].header.get("CDELT1", 0)) * 3.6e9  # deg -> uas
    return arr, cd


def _extract(sm, cd, cy0, cx0, rmin):
    ny, nx = sm.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    best = None
    span, step = int(round(12.0 / cd)), max(1, int(round(1.0 / cd)))
    for dy in range(-span, span + 1, step):
        for dx in range(-span, span + 1, step):
            cy, cx = cy0 + dy, cx0 + dx
            r = np.hypot(yy - cy, xx - cx) * cd
            t = np.arctan2(yy - cy, xx - cx)
            radii = []
            for s in range(NSEC):
                lo = -np.pi + s * 2 * np.pi / NSEC
                m = (t >= lo) & (t < lo + 2 * np.pi / NSEC) & (r >= rmin) & (r < RMAX)
                if not m.any():
                    continue
                radii.append(r[m][np.argmax(sm[m])])
            radii = np.array(radii)
            if len(radii) < NSEC - 4:
                continue
            score = radii.std() / radii.mean()
            if best is None or score < best[0]:
                best = (score, radii)
    radii = best[1]
    return 2 * np.median(radii), 2 * radii.std()


def measure(path):
    """Return (status, diameter, uncertainty, all_diameters).

    status: 'stable' | 'borderline' | 'ambiguous'. diameter/uncertainty
    are None when ambiguous.
    """
    arr, cd = load(path)
    sm = gaussian_filter(arr, BLUR_UAS / cd / 2.355)
    yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
    tot = sm.sum()
    cy0, cx0 = (sm * yy).sum() / tot, (sm * xx).sum() / tot
    results = [_extract(sm, cd, cy0, cx0, rmin) for rmin in RMINS]
    ds = [d for d, _ in results]
    if max(ds) - min(ds) <= AMBIG_TOL:
        i = np.argsort(ds)[1]
        return "stable", results[i][0], results[i][1], ds
    # look for an agreeing majority (pair, or a chain through the middle)
    pairs = [(i, j) for i in range(3) for j in range(i + 1, 3)
             if abs(ds[i] - ds[j]) <= AMBIG_TOL]
    if len(pairs) == 2:
        # chain: the shared index agrees with both neighbors
        shared = set(pairs[0]) & set(pairs[1])
        k = shared.pop()
        return "borderline", results[k][0], results[k][1], ds
    if len(pairs) == 1:
        i, j = pairs[0]
        k = i if results[i][1] <= results[j][1] else j  # lower sector spread
        return "borderline", results[k][0], results[k][1], ds
    return "ambiguous", None, None, ds


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    vals, n_ambig = [], 0
    print(f"{'image':30s} {'diam(uas)':>9s} {'+-':>5s}  tolerance {TOL_LO}-{TOL_HI}")
    for path in sys.argv[1:]:
        status, d, sd, ds = measure(path)
        dstr = "/".join(f"{x:.1f}" for x in ds)
        if status == "ambiguous":
            n_ambig += 1
            print(f"{path.split('/')[-1]:30s} {'—':>9s} {'—':>5s}  AMBIGUOUS "
                  f"(annulus-dependent: {dstr})")
            continue
        vals.append(d)
        ok = "OK" if TOL_LO <= d <= TOL_HI else "OUT"
        note = "" if status == "stable" else f"  borderline ({dstr})"
        print(f"{path.split('/')[-1]:30s} {d:9.1f} {sd:5.1f}  {ok}{note}")
    v = np.array(vals)
    n_ok = int(np.sum((v >= TOL_LO) & (v <= TOL_HI)))
    print(f"\nmeasurable {len(v)}/{len(sys.argv)-1} (ambiguous {n_ambig})  "
          f"mean {v.mean():.1f}  median {np.median(v):.1f}  "
          f"in-tolerance {n_ok}/{len(v)}")


if __name__ == "__main__":
    main()
