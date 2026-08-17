#!/bin/bash
# Manual smoke test: run the pipeline steps for one day (April 11 = 101)
# without Pegasus. Run inside the ehtim container:
#   apptainer exec --bind "$PWD":/work --pwd /work \
#       Apptainer/eht-ehtim.sif ./run_manual.sh
# (build it first: apptainer build Apptainer/eht-ehtim.sif Apptainer/eht-ehtim.def)
set -e

WORK=manual_test
mkdir -p $WORK
cp eht-pipelines/eht-imaging_pipeline.py data/checksums.txt $WORK/
cd $WORK

echo "=== Step 1: Fetch + verify data ==="
python ../bin/fetch_data.py \
    --expected-checksums checksums.txt \
    --manifest checksums_manifest.txt \
    --uvfits SR1_M87_2017_101_lo_hops_netcal_StokesI.uvfits \
             SR1_M87_2017_101_hi_hops_netcal_StokesI.uvfits

echo "=== Step 2: eht-imaging reconstruction ==="
python ../bin/run_ehtim.py \
    --input-lo SR1_M87_2017_101_lo_hops_netcal_StokesI.uvfits \
    --input-hi SR1_M87_2017_101_hi_hops_netcal_StokesI.uvfits \
    --pipeline-script eht-imaging_pipeline.py \
    --output ehtim_101.fits

echo "=== Step 3: Render panel ==="
python ../bin/render_images.py \
    --image ehtim=ehtim_101.fits \
    --date April_11 \
    --output m87_101_panel.png

echo "=== Step 4: Closure statistics ==="
python ../bin/compute_stats.py \
    --obs-lo SR1_M87_2017_101_lo_hops_netcal_StokesI.uvfits \
    --obs-hi SR1_M87_2017_101_hi_hops_netcal_StokesI.uvfits \
    --image ehtim=ehtim_101.fits \
    --day 101 --date April_11 \
    --output stats_101.json

echo "=== Step 5: Aggregate ==="
python ../bin/aggregate_results.py \
    -i stats_101.json \
    --csv-output stats_summary.csv \
    --report-output summary_report.md

echo "=== Complete! ==="
ls -la
