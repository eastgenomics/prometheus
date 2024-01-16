"""
Contains utility functions used in multiple modules
"""

import time
import re
from datetime import datetime
import json
import glob
import os
import dxpy
from dxpy.bindings.dxproject import DXProject
import pandas as pd
from dxpy.bindings.dxfile_functions import list_subfolders
from dxpy.bindings.dxanalysis import DXAnalysis


def check_analyses_finished(id_list, timer, max_wait_time):
    """checks if analyses have finished or until max time has elapsed

    Args:
        id_list (str): DNAnexus analysis IDs to check if completed
        timer (int): interval to check in (minutes)
        max_wait_time (int): max wait time (minutes)
    """
    analysis_list = []

    # check that all jobs exist
    for analysis_id in id_list:
        try:
            analysis_list.append(DXAnalysis(analysis_id))
        except dxpy.exceptions.DXError:
            raise IOError(f"DNAnexus analysis {analysis_id} not found")

    time_elapsed = 0

    # check for job to complete until max wait time is reached
    while time_elapsed < max_wait_time:
        analyses_completed = 0
        for analysis in analysis_list:
            # check if job is done
            analysis_state = analysis.describe()["state"]
            if analysis_state == "done":
                analyses_completed += 1
            else:
                break

        if analyses_completed >= len(analysis_list):
            break
        else:
            # wait for [timer] minutes
            time.sleep(timer*60)
            time_elapsed += timer

    # fail if analyses took too long to finish
    if time_elapsed >= max_wait_time:
        raise Exception("Analysis took longer than max wait time of"
                        f" {max_wait_time} minutes to complete")


def check_jobs_finished(job_id_list, timer, max_wait_time):
    """checks if jobs have finished or until max time has elapsed

    Args:
        job_id_list (str): DNAnexus job IDs to check if completed
        timer (int): interval to check in (minutes)
        max_wait_time (int): max wait time (minutes)
    """
    job_list = []

    # check that all jobs exist
    for job_id in job_id_list:
        try:
            job_list.append(dxpy.bindings.dxjob.DXJob(job_id))
        except dxpy.exceptions.DXError:
            raise IOError(f"DNAnexus job {job_id} not found")

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

    # fail if jobs took too long to finish
    if time_elapsed >= max_wait_time:
        raise Exception("Jobs took longer than max wait time of"
                        f" {max_wait_time} minutes to complete")


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
        raise Exception(f"Project {project_id} does not exist")

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
        raise Exception(f"Folder {ref_proj_folder} does not exist"
                        f" in project {ref_proj_id}")
    name_regex = f"clinvar_*_{genome_build}.vcf.gz"
    vcf_files = list(dxpy.find_data_objects(
            name=name_regex,
            name_mode='glob',
            project=ref_proj_id,
            folder=ref_proj_folder
        ))

    # Error handling if files are not found in 001 reference
    if not vcf_files:
        raise Exception(f"No clinvar files matching {name_regex} "
                        "were found in 001 reference project")

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
                            f"/annotation/{genome_build}/clinvar", "clinvar_"
                            f"{recent_version}_{genome_build}.vcf.gz.tbi")

    # return latest production version
    return recent_version, vcf_id, index_id


def get_prod_vep_config(ref_proj_id, ref_proj_folder, assay):
    """gets information on latest production ClinVar file

    Args:
        ref_proj_id (str): DNAnexus project ID for 001 reference project
        ref_proj_folder (str): folder path containing vep config files
        assay (str): name of assay of vep config (e.g., TWE, TSO500)

    Raises:
        Exception: no vep config files could be found in ref project folder
        Exception: project folder does not exist

    Returns:
        id: str
            DNAnexus file ID of vep config file
    """
    if not check_proj_folder_exists(ref_proj_id, ref_proj_folder):
        raise Exception(f"Folder {ref_proj_folder} does not exist"
                        f" in project {ref_proj_id}")
    assay = assay.lower()
    name_regex = f"{assay}_vep_config_v*.json"
    config_files = list(dxpy.find_data_objects(
            name=name_regex,
            name_mode='glob',
            project=ref_proj_id,
            folder=ref_proj_folder,
            describe={
                "fields": {
                    "id": True,
                    "name": True,
                    "created": True,
                    "archivalState": True
                }
            }
        ))

    # Error handling if files are not found in 001 reference
    if not config_files:
        raise Exception(f"No vep config files matching {name_regex}"
                        " were found in 001 reference project")

    # return the most recent file uploaded found
    if len(config_files) == 1:
        return config_files[0]["id"]
    else:
        latest = config_files[0]
        for file in config_files:
            if file["describe"]["created"] > latest["describe"]["created"]:
                latest = file
        return latest["id"]


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
                name_mode="glob",
                project=project_id,
                describe={
                    "fields": {
                        "id": True,
                        "name": True,
                        "created": True,
                        "archivalState": True
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
                    "fields": {
                        "id": True,
                        "name": True,
                        "created": True,
                        "archivalState": True
                    }
                }
            ))
    if len(file_list) < 1:
        raise IOError(f"DNAnexus file {file_name} does not exist in project"
                      f" {project_id} folder {folder_path}")

    # return the most recent file uploaded found
    if len(file_list) == 1:
        return file_list[0]["id"]
    else:
        latest = file_list[0]
        for file in file_list:
            if file["describe"]["created"] > latest["describe"]["created"]:
                latest = file
        return latest["id"]


