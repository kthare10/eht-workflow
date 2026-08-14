#!/usr/bin/env python3

"""Render the per-day reconstructed M87 images into a single PNG panel.

Accepts labeled FITS images from any subset of the three pipelines and lays
them out side by side with a common angular scale bar. Rendering choices
(colormap, layout) are ours; validation is on morphology, not styling
(SPEC.md N2).
"""

import argparse
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RAD2UAS = 180.0 / np.pi * 3600 * 1e6


def load_image(path):
    """Return (array, fov_uas). Prefer ehtim's loader (handles all three
    pipelines' FITS conventions), fall back to plain astropy."""
    try:
        import ehtim as eh
        im = eh.image.load_fits(path)
        arr = im.imvec.reshape(im.ydim, im.xdim)
        fov = im.psize * im.xdim * RAD2UAS
        return arr, fov
    except Exception as e:  # noqa: BLE001
        print(f"ehtim loader failed for {path} ({e}); trying astropy", file=sys.stderr)
        from astropy.io import fits
        with fits.open(path) as hdul:
            arr = np.squeeze(hdul[0].data)
            cdelt = abs(hdul[0].header.get("CDELT1", 0)) * 3600 * 1e6  # deg -> uas
            fov = cdelt * arr.shape[-1] if cdelt else None
        return arr, fov


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", action="append", required=True,
                        metavar="LABEL=FITS", help="Labeled input image (repeatable)")
    parser.add_argument("--date", required=True,
                        help="Observation date, underscored (e.g. April_5)")
    parser.add_argument("--display-fov", type=float, default=132.0,
                        help="Displayed field of view in uas (crops wide-FOV "
                             "images like DIFMAP for comparable panels; "
                             "display-only, matches Paper IV Figure 11 style)")
    parser.add_argument("--output", required=True, help="Output PNG")
    args = parser.parse_args()

    title = f"M87 {args.date.replace('_', ' ')}, 2017"

    entries = []
    for spec in args.image:
        label, _, path = spec.partition("=")
        if not path:
            print(f"ERROR: bad --image spec '{spec}', expected LABEL=FITS", file=sys.stderr)
            sys.exit(2)
        try:
            arr, fov = load_image(path)
            entries.append((label, arr, fov))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: could not load {path}: {e}", file=sys.stderr)

    if not entries:
        print("ERROR: no images could be loaded", file=sys.stderr)
        sys.exit(1)

    n = len(entries)
    fig, axes = plt.subplots(1, n, figsize=(3.2 * n, 3.6))
    if n == 1:
        axes = [axes]
    for ax, (label, arr, fov) in zip(axes, entries):
        extent = [fov / 2, -fov / 2, -fov / 2, fov / 2] if fov else None
        ax.imshow(arr, cmap="afmhot", origin="lower", extent=extent)
        if fov and fov > args.display_fov:
            half = args.display_fov / 2
            ax.set_xlim(half, -half)
            ax.set_ylim(-half, half)
        ax.set_title(label, fontsize=10)
        if fov:
            ax.set_xlabel("relative RA (μas)", fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("relative Dec (μas)", fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(args.output, dpi=150)
    print(f"Output: {args.output} ({n} images)")


if __name__ == "__main__":
    main()
