"""
Get latest weekly release of ClinVar files
"""

import re
from ftplib import FTP
from datetime import datetime
import dxpy

from utils import check_jobs_finished


def get_ftp_files():
    """retrieves information about latest ClinVar file

    Returns:
        recent_vcf_file: str
            name of latest vcf file on ncbi website
        recent_tbi_file: str
            name of latest vcf index file on ncbi website
        latest_time: datetime.date
            version date of latest ClinVar file
        recent_vcf_version: str
            version of latest ClinVar file
    """
    clinvar_gz_regex = re.compile(r"^clinvar_[0-9]+\.vcf\.gz$")
    ftp = connect_to_website()

    file_list = []
    ftp.retrlines('LIST', file_list.append)

    latest_time = datetime.strptime("20200101", '%Y%m%d').date()
    recent_vcf_version = ""
    recent_vcf_file = ""

    for file_name in file_list:

        if file_name == "":
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

    return recent_vcf_file, recent_tbi_file, latest_time, recent_vcf_version


def retrieve_clinvar_files(project_id, recent_vcf_file, recent_tbi_file,
                           clinvar_version, genome_build):
    """download latest ClinVar files to 003 development project

    Args:
        project_id (str): DNAnexus file ID of 003 dev project
        recent_vcf_file (str): file name of most recent ClinVar vcf file
        recent_tbi_file (str): file name of most recent ClinVar tbi file
        clinvar_version (str): version of latest Clinvar file
        genome_build (str): genome build of ClinVar file to be retrieved

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
        raise Exception("Genome build \"{}\"specified in ".format(genome_build)
                        + "retrieve_clinvar_files is invalid")

    build_number = genome_build[1:]
    vcf_link = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh"
    + "{}/weekly/{}".format(build_number, recent_vcf_file)
    tbi_link = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh"
    + "{}/weekly/{}".format(build_number, recent_tbi_file)
    vcf_base_name = recent_vcf_file.split(".")[0]
    renamed_vcf = "{}_{}.vcf.gz".format(vcf_base_name, genome_build)
    renamed_tbi = "{}_{}.vcf.gz.tbi".format(vcf_base_name, genome_build)
    subfolder = "ClinVar_version_{}".format(clinvar_version)
    + "annotation_resource_update"
    project_folder = "/{}/Testing".format(subfolder)

    # start url fetcher jobs
    vcf_job_id = run_url_fetcher(project_id, project_folder,
                                 vcf_link, renamed_vcf)
    tbi_job_id = run_url_fetcher(project_id, project_folder,
                                 tbi_link, renamed_tbi)

    # Pause until jobs have finished
    job_list = [vcf_job_id, tbi_job_id]
    check_jobs_finished(job_list, 2, 20)

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
        raise FileNotFoundError("VCF file {} not found in ".format(vcf_id)
                                + "DNAnexus project {} in folder {}"
                                .format(project_id, project_folder))

    tbi_files = list(dxpy.find_data_objects(
            name=renamed_tbi,
            project=project_id,
            folder=project_folder
        ))

    # check if file is present
    if tbi_files:
        tbi_id = tbi_files[0]['id']
    else:
        raise FileNotFoundError("TBI file {} not found in ".format(tbi_id)
                                + "DNAnexus project {} in folder {}"
                                .format(project_id, project_folder))

    return vcf_id, tbi_id


def run_url_fetcher(project_id, destination_folder,
                    download_link, new_file_name):
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
    job_id = job.describe().get('id')

    return job_id


def connect_to_website():
    """generates a FTP object to enable download from ncbi website

    Returns:
        ftplib.FTP: FTP object to enable download from ncbi website
    """
    try:
        ftp = FTP("ftp.ncbi.nlm.nih.gov")
        ftp.login()
        ftp.cwd("/pub/clinvar/vcf_GRCh37/weekly/")
    except OSError as error:
        print("Error: cannot connect to ncbi website")
        print(error)
        exit

    return ftp
