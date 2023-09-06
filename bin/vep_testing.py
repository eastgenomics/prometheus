"""
Handles running vep with development and production ClinVar vcf files
"""

import dxpy
import subprocess
import glob
from dxpy.bindings.dxfile_functions import download_folder
import vcfpy
import pandas as pd

# local modules
import compare_annotation
from utils import check_jobs_finished
from utils import check_proj_folder_exists
from utils import find_dx_file


def perform_vep_testing(project_id, dev_config_id, prod_config_id,
                        clinvar_version, bin_folder):
    """compares vep output for dev and prod files and outputs reports

    Args:
        project_id (str): DNAnexus file ID for 003 dev project
        dev_config_id (str): DNAnexus file ID for dev vep config file
        prod_config_id (str): DNAnexus file ID for prod vep config file
        clinvar_version (str): version of ClinVar vcf
        bin_folder (str): path to bin folder

    Returns:
        added_csv: str
            path to csv report for added variants
        deleted_csv: str
            path to csv report for deleted variants
        changed_csv: str
            path to csv report for changed variants
        detailed_csv: str
            path to csv report for detailed changed variants
        job_report: str
            path to txt file report for vep jobs run
    """
    twe_vcf_id, twe_bed_id = get_recent_vep_vcf_bed("TWE")
    tso_vcf_id, tso_bed_id = get_recent_vep_vcf_bed("TSO500")

    update_folder = "ClinVar_version_{}".format(clinvar_version)
    + "_annotation_resource_update"

    # Run on Dev TWE VCF
    dev_twe_folder = "clinvar_testing_dev_twe"
    dev_twe_job = run_vep(project_id, dev_twe_folder, dev_config_id,
                          twe_vcf_id, twe_bed_id, update_folder)
    # Run on Dev TSO500 VCF
    dev_tso_folder = "clinvar_testing_dev_tso500"
    dev_tso_job = run_vep(project_id, dev_tso_folder, dev_config_id,
                          tso_vcf_id, tso_bed_id, update_folder)
    # Run on Prod TWE VCF
    prod_twe_folder = "clinvar_testing_prod_twe"
    prod_twe_job = run_vep(project_id, prod_twe_folder, prod_config_id,
                           twe_vcf_id, twe_bed_id, update_folder)
    # Run on Prod TSO500 VCF
    prod_tso_folder = "clinvar_testing_prod_tso500"
    prod_tso_job = run_vep(project_id, prod_tso_folder, prod_config_id,
                           tso_vcf_id, tso_bed_id, update_folder)

    # Pause until jobs have finished
    job_list = [dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job]
    check_jobs_finished(job_list, 2, 20)

    # Add job IDs to report text file
    job_report = make_job_report(dev_twe_job, dev_tso_job, prod_twe_job,
                                 prod_tso_job, "./temp/job_report.txt")

    # parse VEP run output vcf using bcftools
    dev_twe_output = parse_vep_output(project_id, dev_twe_folder,
                                      "dev_twe", update_folder)
    dev_tso_output = parse_vep_output(project_id, dev_tso_folder,
                                      "dev_tso500", update_folder)
    prod_twe_output = parse_vep_output(project_id, prod_twe_folder,
                                       "prod_twe", update_folder)
    prod_tso_output = parse_vep_output(project_id, prod_tso_folder,
                                       "prod_tso500", update_folder)

    # Perform comparison of differences when using dev vs. prod
    # Get diff for twe
    twe_diff_filename = get_diff_output(dev_twe_output, prod_twe_output,
                                        "twe", bin_folder)
    # Get diff for tso500
    tso_diff_filename = get_diff_output(dev_tso_output, prod_tso_output,
                                        "tso500", bin_folder)

    # Get detailed table of differences for twe and tso500
    (added_csv,
     deleted_csv,
     changed_csv,
     detailed_csv) = (compare_annotation
                      .compare_annotation(twe_diff_filename,
                                          tso_diff_filename))

    return added_csv, deleted_csv, changed_csv, detailed_csv, job_report


def parse_vep_output(project_id, folder, label, update_folder):
    """parses output from running vep and returns path to processed output

    Args:
        project_id (str): DNAnexus project ID for 003 dev project
        folder (str): folder name to output to in current update folder
        label (str): label for naming the end of the output file
        update_folder (str): path to folder in 003 project for current update
        bin_folder (str): path to bin folder

    Raises:
        Exception: Folder not found in project
        IOError: Input vcf file not found

    Returns:
        str: path to parsed vep output
    """
    # Download files output from vep
    folder_path = "/{0}/{1}".format(update_folder, folder)
    if not check_proj_folder_exists(project_id, folder_path):
        raise Exception("Folder {} not found in {}".format(project_id,
                                                           folder_path))
    download_folder(project_id,
                    "temp/{}".format(label),
                    folder=folder_path,
                    overwrite=True)

    # Parse the variant and ClinVar annotation fields
    glob_path = "temp/{}/*.vcf.gz".format(label)
    vcf_input_path = ""
    try:
        vcf_input_path = glob.glob(glob_path)[0]
    except IndexError:
        raise IOError("File matching glob {} not found".format(glob_path))
    vcf_output_path = "parsed_vcf_{}.txt".format(label)
    vcf_reader = vcfpy.Reader(open(vcf_input_path, 'rb'))

    with open(vcf_output_path, "w") as file:
        for record in vcf_reader:
            new_record = ("{}:{}:{}:{} {} {} {}\n"
                          .format(record.CHROM, record.POS,
                                  record.REF, record.ALT,
                                  record.INFO["Clinvar"],
                                  record.INFO["ClinVar_CLNSIG"],
                                  record.INFO["ClinVar_CLNSIGCONF"]))
            file.write(new_record)

    return vcf_output_path


