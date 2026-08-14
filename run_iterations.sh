#!/bin/bash
# Run the workflow N times sequentially (default 5), archiving each run's
# staged output to output_iterK/ so successive runs don't clobber each
# other. Records the Pegasus run directory and SHA-256 checksums per
# iteration. Usage: ./run_iterations.sh [N]
set -e
cd "$(dirname "$0")"
N=${1:-5}
SCRATCH_BASE="$PWD/scratch/cc/pegasus/eht-m87"

# Stale scratch from old test runs holds ~1 GB of container copies each;
# clear it up front so 5 fresh iterations fit on disk (approved 2026-08-13).
for old in "$SCRATCH_BASE"/run000[1-8]; do
    [ -d "$old" ] && { echo "removing stale scratch: $old"; rm -rf "$old"; }
done

for i in $(seq 1 "$N"); do
    echo "=== Iteration $i/$N: planning + submitting ==="
    rm -rf output && mkdir -p output
    plan_log=$(mktemp)
    pegasus-plan --submit -s condorpool -o local workflow.yml | tee "$plan_log"
    rundir=$(grep -oE '/home/[^ ]*/eht-m87/run[0-9]+' "$plan_log" | head -1)
    rm -f "$plan_log"
    if [ -z "$rundir" ]; then
        echo "iteration $i: could not determine run dir from pegasus-plan output"
        exit 1
    fi
    echo "iteration $i run dir: $rundir"

    # wait for DAGMan to finish (up to 60 min)
    status=""
    for t in $(seq 1 360); do
        line=$(grep -hoE "EXITING WITH STATUS [0-9]+" "$rundir"/*.dag.dagman.out 2>/dev/null | tail -1)
        if [ -n "$line" ]; then
            status=${line##* }
            break
        fi
        sleep 10
    done
    if [ "$status" != "0" ]; then
        echo "iteration $i FAILED (dagman status: ${status:-timeout}) — see $rundir"
        pegasus-analyzer "$rundir" || true
        exit 1
    fi

    iter_dir="output_iter$i"
    rm -rf "$iter_dir"
    cp -r output "$iter_dir"
    { basename "$rundir"; echo "$rundir"; } > "$iter_dir/RUNDIR.txt"
    grep -h "wf_uuid" "$rundir/braindump.yml" >> "$iter_dir/RUNDIR.txt" 2>/dev/null || true
    (cd "$iter_dir" && sha256sum ./* > SHA256SUMS.txt 2>/dev/null || true)
    # this run's scratch (staged containers + intermediates) is no longer
    # needed once outputs are archived; free it for the next iteration
    run_scratch="$SCRATCH_BASE/$(basename "$rundir")"
    [ -d "$run_scratch" ] && rm -rf "$run_scratch"
    echo "=== Iteration $i complete -> $iter_dir (run: $(basename "$rundir")) ==="
done
echo "ALL $N ITERATIONS COMPLETE"
