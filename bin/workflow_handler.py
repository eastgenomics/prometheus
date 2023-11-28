"""
Handles building and running the helios reports workflow
"""

import dxpy
import re
import os
import io
import json
import pandas as pd

# local modules
from utils import (check_analyses_finished,
                   find_dx_file,
                   find_all_dx_files,
                   match_folder_name,
                   get_recent_002_projects)
from inspect_workflow_logs import (inspect_workflow_info,
                                   inspect_vep_logs)


def build_reports_workflow(source_dir, project, proj_folder, workflow_name):
    with open(source_dir) as f:
        wf_json = json.load(f)
    wf = dxpy.new_dxworkflow(**wf_json,
                             project=project,
                             folder=proj_folder)
    workflow_id = wf.get_id()

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
    analyses = []
    for index, run in recent_runs.iterrows():
        try:
            analyses = launch_workflow_jobs(workflow_id,
                                            run["id"],
                                            project_id,
                                            workflow_version,
                                            workflow_name,
                                            evidence_folder)
            break
        except IOError as ex:
            print(ex)
    if len(analyses) < 1:
        raise Exception("No DNA samples were found in TSO500 runs"
                        + " within the past 12 months")

    analysis_IDs = []
    for analysis in analyses:
        analysis_IDs.append(analysis.describe()["id"])

    # wait until each analysis has finished
    check_analyses_finished(analysis_IDs, 2, 60)
    # record that these jobs have been set off successfully
    analyses_launched_path = "temp/analyses_launched.txt"
    with open(analyses_launched_path, "w") as f:
        for id in analysis_IDs:
            f.write(id + "\n")
    # upload text file to 003 workflow update evidence folder
    dxpy.upload_local_file(filename=analyses_launched_path,
                           project=project_id,
                           folder=evidence_folder)

    # get workflow name to confirm the new workflow name is used
    analysis_id = analysis_IDs[0]
    (passed, test_results) = inspect_workflow_info(analysis_id, workflow_name)
    # upload test results to DNAnexus 003 project
    if passed:
        dxpy.upload_local_file(filename=test_results,
                               project=project_id,
                               folder=evidence_folder)
    else:
        raise Exception("Workflow did not have new name")

    # find vep run from workflow analysis
    analysis = dxpy.bindings.dxanalysis.DXAnalysis(analysis_id)
    job_info = analysis.describe()
    vep_stage_id = "stage-GF25PqQ4b0bQjvBVP4Bb5pJ0"
    stages = job_info["stages"]
    vep_run = ""
    for stage in stages:
        if stage["id"] == vep_stage_id:
            vep_run = stage["execution"]["id"]
            break
    # check vep stage has been found
    if vep_run == "":
        raise Exception("Vep stage not found for analysis {}"
                        .format(analysis_id))
    # download log file from a vep run set off by the workflow
    log = "temp/reports_workflow_vep_log.txt"
    os.system("dx watch {} > {}".format(vep_run, log))
    # check that correct version of vep config is present as input to job
    # check that correct version of clinvar file is present in log
    (passed, test_results) = inspect_vep_logs(log,
                                              vep_run,
                                              vep_config_name,
                                              clinvar_version)
    dxpy.upload_local_file(filename=test_results,
                           project=project_id,
                           folder=evidence_folder)


def launch_workflow_jobs(workflow_id,
                         run_project_id,
                         dev_project_id,
                         workflow_version,
                         workflow_name,
                         evidence_path):
    base_path = "/output"
    folder_regex = r"TSO500-.+"
    # find subfolder in folder from regex
    try:
        date_time_folder = match_folder_name(run_project_id,
                                             base_path,
                                             folder_regex)
    except Exception:
        # no output folder is present, therefore project is still
        # processing
        raise IOError("002 project {} is still processing"
                      .format(run_project_id))
    sampleSheetFolder = ("{}/eggd_tso500/analysis_folder"
                         .format(date_time_folder))
    sampleSheetName = "SampleSheet.csv"
    sampleSheetID = find_dx_file(run_project_id,
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
    input_path = date_time_folder
    output_path = evidence_path
    job_IDs = []
    for sample in list_DNA:
        # set off DNA sample job and record job ID
        job_ID = launch_workflow(workflow_id,
                                 dev_project_id,
                                 run_project_id,
                                 input_path,
                                 output_path,
                                 workflow_name,
                                 sample)
        job_IDs.append(job_ID)
    return job_IDs


def get_samplesheet_samples(filename):
    # read in sample sheet as file
    start_regex = re.compile(r"\[Data\]")
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
                    dev_project_id,
                    run_project_id,
                    input_path,
                    output_path,
                    workflow_name,
                    sample_prefix):
    workflow = dxpy.bindings.dxworkflow.DXWorkflow(workflow_id)

    bam_path = ("{}/eggd_tso500/analysis_folder/".format(input_path)
                + "Logs_Intermediates/StitchedRealigned")
    bam_regex = sample_prefix + "*.bam"
    bam_ID = find_dx_file(run_project_id, bam_path, bam_regex)

    index_regex = sample_prefix + "*.bai"
    index_ID = find_dx_file(run_project_id, bam_path, index_regex)

    name = sample_prefix

    fastq_path = ("{}/eggd_tso500/".format(input_path)
                  + "analysis_folder/Logs_Intermediates/FastqGeneration")
    fastq_regex = "{}*.fastq.gz".format(sample_prefix)
    fastq_IDs = find_all_dx_files(run_project_id, fastq_path, fastq_regex)
    if len(fastq_IDs) < 4:
        raise Exception("Fewer than 4 fastq files found in "
                        + "project {}".format(run_project_id))
    gvcf_path = ("{}/eggd_tso500/analysis_folder/".format(input_path)
                 + "Results")
    gvcf_regex = sample_prefix + "*.genome.vcf"
    gvcf_ID = find_dx_file(run_project_id, gvcf_path, gvcf_regex)

    stage_fq = "stage-GFQZjB84b0bxz4Yg1y3ygKJZ.fastqs"

    input_dict = {
        stage_fq: [{"$dnanexus_link": fastq_IDs[0]},
                   {"$dnanexus_link": fastq_IDs[1]},
                   {"$dnanexus_link": fastq_IDs[2]},
                   {"$dnanexus_link": fastq_IDs[3]}],
        "stage-GF22j384b0bpYgYB5fjkk34X.bam": {"$dnanexus_link": bam_ID},
        "stage-GF22j384b0bpYgYB5fjkk34X.index": {"$dnanexus_link": index_ID},
        "stage-GF22GJQ4b0bjFFxG4pbgFy5V.name": name,
        "stage-GF25f384b0bVZkJ2P46f79xy.gvcf": {"$dnanexus_link": gvcf_ID}
    }

    analysis_name = "{}_{}".format(workflow_name, sample_prefix)
    analysis_id = workflow.run(workflow_input=input_dict,
                               project=dev_project_id,
                               folder=output_path,
                               name=analysis_name)
    return analysis_id
