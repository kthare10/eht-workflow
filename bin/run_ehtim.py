#!/usr/bin/env python3

"""Run the EHT eht-imaging (EHTIM) RML pipeline for one observation day.

Invokes the EHT's fiducial driver (vendored from
eventhorizontelescope/2019-D01-02) on the low- and high-band uvfits files:

    python eht-imaging_pipeline.py -i <lo>.uvfits -i2 <hi>.uvfits -o <out>.fits
"""

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-lo", required=True, help="Low-band uvfits file")
    parser.add_argument("--input-hi", required=True, help="High-band uvfits file")
    parser.add_argument("--pipeline-script", default="eht-imaging_pipeline.py",
                        help="EHT pipeline driver script (staged by Pegasus)")
    parser.add_argument("--output", required=True, help="Output FITS image")
    args = parser.parse_args()

    script = os.path.join(os.getcwd(), args.pipeline_script)
    cmd = [sys.executable, script,
           "-i", args.input_lo, "-i2", args.input_hi, "-o", args.output]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"ERROR: eht-imaging pipeline exited with {result.returncode}",
              file=sys.stderr)
        sys.exit(result.returncode)

    if not os.path.exists(args.output):
        print(f"ERROR: expected output {args.output} not produced", file=sys.stderr)
        sys.exit(1)
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