def get_diff_output(dev_output, prod_output, label, bin_folder):
    """get the diff output between dev and prod vep parsed outputs

    Args:
        dev_output (str): parsed vep output for dev vcf
        prod_output (str): parsed vep output for prod vcf
        label (str): label for naming the end of the output file
        bin_folder (str): path to bin folder

    Returns:
        str: path to diff output txt file
    """
    # run diff
    output_file = "temp/{}_diff_output.txt".format(label)
    diff_input = ["sh", "{}/get_diff.sh".format(bin_folder),
                  dev_output, prod_output, output_file]
    subprocess.run(diff_input, stderr=subprocess.STDOUT)

    return output_file


def make_job_report(dev_twe_job, dev_tso_job, prod_twe_job,
                    prod_tso_job, path) -> str:
    """generates job report txt file from vep run DNAnexus job IDs

    Args:
        dev_twe_job (str): DNAnexus job ID for dev twe vep run
        dev_tso_job (str): DNAnexus job ID for dev tso vep run
        prod_twe_job (str): DNAnexus job ID for prod twe vep run
        prod_tso_job (str): DNAnexus job ID for prod tso vep run
        path (str): output path

    Returns:
        str: path to job report txt file
    """
    try:
        with open(path, "w") as file:
            file.write("Development TWE job: {}\n".format(dev_twe_job))
            file.write("Development TSO500 job: {}\n".format(dev_tso_job))
            file.write("Production TWE job: {}\n".format(prod_twe_job))
            file.write("Production TSO500 job: {}\n".format(prod_tso_job))
    except FileNotFoundError:
        print("The directory for saving the job report "
              + "{} does not exist".format(path))
    except FileExistsError:
        print("The file {} ".format(path)
              + "already exists and job report cannot be saved")

    return path


def run_vep(project_id, project_folder, config_file, vcf_file, panel_bed_file,
            update_folder):
    """runs the DNAnexus app vep

    Args:
        project_id (str): DNAnexus project ID for 003 dev project
        project_folder (str): DNAnexus folder name to run vep in
        config_file (str): DNAnexus file ID for vep config file
        vcf_file (str): DNAnexus file ID for vep vcf file
        panel_bed_file (str): DNAnexus file ID for vep panel bed file
        update_folder (str): DNAnexus folder in 003 project for current update

    Returns:
        str: DNAnexus job ID for vep run
    """
    inputs = {
        "config_file": {'$dnanexus_link': config_file},
        "vcf": {'$dnanexus_link': vcf_file},
        "panel_bed": {'$dnanexus_link': panel_bed_file}
    }

    folder_path = "/{0}/{1}".format(update_folder, project_folder)

    job = dxpy.bindings.dxapp.DXApp(name="eggd_vep").run(
                app_input=inputs,
                project=project_id,
                folder=folder_path,
                priority='high'
            )

    job_id = job.describe().get('id')

    return job_id


def get_recent_vep_vcf_bed(assay):
    """gets most recent vcf and panel bed files in use for given assay

    Args:
        assay (str): name of assay

    Raises:
        Exception: No 002 projects found for assay in past 6 months

    Returns:
        vcf: str
            DNAnexus file ID for most recent VCF file found
        bed: str
            DNAnexus file ID for most recent panel bed file found
    """
    # get 002 projects matching assay name in past 6 months
    assay_response = list(dxpy.find_projects(
            level='VIEW',
            created_after="-6m",
            name=f"002*{assay}",
            name_mode="glob",
            describe={
                'fields': {
                    'id': True, 'name': True, 'created': True
                }
            }
        ))
    if len(assay_response) < 1:
        raise Exception("No 002 projects found for assay {}"
                        .format(assay) + " in past 6 months")
    # get most recent 002 in search and return project id
    df = pd.DataFrame.from_records(data=assay_response,
                                   columns=["id", "name", "created"])
    # sort by date
    df = df.sort(["created"], ascending=[False])

    if assay == "TSO500":
        folder_bed = "/bed_files/b37/kits/tso500/"
        vcf_name = "*Hotspots.vcf.gz"
    else:
        folder_bed = "/bed_files/b37/kits/twist_exome/"
        vcf_name = "*_markdup_recalibrated_Haplotyper.vcf.gz"

    bed_name = "*.bed"
    vcf = ""
    bed = ""

    for index, row in df.iterrows():
        # attempt to find vcf and bed files
        try:
            project_id = row["id"]
            # final all vcf files matching name glob and pick first
            vcf = find_dx_file(project_id, "", vcf_name)
            bed = find_dx_file(project_id, folder_bed, bed_name)
        except IOError:
            pass

    if bed == "":
        raise IOError("Panel bed file not found in 001"
                      + "ref proejct for assay {}".format(assay))
    if vcf == "":
        raise IOError("VCF file not found in recent 002 "
                      + "project for assay {}".format(assay))

    return vcf, bed
