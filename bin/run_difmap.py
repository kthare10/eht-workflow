#!/usr/bin/env python3

"""Run the EHT DIFMAP CLEAN imaging pipeline on one uvfits file.

Drives Caltech DIFMAP through `expect` (DIFMAP is interactive) using the
EHT's fiducial calling sequence:

    @EHT_Difmap <basename>,CircMask_r30_x-0.002_y0.022,-10,0.5,0.1,2,-1

The EHT_Difmap script writes `<base>.<mask>.RT-10.CF0.5.ALMA0.1.UVW2_-1.noresiduals.fits`
(restored CLEAN map) and a matching `.stat` file; this wrapper renames them
to the declared Pegasus output names.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys

FIDUCIAL_PARAMS = "-10,0.5,0.1,2,-1"

EXPECT_TEMPLATE = """set timeout -1
spawn difmap
expect "*0>"
send -- "@{script} {basename},{mask},{params}\\r"
expect "*0>"
send -- "exit\\r"
expect "*quit without saving: "
send -- "\\r"
expect eof
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input uvfits file")
    parser.add_argument("--script", default="EHT_Difmap", help="DIFMAP script name")
    parser.add_argument("--mask", default="CircMask_r30_x-0.002_y0.022.win",
                        help="Cleaning-window mask file")
    parser.add_argument("--output", required=True, help="Output FITS image")
    parser.add_argument("--stats-output", required=True,
                        help="Output DIFMAP .stat summary file")
    args = parser.parse_args()

    basename = args.input[:-len(".uvfits")] if args.input.endswith(".uvfits") else args.input
    mask = args.mask[:-len(".win")] if args.mask.endswith(".win") else args.mask

    expect_script = EXPECT_TEMPLATE.format(
        script=args.script, basename=basename, mask=mask, params=FIDUCIAL_PARAMS
    )
    print(f"Running: @{args.script} {basename},{mask},{FIDUCIAL_PARAMS}")
    result = subprocess.run(["expect"], input=expect_script, text=True)
    if result.returncode != 0:
        print(f"ERROR: difmap/expect exited with {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    produced = glob.glob(f"{basename}.{mask}.*noresiduals.fits")
    if not produced:
        print("ERROR: no DIFMAP output FITS found; directory contents:",
              file=sys.stderr)
        print("\n".join(sorted(os.listdir("."))), file=sys.stderr)
        sys.exit(1)
    shutil.move(produced[0], args.output)

    stats = glob.glob(f"{basename}.{mask}.*.stat")
    if stats:
        shutil.move(stats[0], args.stats_output)
    else:
        print("WARNING: no .stat file produced", file=sys.stderr)
        open(args.stats_output, "w").close()

    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
