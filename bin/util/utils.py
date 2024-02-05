"""
Contains utility functions used in multiple modules
"""

import re
from datetime import datetime
import json
import glob
import os
import dxpy
from dxpy.bindings.dxproject import DXProject
import pandas as pd
from dxpy.bindings.dxfile_functions import list_subfolders
from packaging import version
from flatten_dict import flatten, unflatten


def check_project_exists(project_id) -> bool:
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


def check_proj_folder_exists(project_id, folder_path) -> bool:
    """checks if a DNAnexus folder exists in a given project

    Args:
        project_id (str): DNAnexus project ID
        folder_path (str): path to DNAnexus folder

    Raises:
        RuntimeError: project not found

    Returns:
        bool: does folder exist in project
    """
    if not check_project_exists(project_id):
        raise RuntimeError(f"Project {project_id} does not exist")

    try:
        dxpy.api.project_list_folder(
            project_id,
            input_params={"folder": folder_path, "only": "folders"},
            always_retry=True
        )
        return True
    except dxpy.exceptions.ResourceNotFound:
        return False


def get_prod_version(
    ref_proj_id, ref_proj_folder, genome_build
) -> tuple[str, str, str]:
    """gets information on latest production ClinVar file

    Args:
        ref_proj_id (str): DNAnexus project ID for 001 reference project
        ref_proj_folder (str): folder path containing ClinVar files
        genome_build (str): genome build of ClinVar file

    Raises:
        RuntimeError: no ClinVar files could be found in ref project folder
        RuntimeError: project folder does not exist
        RuntimeError: all found files had invalid dates in name

    Returns:
        recent_version: str
            version of production Clinvar file
        vcf_id: str
            DNAnexus file ID for production vcf file
        index_id: str
            DNAnexus file ID for production vcf index file
    """
    if not check_proj_folder_exists(ref_proj_id, ref_proj_folder):
        raise RuntimeError(
            f"Folder {ref_proj_folder} does not exist in project {ref_proj_id}"
        )
    name_regex = f"clinvar_*_{genome_build}.vcf.gz"
    vcf_files = list(dxpy.find_data_objects(
        name=name_regex, name_mode='glob', project=ref_proj_id,
        folder=ref_proj_folder,
        describe={
            "fields": {
                "name": True
            }
        }
    ))

    # Error handling if files are not found in 001 reference
    if not vcf_files:
        raise RuntimeError(
            f"No clinvar files matching {name_regex}"
            + " were found in 001 reference project"
        )

    latest_time = datetime.strptime("20200101", '%Y%m%d').date()
    recent_version = vcf_id = index_id = version = ""

    for file in vcf_files:
        name = file["describe"]["name"]
        # if name does not match regex, skip file
        try:
            version = re.search(r"clinvar_([0-9]{8})", name).groups()[0]
        except AttributeError:
            continue
        version_date = datetime.strptime(version, '%Y%m%d').date()
        if version_date > latest_time:
            latest_time = version_date
            recent_version = version
            vcf_id = file["id"]

    # if no recent version could be found
    if recent_version == "":
        raise RuntimeError(
            f"All clinvar files matching {name_regex}"
            + " in 001 reference project had invalid dates in name"
        )

    # get index file based on clinvar version
    index_id = find_dx_file(
        ref_proj_id, f"/annotation/{genome_build}/clinvar",
        f"clinvar_{recent_version}_{genome_build}.vcf.gz.tbi", False
    )

    # return latest production version
    return recent_version, vcf_id, index_id


def get_prod_vep_config(ref_proj_id, ref_proj_folder, assay) -> str:
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
        raise RuntimeError(
            f"Folder {ref_proj_folder} does not exist in project {ref_proj_id}"
        )
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
        raise RuntimeError(f"No vep config files matching {name_regex}"
                           + " were found in 001 reference project")

    # return the most recent file uploaded found
    if len(config_files) == 1:
        return config_files[0]["id"]
    else:
        return get_latest_version(config_files)["id"]


