"""
Get latest weekly release of ClinVar files
"""

import re
from ftplib import error_perm
from ftplib import FTP
from datetime import datetime
import dxpy
import time


def get_ftp_files(
        base_vcf_link, base_vcf_path, genome_build
) -> tuple[str, str, datetime, str]:
    """retrieves information about latest ClinVar file

    Args:
        base_vcf_link (str): link used to download clivar files
        base_vcf_path (str): path appended to link used to download clinvar
        files
        genome_build (str): build of genome

    Returns:
        recent_vcf_file: str
            name of latest vcf file on ncbi website
        recent_tbi_file: str
            name of latest vcf index file on ncbi website
        latest_time: datetime
            version date of latest ClinVar file
        recent_vcf_version: str
            version of latest ClinVar file
    """
    clinvar_gz_regex = re.compile(r"^clinvar_[0-9]+\.vcf\.gz$")
    ftp = connect_to_website(base_vcf_link, base_vcf_path, genome_build)

    file_list = []
    ftp.retrlines('LIST', file_list.append)

    latest_time = datetime.strptime("20200101", '%Y%m%d').date()
    recent_vcf_version = ""
    recent_vcf_file = ""

    for file_name in file_list:

        if not file_name.strip():
            continue
        file_name = file_name.split()[-1]

        # find most recent version of annotation resource
        if clinvar_gz_regex.match(file_name):
            # get just the full clinvar vcf
            ftp_vcf = file_name
            ftp_vcf_ver = str(ftp_vcf.split("_")[1].split(".")[0])
            date_object = datetime.strptime(str(ftp_vcf_ver), '%Y%m%d').date()

            if latest_time < date_object:
                latest_time = date_object
                recent_vcf_version = ftp_vcf_ver
                recent_vcf_file = file_name

        # get corresponding .vcf.gz.tbi file based on vcf name
        recent_tbi_file = recent_vcf_file + ".tbi"

    # safety feature to prevent too many requests to server
    time.sleep(1)

    return recent_vcf_file, recent_tbi_file, latest_time, recent_vcf_version


def retrieve_clinvar_files(
    project_id, recent_vcf_file, recent_tbi_file, clinvar_version,
    genome_build, base_vcf_link
) -> tuple[str, str]:
    """download latest ClinVar files to 003 development project

    Args:
        project_id (str): DNAnexus file ID of 003 dev project
        recent_vcf_file (str): file name of most recent ClinVar vcf file
        recent_tbi_file (str): file name of most recent ClinVar tbi file
        clinvar_version (str): version of latest Clinvar file
        genome_build (str): genome build of ClinVar file to be retrieved
        base_vcf_link (str): link used to download clivar files

    Raises:
        Exception: invalid genome build provided
        FileNotFoundError: vcf file not found
        FileNotFoundError: tbi file not found

    Returns:
        vcf_id: str
            DNAnexus file ID for downloaded vcf file
        tbi_id: str
            DNAnexus file ID for downloaded tbi file
    """
    # validate genome build
    valid_genome_builds = ["b37", "b38"]
    if genome_build not in valid_genome_builds:
        raise Exception(
            f"Genome build \"{genome_build}\"specified in"
            + " retrieve_clinvar_files is invalid"
        )

    build_number = genome_build[1:]
    vcf_link = (
        f"{base_vcf_link}/vcf_GRCh"
        + f"{build_number}/weekly/{recent_vcf_file}")
    tbi_link = (
        f"{base_vcf_link}/vcf_GRCh"
        + f"{build_number}/weekly/{recent_tbi_file}")
    vcf_base_name = recent_vcf_file.split(".")[0]
    renamed_vcf = f"{vcf_base_name}_{genome_build}.vcf.gz"
    renamed_tbi = f"{vcf_base_name}_{genome_build}.vcf.gz.tbi"
    subfolder = (
        f"ClinVar_version_{clinvar_version}"
        + "_annotation_resource_update"
    )
    project_folder = f"/{subfolder}/Testing"

    # start url fetcher jobs
    run_url_fetcher(
        project_id, project_folder, vcf_link, renamed_vcf
    )
    run_url_fetcher(
        project_id, project_folder, tbi_link, renamed_tbi
    )

    # find file in DNAnexus output folder + get file ID
    vcf_files = list(dxpy.find_data_objects(
        name=renamed_vcf,
        project=project_id,
        folder=project_folder
    ))

    # check if file is present
    if vcf_files:
        vcf_id = vcf_files[0]['id']
    else:
        raise FileNotFoundError(
            f"VCF file {vcf_id} not found in DNAnexus project {project_id} in"
            + f" folder {project_folder}")

    tbi_files = list(dxpy.find_data_objects(
        name=renamed_tbi,
        project=project_id,
        folder=project_folder
    ))

    # check if file is present
    if tbi_files:
        tbi_id = tbi_files[0]['id']
    else:
        raise FileNotFoundError(
            f"TBI file {tbi_id} not found in DNAnexus project {project_id} in"
            + f" folder {project_folder}")

    return vcf_id, tbi_id


def run_url_fetcher(
    project_id, destination_folder, download_link, new_file_name
) -> str:
    """runs url fetcher to download a file to a given project folder

    Args:
        project_id (str): DNAnexus project ID for project to download to
        destination_folder (str): path to DNAnexus project folder
        download_link (str): website link to download from
        new_file_name (str): new name of downloaded file

    Returns:
        str: DNAnexus job ID for url fetcher job run
    """
    inputs = {
        "url": download_link,
        "output_name": new_file_name
    }

    job = dxpy.bindings.dxapp.DXApp(name="url_fetcher").run(
        app_input=inputs,
        project=project_id,
        folder=destination_folder,
        priority='high'
    )
    job.wait_on_done()
    job_id = job.describe().get('id')

    return job_id


def connect_to_website(base_vcf_link, base_vcf_path, genome_build) -> FTP:
    """generates a FTP object to enable download from ncbi website

    Args:
        base_vcf_link (str): link used to download clivar files
        base_vcf_path (str): path appended to link used to download clinvar
        genome_build (str): build of genome

    Raises:
        RuntimeError: cannot connect to ncbi website
        RuntimeError: invalid base vcf link provided to connect_to_website
        RuntimeError: cannot find directory provided as base_vcf_path

    Returns:
        ftplib.FTP: FTP object to enable download from ncbi website

    """
    # safety feature to prevent too many requests to server
    time.sleep(1)
    genome_version = genome_build[1:]

    # remove "https://" from link"
    pattern = r"(http|https)://(.+)"
    result = re.search(pattern, base_vcf_link)
    if result is None or len(result.groups()) < 2:
        raise RuntimeError(
            "Error: invalid base vcf link provided to connect_to_website"
        )
    else:
        vcf_link = result.group(2)

    try:
        ftp = FTP(vcf_link)
        ftp.login()
        vcf_path = (
            f"{base_vcf_path}/vcf_GRCh"
            + f"{genome_version}/weekly/"
        )
        ftp.cwd(vcf_path)
    except OSError:
        raise RuntimeError("Error: cannot connect to ncbi website")
    except error_perm:
        raise RuntimeError(f"Error: cannot find directory {vcf_path}")

    return ftp