def find_all_dx_files(project_id, folder_path, file_name):
    """gets file ID of DNAnexus file from file name

    Args:
        project_id (str): DNAnexus project ID to search in
        folder_path (str): DNAnexus folder path to search in
        file_name (str): DNAnexus file name to search for

    Raises:
        IOError: DNAnexus file does not exist

    Returns:
        list (str): DNAnexus file IDs
    """
    if folder_path == "":
        file_list = list(dxpy.find_data_objects(
                name=file_name,
                name_mode="glob",
                project=project_id,
                describe={
                    "fields": {
                        "id": True,
                        "name": True,
                        "created": True,
                        "archivalState": True
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
                    "fields": {
                        "id": True,
                        "name": True,
                        "created": True,
                        "archivalState": True
                    }
                }
            ))
    if len(file_list) < 1:
        raise IOError(f"DNAnexus file {file_name} does not exist in project"
                      f" {project_id} folder {folder_path}")

    # return the most recent file uploaded found
    file_ids = []
    for file in file_list:
        file_ids.append(file["id"])

    return file_ids


def load_config(bin_path, config_path):
    """loads config file

    Returns:
        ref_proj_id: str
            DNAnexus project ID for 001 reference project
        dev_proj_id: str
            DNAnexus project ID for 003 development project
        slack_channel: str
            Slack API token
    """
    with open(config_path, "r", encoding="utf8") as json_file:
        config = json.load(json_file)

    ref_proj_id = config.get('001_REFERENCE_PROJ_ID')
    dev_proj_id = config.get('003_DEV_CLINVAR_UPDATE_PROJ_ID')
    slack_channel = config.get('SLACK_CHANNEL')

    return ref_proj_id, dev_proj_id, slack_channel


def load_config_repo(assay, bin_path, config_path):
    """loads config file for VEP config update

    Returns:
        repo: str
            URL to github repo for assay config file
    """
    with open(config_path, "r", encoding="utf8") as json_file:
        config = json.load(json_file)

    if assay == "TSO500":
        repo = config.get('TSO500_CONFIG_REPO')
    elif assay == "TWE":
        repo = config.get('TWE_CONFIG_REPO')
    elif assay == "CEN":
        repo = config.get('CEN_CONFIG_REPO')

    return repo


def update_json(json_path_glob, first_match, replace_regex, replace_with):
    """updates json file by replacing specific string from regex

    Args:
        json_path_glob (str): glob path to json
        first_match (str): first regex to match before replace pattern
        replace_regex (str): regex pattern to replace
        replace_with (str): string to replace the replace regex

    Raises:
        Exception: first match regex has not match
        Exception: replace regex has no match
    """
    old_config_filename = glob.glob(json_path_glob)[0]
    new_lines = []
    with open(old_config_filename, "r") as f:
        match_found = False
        regex_found = False
        for line in f:
            if not match_found:
                # find first match regex
                new_lines.append(line)
                if re.search(first_match, line):
                    match_found = True
            else:
                match = re.search(replace_regex, line)
                if match and not regex_found:
                    regex_found = True
                    replace_string = match[1]
                    modified = re.sub(replace_string, replace_with, line)
                    new_lines.append(modified)
                else:
                    new_lines.append(line)
    if not match_found:
        raise Exception(f"Regex {first_match} had no match"
                        f" in file {old_config_filename}")
    elif not regex_found:
        raise Exception(f"Regex {replace_regex} had no match"
                        f" in file {old_config_filename}")
    os.remove(old_config_filename)
    with open(old_config_filename, "w") as f:
        f.writelines(new_lines)


def is_json_content_different(json_path_glob, first_match,
                              file_id_regex, new_file_id):
    """checks if specific file ID in json is different to ID provided

    Args:
        json_path_glob (str): glob path to json
        first_match (str): regex match before file ID regex
        file_id_regex (str): regex for json file ID
        new_file_id (str): new file ID to be compared against

    Raises:
        Exception: first match regex has no match
        Exception: file ID regex has no match

    Returns:
        _type_: _description_
    """
    config_filename = glob.glob(json_path_glob)[0]
    with open(config_filename, "r") as f:
        match_found = False
        regex_found = False
        for line in f:
            if not match_found:
                # find first match regex
                if re.search(first_match, line):
                    match_found = True
            else:
                match = re.search(file_id_regex, line)
                if match:
                    regex_found = True
                    # get file ID portion of match in parentheses
                    file_id = match[1]
                    if file_id == new_file_id:
                        return False
                    else:
                        return True
    if not match_found:
        raise Exception(f"Regex {first_match} had no match"
                        f" in file {config_filename}")
    elif not regex_found:
        raise Exception(f"Regex {file_id_regex} had no match"
                        f" in file {config_filename}")


def search_json(json_path_glob, first_match,
                search_regex):
    """attempts to find string matching regex in json

    Args:
        json_path_glob (str): glob path to json
        first_match (str): regex to match before search regex
        search_regex (str): regex to search for

    Raises:
        Exception: first match regex not found
        Exception: search regex not found

    Returns:
        str: string matching search regex
    """
    config_filename = glob.glob(json_path_glob)[0]
    with open(config_filename, "r") as f:
        match_found = False
        regex_found = False
        for line in f:
            if not match_found:
                # find first match regex
                if re.search(first_match, line):
                    match_found = True
            else:
                match = re.search(search_regex, line)
                if match:
                    regex_found = True
                    # get portion of match in parentheses
                    return match[1]
    if not match_found:
        raise Exception(f"Regex {first_match} had no match"
                        f" in file {config_filename}")
    elif not regex_found:
        raise Exception(f"Regex {search_regex} had no match"
                        f" in file {config_filename}")


def increment_version(version):
    """increments version number by 1

    Args:
        version (str): version to increment

    Raises:
        Exception: version has invalid format

    Returns:
        str: incremented version
    """
    # string format: x.y.z
    regex = r"([0-9]+)\.([0-9]+)\.([0-9]+)"
    matched = re.search(regex, version)
    if not matched:
        raise Exception(f"Version {version} has invalid format."
                        " Format must be x.y.z where x y and z are integers")
    new_version_end = int(matched[3]) + 1
    return_version = f"{matched[1]}.{matched[2]}.{new_version_end}"
    return return_version


def get_recent_002_projects(assay, months):
    """get 002 projects matching assay name in past n months

    Args:
        assay (str): name of assay to check
        months (int): number of months ago to check from

    Raises:
        Exception: No projects found for assay in past n months

    Returns:
        pandas.DataFrame: projects found, cols id, name, created
    """
    assay_response = list(dxpy.find_projects(
            name=f"002*{assay}",
            name_mode="glob",
            describe={
                'fields': {
                    'id': True,
                    'name': True,
                    "created": True
                }
            },
            created_after=f"-{months}M",
        ))
    if len(assay_response) < 1:
        raise Exception(f"No 002 projects found for assay {assay}"
                        f" in past {months} months")

    assay_info = [[]]
    for entry in assay_response:
        info = [entry["describe"]["id"],
                entry["describe"]["name"],
                entry["describe"]["created"]]
        assay_info.append(info)

    # get most recent 002 in search and return project id
    df = pd.DataFrame.from_records(data=assay_info,
                                   columns=["id",
                                            "name",
                                            "created"])
    # sort by date
    df = df.sort_values(["created"], ascending=[False])

    return df


def find_file_name_from_id(file_id):
    """returns file name from DNAnexus file ID

    Args:
        file_id (str): DNAnexus file ID

    Returns:
        name (str): name of DNAnexus file
    """
    file = dxpy.bindings.dxfile.DXFile(file_id)
    name = file.describe()["name"]
    return name


def match_folder_name(project_id, base_path, folder_regex):
    """finds path to folder in project from folder name regex

    Args:
        project_id (str): DNAnexus project ID
        base_path (str): path to folder
        folder_regex (str): regex of folder name

    Raises:
        Exception: base path not found in project
        Exception: folder matching regex not found

    Returns:
        _type_: _description_
    """
    if not check_proj_folder_exists(project_id, base_path):
        raise Exception(f"Folder {base_path} does not exist"
                        f" in project {project_id}")

    folders = list_subfolders(project=project_id,
                              path=base_path,
                              recurse=False)
    match_regex = re.compile(folder_regex)
    for folder in folders:
        if match_regex.search(folder):
            return folder
    raise Exception(f"No folder matched the regex {folder_regex} "
                    f"in path {base_path} of project {project_id}")


def search_for_regex(log_file, regex):
    """returns all lines containing regex in text file

    Args:
        log_file (str): path to log file
        regex (str): regex to search for

    Returns:
        list (str): all lines in file containing regex
    """
    regex = re.compile(regex)
    results = []
    with open(log_file) as f:
        for line in f:
            result = regex.search(line)
            if result:
                results.append(line)
    return results