def get_latest_version(files) -> str:
    """get latest file in list by version

    Args:
        file_names (list[list[str]]): results of dxpy.find_data_objects
        to compare

    Raises:
        RuntimeError: all config files have invalid versions

    Returns:
        list[str]: name of latest file
    """
    regex = r"[0-9]+\.[0-9]+\.[0-9]+"
    latest_version = version.parse("0.0.1")
    latest_file = None
    for file in files:
        name = file["describe"]["name"]
        version_str = re.search(regex, name)
        # if cannot find match for regex continue
        if not version_str:
            continue
        version_parsed = version.parse(version_str)
        if version > latest_version:
            latest_version = version_parsed
            latest_file = file

    if latest_file is None:
        raise RuntimeError("All config files have invalid version numbers")
    else:
        return latest_file


def find_dx_file(
        project_id, folder_path, file_name, return_all
) -> str | list[str]:
    """gets file IDs of DNAnexus files from file name.
    returns latest file if return_all is false
    returns all file matches if return_all is true

    Args:
        project_id (str): DNAnexus project ID to search in
        folder_path (str): DNAnexus folder path to search in
        file_name (str): DNAnexus file name to search for
        return_all (bool): return all matches if true latest match if false

    Raises:
        IOError: DNAnexus file does not exist

    Returns:
        str: DNAnexus file ID
        list (str): list of DNAnexus file IDs
    """
    if folder_path == "":
        folder_path = None

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
        raise IOError(
            f"DNAnexus file {file_name} does not exist in project"
            + f" {project_id} folder {folder_path}"
        )

    if return_all:
        # return all files found
        file_ids = []
        for file in file_list:
            file_ids.append(file["id"])
        return file_ids
    else:
        # return the most recent file uploaded found
        if len(file_list) == 1:
            return file_list[0]["id"]
        else:
            latest = file_list[0]
            for file in file_list:
                if file["describe"]["created"] > latest["describe"]["created"]:
                    latest = file
            return latest["id"]


def load_config(bin_path, config_path) -> tuple[str, str, str, str]:
    """loads config file

    Args:
        bin_path (str): path to bin directory
        config_path (str): path to config file

    Returns:
        ref_proj_id: str
            DNAnexus project ID for 001 reference project
        dev_proj_id: str
            DNAnexus project ID for 003 development project
        slack_channel: str
            Slack API token
        clinvar_link: str
            Base link used to fetch clinvar files
    """
    with open(config_path, "r", encoding="utf8") as json_file:
        config = json.load(json_file)

    ref_proj_id = config.get("001_REFERENCE_PROJ_ID")
    dev_proj_id = config.get("003_DEV_CLINVAR_UPDATE_PROJ_ID")
    slack_channel = config.get("SLACK_CHANNEL")
    clinvar_link = config.get("CLINVAR_BASE_LINK")

    return ref_proj_id, dev_proj_id, slack_channel, clinvar_link


