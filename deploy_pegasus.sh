#!/bin/bash
# Convert the locally built docker images to .sif files and submit the
# workflow. For submit hosts without a Docker Hub login.
set -e

cd "$(dirname "$0")"
mkdir -p containers

for name in ehtim difmap smili rex; do
    if [ ! -f "containers/eht-${name}.sif" ]; then
        echo "=== Converting kthare10/eht-${name}:latest -> containers/eht-${name}.sif ==="
        singularity build --force "containers/eht-${name}.sif" \
            "docker-daemon://kthare10/eht-${name}:latest"
    fi
done

echo "=== Generating workflow ==="
python3 workflow_generator.py \
    --sif-dir "$PWD/containers" \
    --smili-nproc 2 \
    --output workflow.yml "$@"

echo "=== Planning and submitting ==="
pegasus-plan --submit -s condorpool -o local workflow.yml
