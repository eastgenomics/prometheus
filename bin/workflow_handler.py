"""
Handles building and running the helios reports workflow
"""

import dxpy
from dxpy.app_builder import upload_applet
import subprocess
import re
import os
import io
import pandas as pd

# local modules
from utils import check_jobs_finished
from utils import find_dx_file
from utils import match_folder_name
from utils import get_recent_002_projects
from inspect_workflow_logs import (inspect_workflow_info,
                                   inspect_vep_logs)


def build_reports_workflow(source_dir, project, proj_folder, workflow_name):
    # upload_applet(src_dir=source_dir,
    #               uploaded_resources=False,
    #               project=project,
    #               override_folder=proj_folder)

    # TODO: replace terminal call with dxpy function
    # run build via dx-toolkit
    os.chdir(source_dir)
    select_input = ["dx", "select", project]
    subprocess.run(select_input, stderr=subprocess.STDOUT)
    build_input = ["dx", "build", "--destination", proj_folder]
    subprocess.run(build_input, stderr=subprocess.STDOUT)
    # reset directory
    os.chdir("..")
    os.chdir("..")
    # get workflow ID
    filename = "{}.json".format(workflow_name)
    workflow_id = find_dx_file(project, proj_folder, filename)
    return workflow_id


def test_reports_workflow(workflow_id,
                          project_id,
                          workflow_version,
                          evidence_folder,
                          workflow_name,
                          vep_config_name,
                          clinvar_version):
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
    analysis_IDs = []
    for run in recent_runs:
        try:
            analysis_IDs = launch_workflow_jobs(workflow_id,
                                                project_id,
                                                workflow_version,
                                                workflow_name)
            break
        except Exception:
            continue
    if len(analysis_IDs) < 1:
        raise Exception("No DNA samples were found in TSO500 runs"
                        + " within the past 12 months")

    # wait until each job has finished
    check_jobs_finished(analysis_IDs, 2, 30)
    # record that these jobs have been set off successfully
    jobs_launched_path = "temp/jobs_launched.txt"
    with open(jobs_launched_path, "w") as f:
        f.writelines(analysis_IDs)
    # upload text file to 003 workflow update evidence folder
    dxpy.upload_local_file(filename=jobs_launched_path,
                           project=project_id,
                           folder=evidence_folder)

    # get workflow name to confirm the new workflow name is used
    (passed, test_results) = inspect_workflow_info(workflow_id, workflow_name)
    # upload test results to DNAnexus 003 project
    if passed:
        dxpy.upload_local_file(filename=test_results,
                               project=project_id,
                               folder=evidence_folder)
    else:
        raise Exception("Workflow did not have new name")

    # TODO: find vep run from workflow analysis
    analysis_id = analysis_IDs[0]
    analysis = dxpy.bindings.dxanalysis.DXAnalysis(analysis_id)
    job_info = analysis.describe()
    vep_run = job_info["subjob"]
    # download log file from a vep run set off by the workflow
    log = "temp/reports_workflow_vep_log.txt"
    os.system("dx watch {} > {}".format(vep_run, log))
    # check that correct version of vep config is present as input to job
    # check that correct version of clinvar file is present in log
    (passed, test_results) = inspect_vep_logs(log,
                                              vep_run,
                                              vep_config_name,
                                              clinvar_version)
    if passed:
        dxpy.upload_local_file(filename=test_results,
                               project=project_id,
                               folder=evidence_folder)
    else:
        raise Exception("Vep logs failed testing")


def launch_workflow_jobs(workflow_id, project_id, workflow_version):
    basePath = "/output"
    folder_regex = r"TSO500-.+"
    # find subfolder in folder from regex
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


def get_samplesheet_samples(filename):
    # read in sample sheet as file
    start_regex = re.compile(r"\[data\]")
    start_found = False
    csv_lines = []
    with open(filename) as sample_sheet:
        for line in sample_sheet:
            if start_found:
                csv_lines.append(line)
            elif start_regex.search(line):
                start_found = True
    sample_df = pd.read_csv(io.StringIO('\n'.join(csv_lines)))
    sample_list = sample_df["Sample_ID"].values.tolist()
    return sample_list


def launch_workflow(workflow_id,
                    project_id,
                    output_path,
                    workflow_name,
                    sample_prefix):
    workflow = dxpy.bindings.dxworkflow.DXWorkflow(workflow_id)

    bam_path = ("{}/eggd_tso500/analysis_folder/".format(output_path)
                + "Logs_Intermediates/StitchedRealigned")
    bam_regex = sample_prefix + r".*\.bam"
    bam_ID = find_dx_file(project_id, bam_path, bam_regex)

    index_regex = sample_prefix + r".*\.bai"
    index_ID = find_dx_file(project_id, bam_path, index_regex)

    name = sample_prefix

    gvcf_path = ("{}/eggd_tso500/analysis_folder/".format(output_path)
                 + "Results")
    gvcf_regex = sample_prefix + r".*\.genome\.vcf"
    gvcf_ID = find_dx_file(project_id, gvcf_path, gvcf_regex)

    input_dict = {
        "stage-GF22j384b0bpYgYB5fjkk34X.bam": {"$dnanexus_link": bam_ID},
        "stage-GF22j384b0bpYgYB5fjkk34X.index": {"$dnanexus_link": index_ID},
        "stage-GF22GJQ4b0bjFFxG4pbgFy5V.name": {"$dnanexus_link": name},
        "stage-GF25f384b0bVZkJ2P46f79xy.gvcf": {"$dnanexus_link": gvcf_ID}
    }

    destination = "{}/{}/{}".format(project_id, output_path, workflow_name)
    analysis_id = workflow.run(workflow_input=input_dict,
                               destination=destination)
    return analysis_id
