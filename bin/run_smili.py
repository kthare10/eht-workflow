#!/usr/bin/env python3

"""Run the EHT SMILI RML pipeline on one uvfits file.

Invokes the EHT's fiducial driver (vendored from
eventhorizontelescope/2019-D01-02):

    python smili_imaging_pipeline.py -i <band>.uvfits -o <out>.fits --day <D> --nproc <N>

The EHT driver is Python-2 (per its README, "tested in Python 2.7"; e.g.
xrange at line 339), so this wrapper first makes a mechanically converted
copy with stdlib 2to3 and executes that — the vendored script itself stays
verbatim. The driver also writes <out>.precal.uvfits and
<out>.selfcal.uvfits alongside the image; those are left undeclared
(scratch only).
"""

import argparse
import os
import shutil
import subprocess
import sys


def py3_convert(script):
    """Copy the staged py2 driver and 2to3-convert the copy; return its path."""
    converted = "smili_pipeline_2to3.py"
    shutil.copy(script, converted)
    result = subprocess.run(["2to3", "-w", "-n", converted],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"WARNING: 2to3 failed ({result.stderr.strip()}); "
              f"running the driver unconverted", file=sys.stderr)
        return script
    print(f"Applied mechanical 2to3 conversion: {script} -> {converted}")
    return converted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input uvfits file")
    parser.add_argument("--day", type=int, required=True,
                        help="Observing day of April 2017 (5, 6, 10, or 11)")
    parser.add_argument("--nproc", type=int, default=1, help="Parallel processes")
    parser.add_argument("--pipeline-script", default="smili_imaging_pipeline.py",
                        help="EHT pipeline driver script (staged by Pegasus)")
    parser.add_argument("--output", required=True, help="Output FITS image")
    args = parser.parse_args()

    script = py3_convert(os.path.join(os.getcwd(), args.pipeline_script))
    cmd = [sys.executable, script,
           "-i", args.input, "-o", args.output,
           "--day", str(args.day), "--nproc", str(args.nproc)]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"ERROR: SMILI pipeline exited with {result.returncode}",
              file=sys.stderr)
        sys.exit(result.returncode)

    if not os.path.exists(args.output):
        print(f"ERROR: expected output {args.output} not produced", file=sys.stderr)
        sys.exit(1)
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
