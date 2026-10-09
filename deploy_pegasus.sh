#!/bin/bash
# Build the four .sif images from Apptainer/*.def and submit the workflow.
#
# No Docker involved: `Bootstrap: docker` in each definition makes Apptainer pull
# and convert the OCI base images itself, and the resulting .sif files are staged
# by Pegasus like any other input file — so no Docker Hub login is needed either.
#
# Must run on a Linux host whose architecture matches the worker nodes: Apptainer
# cannot build on macOS, and a .sif has no multi-arch manifest. See
# APPTAINER.md.
set -e

cd "$(dirname "$0")"

for name in ehtim difmap smili rex; do
    if [ ! -f "Apptainer/eht-${name}.sif" ]; then
        echo "=== Building Apptainer/eht-${name}.sif from Apptainer/eht-${name}.def ==="
        # Built from the workflow root so %files sources (if any are added
        # later) resolve the same way Docker's build context did.
        apptainer build --force "Apptainer/eht-${name}.sif" \
            "Apptainer/eht-${name}.def"
    fi
done

# Execution site: condorpool (Pegasus's built-in HTCondor site) on a plain pool
# with no site catalog; set EXEC_SITE=compute and pass -s <catalog>.yml (or set
# one in ~/.pegasusrc) for a hosted site catalog.
EXEC_SITE=${EXEC_SITE:-condorpool}

echo "=== Generating workflow ==="
# --sif-dir already defaults to Apptainer/, but pass it explicitly so this
# script keeps working if that default ever changes.
python3 workflow_generator.py \
    --sif-dir "$PWD/Apptainer" \
    --smili-nproc 2 \
    -e "$EXEC_SITE" \
    --output workflow.yml "$@"

echo "=== Planning and submitting ==="
# The generator writes no site catalog; --output-dir keeps the staged
# outputs in output/ (Pegasus's default local site would use wf-output/).
pegasus-plan --dir submit -s "$EXEC_SITE" -o local --output-dir "$PWD/output" \
    --submit workflow.yml
