#!/usr/bin/env python3

"""
Pegasus workflow generator for the EHT M87 black hole imaging reproduction.

Clean-room reproduction of the first image of the M87* black hole using only
EHT Collaboration public releases (see SPEC.md; forbidden sources in
CLAUDE.md). The workflow:

1. Fetches the EHT calibrated uvfits release (2019-D01-01) and verifies
   SHA-256 checksums against data/checksums.txt
2. Per observation day (April 5/6/10/11 2017 = days 095/096/100/101), runs
   the three fiducial EHT imaging pipelines from 2019-D01-02:
   - DIFMAP  (CLEAN, per band: lo, hi)
   - eht-imaging (RML, lo+hi combined)
   - SMILI   (RML, per band: lo, hi)
3. Renders a per-day PNG panel of all reconstructed images
4. Computes closure chi^2 statistics (cphase, logcamp) per image vs the data
5. Aggregates everything into a CSV table and markdown report
6. Measures ring diameter/width/orientation/asymmetry of every image with
   REx (ehtim.features.rex, the EHT's own extractor) into ring_rex.csv

Usage:
    ./workflow_generator.py --output workflow.yml
    ./workflow_generator.py --days 101 --skip-smili --output workflow.yml
    ./workflow_generator.py -e condorpool        # plain HTCondor pool, no site catalog
    ./workflow_generator.py -s unity.yml         # hosted site catalog

Sites follow pegasus-isi/pegasus-gromacs: jobs run on a site named "compute",
defined by a centrally hosted site catalog (-s FILE, or one in ~/.pegasusrc).
The generator writes the workflow and catalogs but no site catalog, and never
plans or submits — it prints the pegasus-plan command.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from Pegasus.api import *

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# day-of-year tag -> (date label, day-of-April for SMILI's --day).
# Date labels are underscored so no job argument contains a space
# (space-containing argument values do not survive Condor arg handling);
# the wrapper scripts convert underscores back for display.
DAYS = {
    "095": ("April_5", 5),
    "096": ("April_6", 6),
    "100": ("April_10", 10),
    "101": ("April_11", 11),
}
BANDS = ["lo", "hi"]

DATA_URL = ("https://github.com/eventhorizontelescope/2019-D01-01/raw/master/"
            "EHTC_FirstM87Results_Apr2019_uvfits.tgz")

# Vendored EHT pipeline files (see eht-pipelines/PROVENANCE.md)
EHT_DIFMAP_SCRIPT = "EHT_Difmap"
EHT_DIFMAP_MASK = "CircMask_r30_x-0.002_y0.022.win"
EHT_EHTIM_SCRIPT = "eht-imaging_pipeline.py"
EHT_SMILI_SCRIPT = "smili_imaging_pipeline.py"

TOOL_CONFIGS = {
    "fetch_data":        {"memory": "1 GB", "cores": 1},
    "run_difmap":        {"memory": "2 GB", "cores": 1},
    "run_ehtim":         {"memory": "4 GB", "cores": 1},
    "run_smili":         {"memory": "6 GB", "cores": 2},
    "render_images":     {"memory": "2 GB", "cores": 1},
    "compute_stats":     {"memory": "4 GB", "cores": 1},
    "aggregate_results": {"memory": "1 GB", "cores": 1},
    "measure_ring_rex":  {"memory": "2 GB", "cores": 1},
}


def uvfits_name(day, band):
    return f"SR1_M87_2017_{day}_{band}_hops_netcal_StokesI.uvfits"


class EHTWorkflow:
    """EHT M87 imaging workflow generator."""

    wf = None
    sc = None
    tc = None
    rc = None
    props = None

    wf_name = "eht-m87"

    def __init__(self, dagfile="workflow.yml", days=None, skip_difmap=False,
                 skip_ehtim=False, skip_smili=False, smili_nproc=4,
                 sif_dir=None):
        self.dagfile = dagfile
        self.days = days or list(DAYS)
        self.skip_difmap = skip_difmap
        self.skip_ehtim = skip_ehtim
        self.skip_smili = skip_smili
        self.smili_nproc = smili_nproc
        self.sif_dir = sif_dir
        self.wf_dir = str(Path(__file__).parent.resolve())
        self.shared_scratch_dir = os.path.join(self.wf_dir, "scratch")
        self.local_storage_dir = os.path.join(self.wf_dir, "output")

    def write(self):
        if self.sc is not None:
            self.sc.write()
        self.props.write()
        self.rc.write()
        self.tc.write()
        self.wf.write(file=self.dagfile)

    # ------------------------------------------------------------------
    # Plan / run / monitor (thin wrappers over the Pegasus API Workflow
    # object, for interactive use e.g. from a Jupyter notebook)
    # ------------------------------------------------------------------
    def plan_submit(self, exec_site_name="compute", raise_errors=False):
        try:
            self.wf.plan(
                dir="submit",
                sites=[exec_site_name],
                output_sites=["local"],
                cleanup="none",
                verbose=1,
                submit=True,
            )
        except PegasusClientError as e:
            print(e)
            if raise_errors:
                raise

    def status(self):
        try:
            self.wf.status(long=True)
        except PegasusClientError as e:
            print(e)

    def wait(self):
        try:
            self.wf.wait()
        except PegasusClientError as e:
            print(e)

    def statistics(self):
        try:
            self.wf.statistics()
        except PegasusClientError as e:
            print(e)

    def create_pegasus_properties(self, hosted_site_catalog=None):
        self.props = Properties()
        self.props["pegasus.transfer.threads"] = "16"
        if hosted_site_catalog:
            # Use one of Pegasus' centrally hosted site catalogs instead of
            # a locally generated one. pegasus-plan downloads and caches the
            # named file from the catalog repository at plan time.
            # https://pegasus.isi.edu/documentation/reference-guide/catalogs.html#centrally-hosted-site-catalogs
            self.props["pegasus.catalog.site.repo.file"] = hosted_site_catalog

    # Not used by the CLI — pegasus-plan resolves the site catalog from a
    # centrally hosted one instead (see -s/--hosted-site-catalog). Kept for
    # notebook use, when a self-contained, locally generated HTCondor site
    # catalog is wanted.
    def create_sites_catalog(self, exec_site_name="compute"):
        self.sc = SiteCatalog()
        local = Site("local").add_directories(
            Directory(
                Directory.SHARED_SCRATCH, self.shared_scratch_dir
            ).add_file_servers(
                FileServer("file://" + self.shared_scratch_dir, Operation.ALL)
            ),
            Directory(
                Directory.LOCAL_STORAGE, self.local_storage_dir
            ).add_file_servers(
                FileServer("file://" + self.local_storage_dir, Operation.ALL)
            ),
        )
        exec_site = (
            Site(exec_site_name)
            .add_condor_profile(universe="vanilla")
            .add_pegasus_profile(style="condor")
        )
        self.sc.add_sites(local, exec_site)

    def _container(self, name):
        """Container from a local .sif (the default, built from Apptainer/
        eht-<name>.def), or from Docker Hub when --sif-dir is cleared.

        Pegasus stages the .sif like any other input file, so image_site is
        "local" — the site where the file physically lives.
        """
        if self.sif_dir:
            sif = os.path.join(self.sif_dir, f"eht-{name}.sif")
            if not os.path.exists(sif):
                print(f"Warning: Apptainer image not found at {sif} — build it "
                      f"first with: apptainer build {sif} "
                      f"Apptainer/eht-{name}.def")
            return Container(
                f"eht_{name}",
                container_type=Container.SINGULARITY,
                image="file://" + sif,
                image_site="local",
            )
        return Container(
            f"eht_{name}",
            container_type=Container.SINGULARITY,
            image=f"docker://kthare10/eht-{name}:latest",
            image_site="docker_hub",
        )

    def create_transformation_catalog(self, exec_site_name="compute"):
        self.tc = TransformationCatalog()

        difmap_container = self._container("difmap")
        ehtim_container = self._container("ehtim")
        smili_container = self._container("smili")
        rex_container = self._container("rex")
        self.tc.add_containers(difmap_container, ehtim_container,
                               smili_container, rex_container)

        tool_containers = {
            "fetch_data": ehtim_container,
            "run_difmap": difmap_container,
            "run_ehtim": ehtim_container,
            "run_smili": smili_container,
            "render_images": ehtim_container,
            "compute_stats": ehtim_container,
            "aggregate_results": ehtim_container,
            "measure_ring_rex": rex_container,
        }
        for tool, config in TOOL_CONFIGS.items():
            tx = Transformation(
                tool,
                site=exec_site_name,
                pfn=os.path.join(self.wf_dir, f"bin/{tool}.py"),
                is_stageable=True,
                container=tool_containers[tool],
            ).add_pegasus_profile(memory=config["memory"], cores=config["cores"])
            self.tc.add_transformations(tx)

    def create_replica_catalog(self):
        self.rc = ReplicaCatalog()
        pipelines_dir = os.path.join(self.wf_dir, "eht-pipelines")
        for name in (EHT_DIFMAP_SCRIPT, EHT_DIFMAP_MASK,
                     EHT_EHTIM_SCRIPT, EHT_SMILI_SCRIPT):
            self.rc.add_replica("local", name,
                                "file://" + os.path.join(pipelines_dir, name))
        self.rc.add_replica("local", "checksums.txt",
                            "file://" + os.path.join(self.wf_dir, "data/checksums.txt"))

    def create_workflow(self):
        self.wf = Workflow(self.wf_name, infer_dependencies=True)

        difmap_script = File(EHT_DIFMAP_SCRIPT)
        difmap_mask = File(EHT_DIFMAP_MASK)
        ehtim_script = File(EHT_EHTIM_SCRIPT)
        smili_script = File(EHT_SMILI_SCRIPT)
        checksums = File("checksums.txt")

        # --- Fetch: one job downloads, verifies, and extracts all uvfits ---
        uvfits = {(d, b): File(uvfits_name(d, b)) for d in self.days for b in BANDS}
        manifest = File("checksums_manifest.txt")
        fetch_job = (
            Job("fetch_data", _id="fetch_data", node_label="fetch_data")
            .add_args(
                "--url", DATA_URL,
                "--expected-checksums", checksums.lfn,
                "--manifest", manifest.lfn,
                "--uvfits", *[f.lfn for f in uvfits.values()],
            )
            .add_inputs(checksums)
            .add_outputs(*uvfits.values(), stage_out=False, register_replica=False)
            .add_outputs(manifest, stage_out=True, register_replica=False)
            .add_dagman_profile(retry="2")
        )
        self.wf.add_jobs(fetch_job)

        stats_files = []
        all_images = []
        for day in self.days:
            date, day_of_april = DAYS[day]
            lo, hi = uvfits[(day, "lo")], uvfits[(day, "hi")]
            images = {}  # label -> File

            if not self.skip_difmap:
                for band in BANDS:
                    img = File(f"difmap_{day}_{band}.fits")
                    stat = File(f"difmap_{day}_{band}.stat")
                    job = (
                        Job("run_difmap", _id=f"difmap_{day}_{band}",
                            node_label=f"difmap_{day}_{band}")
                        .add_args(
                            "--input", uvfits[(day, band)].lfn,
                            "--script", difmap_script.lfn,
                            "--mask", difmap_mask.lfn,
                            "--output", img.lfn,
                            "--stats-output", stat.lfn,
                        )
                        .add_inputs(uvfits[(day, band)], difmap_script, difmap_mask)
                        .add_outputs(img, stage_out=True, register_replica=False)
                        .add_outputs(stat, stage_out=True, register_replica=False)
                        .add_pegasus_profiles(label=f"day_{day}")
                    )
                    self.wf.add_jobs(job)
                    images[f"difmap_{band}"] = img

            if not self.skip_ehtim:
                img = File(f"ehtim_{day}.fits")
                job = (
                    Job("run_ehtim", _id=f"ehtim_{day}", node_label=f"ehtim_{day}")
                    .add_args(
                        "--input-lo", lo.lfn,
                        "--input-hi", hi.lfn,
                        "--pipeline-script", ehtim_script.lfn,
                        "--output", img.lfn,
                    )
                    .add_inputs(lo, hi, ehtim_script)
                    .add_outputs(img, stage_out=True, register_replica=False)
                    .add_pegasus_profiles(label=f"day_{day}")
                )
                self.wf.add_jobs(job)
                images["ehtim"] = img

            if not self.skip_smili:
                for band in BANDS:
                    img = File(f"smili_{day}_{band}.fits")
                    job = (
                        Job("run_smili", _id=f"smili_{day}_{band}",
                            node_label=f"smili_{day}_{band}")
                        .add_args(
                            "--input", uvfits[(day, band)].lfn,
                            "--day", str(day_of_april),
                            "--nproc", str(self.smili_nproc),
                            "--pipeline-script", smili_script.lfn,
                            "--output", img.lfn,
                        )
                        .add_inputs(uvfits[(day, band)], smili_script)
                        .add_outputs(img, stage_out=True, register_replica=False)
                        .add_pegasus_profiles(label=f"day_{day}")
                    )
                    self.wf.add_jobs(job)
                    images[f"smili_{band}"] = img

            image_args = []
            for label, f in images.items():
                image_args += ["--image", f"{label}={f.lfn}"]

            panel = File(f"m87_{day}_panel.png")
            render_job = (
                Job("render_images", _id=f"render_{day}", node_label=f"render_{day}")
                .add_args(*image_args, "--date", date, "--output", panel.lfn)
                .add_inputs(*images.values())
                .add_outputs(panel, stage_out=True, register_replica=False)
                .add_pegasus_profiles(label=f"day_{day}")
            )
            self.wf.add_jobs(render_job)

            stats = File(f"stats_{day}.json")
            stats_job = (
                Job("compute_stats", _id=f"stats_{day}", node_label=f"stats_{day}")
                .add_args(
                    "--obs-lo", lo.lfn,
                    "--obs-hi", hi.lfn,
                    *image_args,
                    "--day", day,
                    "--date", date,
                    "--output", stats.lfn,
                )
                .add_inputs(lo, hi, *images.values())
                .add_outputs(stats, stage_out=True, register_replica=False)
                .add_pegasus_profiles(label=f"day_{day}")
            )
            self.wf.add_jobs(stats_job)
            stats_files.append(stats)
            all_images.extend(images.values())

        # --- Fan-in: aggregate all per-day statistics ---
        summary_csv = File("stats_summary.csv")
        report = File("summary_report.md")
        input_args = []
        for f in stats_files:
            input_args += ["-i", f.lfn]
        aggregate_job = (
            Job("aggregate_results", _id="aggregate", node_label="aggregate")
            .add_args(*input_args,
                      "--csv-output", summary_csv.lfn,
                      "--report-output", report.lfn)
            .add_inputs(*stats_files)
            .add_outputs(summary_csv, report, stage_out=True, register_replica=False)
        )
        self.wf.add_jobs(aggregate_job)

        # --- Fan-in: REx ring measurement over every reconstructed image ---
        ring_csv = File("ring_rex.csv")
        rex_job = (
            Job("measure_ring_rex", _id="measure_ring_rex",
                node_label="measure_ring_rex")
            .add_args("--csv", ring_csv.lfn,
                      *sorted(f.lfn for f in all_images))
            .add_inputs(*all_images)
            .add_outputs(ring_csv, stage_out=True, register_replica=False)
        )
        self.wf.add_jobs(rex_job)


def main():
    parser = argparse.ArgumentParser(
        description="Generate the EHT M87 imaging Pegasus workflow")
    parser.add_argument("--days", nargs="+", choices=sorted(DAYS), default=None,
                        help="Observation days to image (default: all four)")
    parser.add_argument("--skip-difmap", action="store_true",
                        help="Skip the DIFMAP CLEAN pipeline")
    parser.add_argument("--skip-ehtim", action="store_true",
                        help="Skip the eht-imaging RML pipeline")
    parser.add_argument("--skip-smili", action="store_true",
                        help="Skip the SMILI RML pipeline")
    parser.add_argument("--smili-nproc", type=int, default=4,
                        help="Parallel processes per SMILI job")
    parser.add_argument("--sif-dir", default="Apptainer",
                        help="Directory holding the locally built "
                             "eht-{difmap,ehtim,rex,smili}.sif images, absolute "
                             "or relative to the workflow directory (default: "
                             "Apptainer). Pass --sif-dir '' to fall back to "
                             "pulling from Docker Hub instead.")
    parser.add_argument("-s", "--hosted-site-catalog", metavar="FILE",
                        default=None,
                        help="Name of a Pegasus centrally hosted site catalog "
                             "to plan against (e.g. access-pegasus.yml), "
                             "instead of a locally generated one. Sets "
                             "pegasus.catalog.site.repo.file; see "
                             "https://pegasus.isi.edu/documentation/"
                             "reference-guide/catalogs.html"
                             "#centrally-hosted-site-catalogs")
    parser.add_argument("-e", "--execution-site-name", metavar="STR",
                        default="compute",
                        help="Execution site name (default: compute). Use "
                             "condorpool on a plain HTCondor pool with no "
                             "site catalog")
    parser.add_argument("-o", "--output", default="workflow.yml",
                        help="Output workflow YAML file")
    args = parser.parse_args()

    if args.skip_difmap and args.skip_ehtim and args.skip_smili:
        print("Error: all three pipelines are skipped — nothing to do")
        sys.exit(1)

    # A relative --sif-dir resolves against the workflow directory, not the
    # caller's CWD, so the default works from anywhere.
    if args.sif_dir:
        sif_dir = args.sif_dir if os.path.isabs(args.sif_dir) else os.path.join(
            os.path.dirname(os.path.abspath(__file__)), args.sif_dir)
    else:
        sif_dir = None

    workflow = EHTWorkflow(
        dagfile=args.output,
        days=args.days,
        skip_difmap=args.skip_difmap,
        skip_ehtim=args.skip_ehtim,
        skip_smili=args.skip_smili,
        smili_nproc=args.smili_nproc,
        sif_dir=sif_dir,
    )

    checksums_path = os.path.join(workflow.wf_dir, "data/checksums.txt")
    if not os.path.exists(checksums_path):
        print(f"Error: {checksums_path} not found (required for data validation)")
        sys.exit(1)
    for name in (EHT_DIFMAP_SCRIPT, EHT_DIFMAP_MASK,
                 EHT_EHTIM_SCRIPT, EHT_SMILI_SCRIPT):
        path = os.path.join(workflow.wf_dir, "eht-pipelines", name)
        if not os.path.exists(path):
            print(f"Error: vendored EHT pipeline file missing: {path}")
            sys.exit(1)

    logger.info(f"Execution site: {args.execution_site_name}")
    logger.info("Hosted site catalog: "
                f"{args.hosted_site_catalog or '(none — supply your own site catalog)'}")

    workflow.create_pegasus_properties(
        hosted_site_catalog=args.hosted_site_catalog)
    workflow.create_transformation_catalog(args.execution_site_name)
    workflow.create_replica_catalog()
    workflow.create_workflow()
    workflow.write()
    logger.info(f"Workflow written to {args.output} "
                f"(days: {', '.join(workflow.days)})")
    # --output-dir keeps outputs in output/: the CLI writes no local site,
    # and Pegasus's default one would stage them to wf-output/ instead.
    logger.info(f"Plan and submit: pegasus-plan --dir submit "
                f"-s {args.execution_site_name} -o local "
                f"--output-dir {workflow.local_storage_dir} --submit {args.output}")


if __name__ == "__main__":
    main()
