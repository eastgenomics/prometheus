"""
Handles building and running the helios reports workflow
"""

import dxpy
import subprocess
import glob
from dxpy.bindings.dxfile_functions import download_folder
from dxpy.bindings.dxfile import DXFile
from dxpy.app_builder import upload_applet
import re
import os

# local modules
import compare_annotation
from utils import check_jobs_finished
from utils import check_proj_folder_exists
from utils import find_dx_file
from utils import match_folder_name
from inspect_vep_logs import inspect_logs
from utils import get_recent_002_projects


def build_reports_workflow(source_dir, project, proj_folder):
    upload_applet(source_dir=source_dir,
                  project=project,
                  override_folder=proj_folder)


def test_reports_workflow(bin_folder, workflow_id,
                          project_id, workflow_version):
    # version must have full or partial name, i.e., v1.3.3 or 1.3.3
    workflow_version = workflow_version.lower()
    version_regex = r"v([0-9]+)\.([0-9]+)\.([0-9]+)"
    ver_match = re.search(version_regex, workflow_version)
    if not ver_match:
        version_regex_partial = r"([0-9]+)\.([0-9]+)\.([0-9]+)"
        par_match = re.search(version_regex_partial, workflow_version)
        if par_match:
            workflow_version = "v" + workflow_version
        else:
            raise Exception("Workflow version provided has invalid format"
                            + ". Use format vx.y.z where x y and z are ints")

    # get list of recent helios runs most to least recent
    recent_runs = get_recent_002_projects("TSO500", 12)
    # set off jobs from TSO500 run with at least 1 DNA sample
    job_IDs = []
    for run in recent_runs:
        try:
            job_IDs = launch_workflow_jobs(workflow_id,
                                           project_id,
                                           workflow_version)
            break
        except Exception:
            continue
    if len(job_IDs) < 1:
        raise Exception("No DNA samples were found in TSO500 runs"
                        + " within the past 12 months")

    # wait until each job has finished
    check_jobs_finished(job_IDs, 2, 30)
    # TODO: record that these jobs have been set off successfully
    # make text file containing job list
    # upload text file to 003 workflow update evidence folder

    # TODO: read workflow log file to confirm the new workflow name is used

    # TODO: download log file from a vep run set off by the workflow
    # TODO: check that correct version of vep config is present in log
    # TODO: check that correct version of clinvar file is present in log


def launch_workflow_jobs(workflow_id, project_id, workflow_version):
    basePath = "/output"
    folder_regex = r"TSO500-.+"
    # TODO: write utils function to find folder in folder from regex
    dateTimeFolder = match_folder_name(project_id,
                                       basePath,
                                       folder_regex)
    sampleSheetFolder = ("/output/{}/eggd_tso500/analysis_folder"
                         .format(dateTimeFolder))
    sampleSheetName = "SampleSheet.csv"
    sampleSheetID = find_dx_file(project_id,
                                 sampleSheetFolder,
                                 sampleSheetName)

    local_path = "temp/SampleSheet.csv"
    dxpy.download_dxfile(dxid=sampleSheetID,
                         filename=local_path)
    # get samples from sample sheet
    samples = get_samplesheet_samples(local_path)
    # for sample in list, determine if DNA/RNA from sample code
    regex_DNA = re.compile(r"-8471$|-8475$")
    list_DNA = []
    for sample in samples:
        if regex_DNA.search(sample):
            list_DNA.append(sample)
    # if no samples are DNA, raise exception and find next run
    if len(list_DNA) < 1:
        os.remove(local_path)
        raise Exception("Sample sheet contains 0 DNA samples")

    # process all DNA samples
    job_IDs = []
    for sample in list_DNA:
        # set off DNA sample job and record job ID
        job_ID = launch_workflow()
        job_IDs.append(job_ID)
    return job_IDs


# TODO: implement function
def get_samplesheet_samples():
    pass


def launch_workflow():
    pass