def load_config_repo(assay, bin_path, config_path) -> str:
    """loads config file for VEP config update

    Args:
        assay (str): name of assay
        bin_path (str): path to bin directory
        config_path (str): path to config file

    Raises:
        RuntimeError: invalid assay name

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
    else:
        raise RuntimeError("Invalid assay name provided to load_config_repo")

    return repo


def update_json(json_path_glob, nested_path, replace_with) -> None:
    """updates json file by replacing specific string from regex

    Args:
        json_path_glob (str): glob path to json
        nested_path (tuple): tuple of n strings representing nested structure
        string to be replaced
        replace_with (str): string to replace the found string

    Raises:
        RuntimeError: json did not contain value at nested path
    """
    config_filename = glob.glob(json_path_glob)[0]
    key_found = False
    with open(config_filename, "r") as json_file:
        config = json.load(json_file)

    flat_config = flatten(config)
    for key in flat_config:
        if key == nested_path:
            flat_config[key] = replace_with
            key_found = True
            break
    if not key_found:
        raise RuntimeError(
            f"Json did not contain value at nested path {nested_path}"
        )

    config = unflatten(flat_config)
    try:
        os.remove(config_filename)
    except OSError:
        pass
    with open(config_filename, "w") as f:
        json.dump(config, f)


def is_json_content_different(json_path_glob, nested_path, new_string) -> bool:
    """checks if specific string in json is different to string provided

    Args:
        json_path_glob (str): glob path to json
        nested_path (tuple): tuple of n strings representing nested structure
        string to be compared against
        new_string (str): new string to be compared against

    Raises:
        RuntimeError: json did not contain value at nested path

    Returns:
        bool: is content different
    """
    config_filename = glob.glob(json_path_glob)[0]
    with open(config_filename, "r") as json_file:
        config = json.load(json_file)

    flat_config = flatten(config)
    for key in flat_config:
        if key == nested_path:
            if new_string == flat_config[key]:
                return False
            else:
                return True
    # if nested path could not be found
    raise RuntimeError(
        f"Json did not contain value at nested path {nested_path}"
    )


def search_json(json_path_glob, nested_path) -> str:
    """attempts to find string at nested path in json

    Args:
        json_path_glob (str): glob path to json
        nested_path (tuple): tuple of n strings representing nested structure
        string to be found

    Raises:
        RuntimeError: json did not contain value at nested path

    Returns:
        str: string found at nested path
    """
    config_filename = glob.glob(json_path_glob)[0]
    with open(config_filename, "r") as json_file:
        config = json.load(json_file)

    flat_config = flatten(config)
    for key in flat_config:
        if key == nested_path:
            return flat_config[key]

    # if nested path could not be found
    raise RuntimeError(
        f"Json did not contain value at nested path {nested_path}"
    )


def increment_version(version) -> str:
    """increments version number by 1

    Args:
        version (str): version to increment

    Raises:
        RuntimeError: version has invalid format

    Returns:
        str: incremented version
    """
    # string format: x.y.z
    regex = r"([0-9]+)\.([0-9]+)\.([0-9]+)"
    matched = re.search(regex, version)
    if not matched:
        raise RuntimeError(
            f"Version {version} has invalid format."
            + " Format must be x.y.z where x y and z are integers"
        )
    new_version_end = int(matched[3]) + 1
    return_version = f"{matched[1]}.{matched[2]}.{new_version_end}"
    return return_version


def get_recent_002_projects(assay, months) -> pd.DataFrame:
    """get 002 projects matching assay name in past n months

    Args:
        assay (str): name of assay to check
        months (int): number of months ago to check from

    Raises:
        RuntimeError: No projects found for assay in past n months

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
        raise RuntimeError(
            f"No 002 projects found for assay {assay} in past {months} months"
        )

    assay_info = [
        [x["describe"]["id"],  x["describe"]["name"], x["describe"]["created"]]
        for x in assay_response
    ]

    # get most recent 002 in search and return project id
    df = pd.DataFrame.from_records(
        data=assay_info, columns=[
            "id", "name", "created"
        ]
    )
    # sort by date
    df = df.sort_values(["created"], ascending=False)

    return df


def match_folder_name(project_id, base_path, folder_regex) -> str:
    """finds path to folder in project from folder name regex

    Args:
        project_id (str): DNAnexus project ID
        base_path (str): path to folder
        folder_regex (str): regex of folder name

    Raises:
        RuntimeError: base path not found in project
        RuntimeError: folder matching regex not found

    Returns:
        str: path to folder matched by name regex
    """
    if not check_proj_folder_exists(project_id, base_path):
        raise RuntimeError(
            f"Folder {base_path} does not exist in project {project_id}"
        )

    folders = list_subfolders(
        project=project_id, path=base_path, recurse=False
    )
    match_regex = re.compile(folder_regex)
    for folder in folders:
        if match_regex.search(folder):
            return folder
    raise RuntimeError(
        f"No folder matched the regex {folder_regex}"
        + f" in path {base_path} of project {project_id}")


def search_for_regex(log_file, regex) -> list[str]:
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
