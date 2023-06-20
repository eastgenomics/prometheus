"""
Get latest weekly release of ClinVar files
"""

import os
import re
import gzip
import zipfile
from ftplib import FTP
from datetime import datetime
import dxpy

dirname = os.path.dirname(__file__)
clinvar_dir = os.path.join(dirname, "/data/clinvar/")
print("Clinvar dir: {}".format(clinvar_dir))

def get_ftp_files():
    """
    Get latest available vcf from NCBI FTP site

    Args: None

    Returns:
        ftp_vcf (string): filename of latest available VCF from FTP site
        ftp_vcf_ver (int): version of latest available VCF from FTP site
    """
    clinvar_gz_regex = re.compile("^clinvar_[0-9]+\.vcf\.gz$")
    ftp = connect_to_website()

    file_list = []
    ftp.retrlines('LIST', file_list.append)

    for file_name in file_list:

        if file_name == "":
            continue
        file_name = file_name.split()[-1]

        earliest_time = datetime.strptime("20200101", '%Y%m%d').date()
        recent_vcf_version = ""
        recent_vcf_file = ""

        # find most recent version of annotation resource
        if clinvar_gz_regex.match(file_name):
            # get just the full clinvar vcf
            ftp_vcf = file_name
            ftp_vcf_ver = int(ftp_vcf.split("_")[1].split(".")[0])
            date_object = datetime.strptime(str(ftp_vcf_ver), '%Y%m%d').date()

            if earliest_time < date_object:
                print("The date {0} is earlier".format(date_object))
                earliest_time = date_object
                recent_vcf_version = ftp_vcf_ver
                recent_vcf_file = file_name
                print(file_name)
                print(earliest_time)

        # get corresponding .vcf.gz.tbi file based on vcf name
        recent_tbi_file = recent_vcf_file + ".tbi"

    print("Latest ClinVar version available: {0}".format(earliest_time))

    return recent_vcf_file, recent_tbi_file, earliest_time, recent_vcf_version

def retrieve_clinvar_files(recent_vcf_file, recent_tbi_file, clinvar_version):
    vcf_path, tbi_path = download_vcf(recent_vcf_file, recent_tbi_file)
    project_id, vcf_id, tbi_id = upload_to_DNAnexus(vcf_path, tbi_path, clinvar_version)
    return project_id, vcf_id, tbi_id

def download_vcf(ftp_vcf, ftp_vcf_index):
    """
    Downloads file from NCBI FTP site to /data/clinvar, called by
    check_current_vcf()

    Args:
        filename (string): name of VCF to be downloaded from FTP site

    Outputs:
        localfile (file): downloaded VCF into /data/clinvar/

    Returns: None
    """

    ftp = connect_to_website()

    vcf_file_to_download = os.path.join(clinvar_dir, ftp_vcf)

    with open(vcf_file_to_download, 'wb') as localfile:
        ftp.retrbinary('RETR ' + ftp_vcf, localfile.write, 1024)

    tbi_file_to_download = os.path.join(clinvar_dir, ftp_vcf_index)

    with open(tbi_file_to_download, 'wb') as localfile:
        ftp.retrbinary('RETR ' + ftp_vcf_index, localfile.write, 1024)

    ftp.quit()

    return vcf_file_to_download, tbi_file_to_download

def upload_to_DNAnexus(vcf_path, tbi_path, vcf_version):
    # create new project and capture returned project id and store
    date = datetime.today().strftime('%Y%m%d')
    project_id = dxpy.bindings.dxproject.DXProject().new(
        name="003_{0}_clinvar_annotation_resource_update_{1}".format(date, vcf_version),
        summary=(
            f'ClinVar annotation resource update testing for version {vcf_version}'
        ),
        description=(
            "This project was automatically created by prometheus "
            f"from {os.environ.get('PARENT_JOB_ID')}"
        )
    )

    # Upload from a path to new project with dxpy
    vcf_file = dxpy.upload_local_file(filename=vcf_path, project=project_id)
    tbi_file = dxpy.upload_local_file(filename=tbi_path, project=project_id)

    tbi_file_id = vcf_file.get_id()
    vcf_file_id = tbi_file.get_id()
    return project_id, tbi_file_id, vcf_file_id

def connect_to_website(): 
    try:
        ftp = FTP("ftp.ncbi.nlm.nih.gov")
        ftp.login()
        ftp.cwd("/pub/clinvar/vcf_GRCh37/weekly/")
    except OSError as error:
        print("Error: cannot connect to ncbi website")
        print(error)
        exit

    return ftp
