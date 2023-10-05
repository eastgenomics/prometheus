"""
Contains utility functions used in multiple modules
"""

import time
import re
from datetime import datetime
import json

import dxpy
from dxpy.bindings.dxproject import DXProject


def check_jobs_finished(job_id_list, timer, max_wait_time):
    """checks if jobs have finished or until max time has elapsed

    Args:
        job_id_list (str): DNAnexus job IDs to check if completed
        timer (int): interval to check in (minutes)
        max_wait_time (int): max wait time
    """
    job_list = []

    # check that all jobs exist
    for job_id in job_id_list:
        try:
            job_list.append(dxpy.bindings.dxjob.DXJob(job_id))
        except dxpy.exceptions.DXError:
            raise IOError("DNAnexus job {} not found".format(job_id))

    time_elapsed = 0

    # check for job to complete until max wait time is reached
    while time_elapsed < max_wait_time:
        jobs_completed = 0
        for job in job_list:
            # check if job is done
            job_state = job.describe()["state"]
            if job_state == "done":
                jobs_completed += 1
            else:
                break

        if jobs_completed >= len(job_list):
            break
        else:
            # wait for [timer] minutes
            time.sleep(timer*60)
            time_elapsed += timer


def check_project_exists(project_id):
    """checks if a DNAnexus project exists from project ID

    Args:
        project_id (str): DNAnexus project ID

    Returns:
        bool: does the specified project exist
    """
    try:
        DXProject(project_id)
        return True
    except dxpy.exceptions.DXError:
        return False


def check_proj_folder_exists(project_id, folder_path):
    """checks if a DNAnexus folder exists in a given project

    Args:
        project_id (str): DNAnexus project ID
        folder_path (str): path to DNAnexus folder

    Raises:
        Exception: project not found

    Returns:
        bool: does folder exist in project
    """
    if not check_project_exists(project_id):
        raise Exception("Project {} does not exist".format(project_id))

    try:
        dxpy.api.project_list_folder(
            project_id,
            input_params={"folder": folder_path, "only": "folders"},
            always_retry=True
        )
        return True
    except dxpy.exceptions.ResourceNotFound:
        return False


def get_prod_version(ref_proj_id, ref_proj_folder, genome_build):
    """gets information on latest production ClinVar file

    Args:
        ref_proj_id (str): DNAnexus project ID for 001 reference project
        ref_proj_folder (str): folder path containing ClinVar files
        genome_build (str): genome build of ClinVar file

    Raises:
        Exception: no ClinVar files could be found in ref project folder
        Exception: project folder does not exist

    Returns:
        recent_version: str
            version of production Clinvar file
        vcf_id: str
            DNAnexus file ID for production vcf file
        index_id: str
            DNAnexus file ID for production vcf index file
    """
    if not check_proj_folder_exists(ref_proj_id, ref_proj_folder):
        raise Exception("Folder {} does not exist in project {}"
                        .format(ref_proj_folder, ref_proj_id))
    name_regex = "clinvar_*_{}.vcf.gz".format(genome_build)
    vcf_files = list(dxpy.find_data_objects(
            name=name_regex,
            name_mode='glob',
            project=ref_proj_id,
            folder=ref_proj_folder
        ))

    # Error handling if files are not found in 001 reference
    if not vcf_files:
        raise Exception("No clinvar files matching {} ".format(name_regex)
                        + "were found in 001 reference project")

    latest_time = datetime.strptime("20200101", '%Y%m%d').date()
    recent_version = ""
    vcf_id = ""
    index_id = ""
    version = ""

    for file in vcf_files:
        name = dxpy.describe(
                    file['id']
                )['name']
        version = re.search(r"clinvar_([0-9]{8})", name).groups()[0]
        version_date = datetime.strptime(version, '%Y%m%d').date()
        if version_date > latest_time:
            latest_time = version_date
            recent_version = version
            vcf_id = file['id']

    # get index file based on clinvar version
    index_id = find_dx_file(ref_proj_id,
                            "/annotation/b37/clinvar", "clinvar_"
                            + "{}_b37.vcf.gz.tbi".format(recent_version))

    # return latest production version
    return recent_version, vcf_id, index_id


def find_dx_file(project_id, folder_path, file_name):
    """gets file ID of DNAnexus file from file name

    Args:
        project_id (str): DNAnexus project ID to search in
        folder_path (str): DNAnexus folder path to search in
        file_name (str): DNAnexus file name to search for

    Raises:
        IOError: DNAnexus file does not exist

    Returns:
        str: DNAnexus file ID
    """
    if folder_path == "":
        file_list = list(dxpy.find_data_objects(
                name=file_name,
                name_mode='glob',
                project=project_id,
                describe={
                    'fields': {
                        'id': True,
                        'name': True,
                        "created": True,
                        'archivalState': True
                    }
                }
            ))
    else:
        file_list = list(dxpy.find_data_objects(
                name=file_name,
                name_mode='glob',
                project=project_id,
                folder=folder_path,
                describe={
                    'fields': {
                        'id': True,
                        'name': True,
                        "created": True,
                        'archivalState': True
                    }
                }
            ))
    if len(file_list) < 1:
        raise IOError("DNAnexus file "
                      + "{} does not exist in project {} folder {}"
                      .format(file_name, project_id, folder_path))

    # return the most recent file uploaded found
    if len(file_list) == 1:
        return file_list[0]["id"]
    else:
        latest = file_list[0]
        for file in file_list:
            if file["describe"]["created"] > latest["describe"]["created"]:
                latest = file
        return latest["id"]


def load_config():
    """loads config file

    Returns:
        ref_proj_id: str
            DNAnexus project ID for 001 reference project
        dev_proj_id: str
            DNAnexus project ID for 003 development project
        slack_channel: str
            Slack API token
    """
    with open("resources/config.json", "r", encoding="utf8") as json_file:
        config = json.load(json_file)

    ref_proj_id = config.get('001_REFERENCE_PROJ_ID')
    dev_proj_id = config.get('003_DEV_CLINVAR_UPDATE_PROJ_ID')
    slack_channel = config.get('SLACK_CHANNEL')

    return ref_proj_id, dev_proj_id, slack_channel


def load_config_repo(assay):
    """loads config file for VEP config update

    Returns:
        tso_config: str
            URL to github repo for TSO500 config file
        twe_config: str
            URL to github repo for TWE config file
        cen_config: str
            URL to github repo for CEN config file
    """
    with open("resources/config.json", "r", encoding="utf8") as json_file:
        config = json.load(json_file)

    if assay == "TSO500":
        repo = config.get('TSO500_CONFIG_REPO')
    elif assay == "TWE":
        repo = config.get('TWE_CONFIG_REPO')
    elif assay == "CEN":
        repo = config.get('CEN_CONFIG_REPO')

    return repo
