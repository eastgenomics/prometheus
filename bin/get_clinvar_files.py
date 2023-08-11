"""
Get latest weekly release of ClinVar files
"""

import os
import re
from ftplib import FTP
from datetime import datetime
import dxpy
from os.path import exists
import time
from utils import check_jobs_finished

dirname = os.path.dirname(__file__)
clinvar_dir = os.path.join(dirname, "/data/clinvar/")
print("Clinvar dir: {}".format(clinvar_dir))

def get_ftp_files():
    clinvar_gz_regex = re.compile("^clinvar_[0-9]+\.vcf\.gz$")
    ftp = connect_to_website()

    file_list = []
    ftp.retrlines('LIST', file_list.append)

    earliest_time = datetime.strptime("20200101", '%Y%m%d').date()
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

def retrieve_clinvar_files(project_id, download_dir, recent_vcf_file, recent_tbi_file, clinvar_version, genome_build):
    #vcf_path, tbi_path = download_vcf(download_dir, recent_vcf_file, recent_tbi_file)
    #vcf_id, tbi_id = upload_to_DNAnexus(project_id, vcf_path, tbi_path, clinvar_version, genome_build)

    # validate genome build
    valid_genome_builds = ["b37", "b38"]
    if not genome_build in valid_genome_builds:
        raise Exception("Genome build \"{}\"specified in retrieve_clinvar_files is invalid".format(genome_build))
    
    build_number = genome_build[1:]
    vcf_link = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh{}/weekly/{}".format(build_number, recent_vcf_file)
    tbi_link = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh{}/weekly/{}".format(build_number, recent_tbi_file)
    vcf_base_name = recent_vcf_file.split(".")[0]
    renamed_vcf = "{}_{}.vcf.gz".format(vcf_base_name, genome_build)
    renamed_tbi = "{}_{}.vcf.gz.tbi".format(vcf_base_name, genome_build)
    subfolder = "ClinVar_version_{}_annotation_resource_update".format(clinvar_version)
    project_folder = "/{}/Testing".format(subfolder)

    # start url fetcher jobs
    vcf_job_id = run_url_fetcher(project_id, project_folder, vcf_link, renamed_vcf)
    tbi_job_id = run_url_fetcher(project_id, project_folder, tbi_link, renamed_tbi)

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
        raise FileNotFoundError("VCF file {} not found in DNAnexus project {} in folder {}"
                                .format(vcf_id, project_id, project_folder))

    tbi_files = list(dxpy.find_data_objects(
            name=renamed_tbi,
            project=project_id,
            folder=project_folder
        ))
    
    # check if file is present
    if tbi_files:
        tbi_id = tbi_files[0]['id']
    else:
        raise FileNotFoundError("TBI file {} not found in DNAnexus project {} in folder {}"
                                .format(tbi_id, project_id, project_folder))


    return vcf_id, tbi_id

def run_url_fetcher(project_id, destination_folder, download_link, new_file_name):
    inputs = {
        "url" : download_link,
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

def download_vcf(download_dir, ftp_vcf, ftp_vcf_index):
    vcf_file_to_download = os.path.join(download_dir, ftp_vcf)
    tbi_file_to_download = os.path.join(download_dir, ftp_vcf_index)

    # if files are already present, skip the download
    if exists(vcf_file_to_download) and exists(tbi_file_to_download):
        return vcf_file_to_download, tbi_file_to_download

    ftp = connect_to_website()

    # download unless files are already present
    if not exists(vcf_file_to_download):
        with open(vcf_file_to_download, 'wb') as localfile:
            ftp.retrbinary('RETR ' + ftp_vcf, localfile.write, 1024)

    if not exists(tbi_file_to_download):
        with open(tbi_file_to_download, 'wb') as localfile:
            ftp.retrbinary('RETR ' + ftp_vcf_index, localfile.write, 1024)

    ftp.quit()

    return vcf_file_to_download, tbi_file_to_download

def upload_to_DNAnexus(project_id, vcf_path, tbi_path, vcf_version, genome_build):
    # upload downloaded clinvar files to new folder in existing 003 project
    subfolder = "ClinVar_version_{}_annotation_resource_update".format(vcf_version)
    folder_path = "/{}/Testing".format(subfolder)

    # get DNAnexus folder object
    dev_project = dxpy.bindings.dxproject.DXProject(project_id)
    dev_project.new_folder(folder_path, parents=True)

    # Upload from a path to new project with dxpy
    sleep_interval = 60 # 60 seconds
    max_retries = 3
    retry_count = 0
    if (retry_count <= max_retries):
        try:
            vcf_file = dxpy.upload_local_file(filename=vcf_path, project=project_id, folder=folder_path)
        except TimeoutError:
            print("Connection aborted due to timeout when attempting to upload VCF files to DNAnexus. Retrying...")
            retry_count += 1
            time.sleep(sleep_interval)
    else:
        raise TimeoutError("Exceeded maximum number of reties when trying to upload VCF file to DNAnexus")
    tbi_file = dxpy.upload_local_file(filename=tbi_path, project=project_id, folder=folder_path)

    # Append build (e.g., b37, b38) to files
    vcf_file.rename("clinvar_{0}_{1}.vcf.gz".format(vcf_version, genome_build))
    tbi_file.rename("clinvar_{0}_{1}.vcf.gz.tbi".format(vcf_version, genome_build))

    vcf_file_id = vcf_file.get_id()
    tbi_file_id = tbi_file.get_id()
    return vcf_file_id, tbi_file_id

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
