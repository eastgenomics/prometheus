"""
Handles running vep with development and production ClinVar vcf files
"""

import dxpy
import subprocess
import glob
from dxpy.bindings.dxfile_functions import download_folder
from dxpy.bindings.dxfile import DXFile
import vcfpy
import os

# local modules
import compare_annotation
from utils import check_jobs_finished
from utils import check_proj_folder_exists
from utils import find_dx_file
from inspect_vep_logs import inspect_logs
from utils import get_recent_002_projects


def vep_testing_config(project_id, dev_config_id,
                       dx_update_folder, ref_proj_id,
                       assay, genome_build,
                       clinvar_id):
    """performs testing for vep config and generates summary file

    Args:
        project_id (str): DNAnexus project ID for dev project
        dev_config_id (str): DNAnexus ID of dev config file
        dx_update_folder (str): dev folder for current vep update
        ref_proj_id (str): DNAnexus project ID for 001 reference
        assay (str): vep assay name

    Returns:
        test_summary_id (str): DNAnexus file ID for summary file
    """
    vcf_id, bed_id = get_recent_vep_vcf_bed(assay,
                                            ref_proj_id,
                                            genome_build)
    # Run vep
    vep_job_folder = "vep_run_{}".format(assay)
    vep_job = run_vep(project_id, vep_job_folder, dev_config_id,
                      vcf_id, bed_id, dx_update_folder)
    # Pause until jobs have finished
    job_list = [vep_job]
    check_jobs_finished(job_list, 2, 20)

    log = "temp/vep_job_log.txt"
    os.system("dx watch {} > {}".format(vep_job, log))

    config_name = DXFile(dxid=dev_config_id,
                         project=project_id).describe()["name"]
    test_passed, results_file = inspect_logs(log,
                                             vep_job,
                                             config_name,
                                             clinvar_id,
                                             assay)

    # upload file to DNAnexus
    evidence_folder = "{}/Evidence".format(dx_update_folder)
    if not check_proj_folder_exists(project_id=project_id,
                                    folder_path=evidence_folder):
        dev_project = dxpy.bindings.dxproject.DXProject(dxid=project_id)
        dev_project.new_folder(evidence_folder, parents=True)
    test_summary_id = dxpy.upload_local_file(filename=results_file,
                                             project=project_id,
                                             folder=evidence_folder)

    return test_summary_id


def vep_testing_annotation(project_id, dev_config_id, prod_config_id,
                           clinvar_version, bin_folder, ref_proj_id,
                           genome_build):
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
    twe_vcf_id, twe_bed_id = get_recent_vep_vcf_bed("TWE",
                                                    ref_proj_id,
                                                    genome_build)
    tso_vcf_id, tso_bed_id = get_recent_vep_vcf_bed("TSO500",
                                                    ref_proj_id,
                                                    genome_build)

    update_folder = ("/ClinVar_version_{}".format(clinvar_version)
                     + "_annotation_resource_update")

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

    # Perform comparison of differences when using prod vs. dev
    # Get diff for twe
    twe_diff_filename = get_diff_output(prod_twe_output, dev_twe_output,
                                        "twe", bin_folder)
    # Get diff for tso500
    tso_diff_filename = get_diff_output(prod_tso_output, dev_tso_output,
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
    folder_path = "{0}/{1}".format(update_folder, folder)
    if not check_proj_folder_exists(project_id, folder_path):
        raise Exception("Folder {} not found in {}".format(folder_path,
                                                           project_id))
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
    vcf_output_path = "temp/parsed_vcf_{}.txt".format(label)
    vcf_reader = vcfpy.Reader.from_path(vcf_input_path)

    with open(vcf_output_path, "w") as file:
        for record in vcf_reader:
            csq_fields = (record.INFO["CSQ"][0]).split("|")
            info = "."
            if csq_fields[4] != "":
                info = csq_fields[4]

            new_record = ("{}:{}:{}:{} {} {} {}\n"
                          .format(record.CHROM, record.POS,
                                  record.REF, record.ALT[0].value,
                                  csq_fields[2],
                                  csq_fields[3],
                                  info))
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


def get_recent_vep_vcf_bed(assay, ref_proj_id, genome_build):
    """gets most recent vcf and panel bed files in use for given assay

    Args:
        assay (str): name of assay

    Raises:
        Exception: no 002 projects found for assay in past 12 months
        IOError: panel bed not found for assay
        IOError: vcf not found for assay

    Returns:
        vcf: str
            DNAnexus file ID for most recent VCF file found
        bed: str
            DNAnexus file ID for most recent panel bed file found
    """
    df = get_recent_002_projects(assay, 12)

    if assay == "TSO500":
        folder_bed = "/bed_files/{}/kits/tso500".format(genome_build)
        vcf_name = "*Hotspots.vcf.gz"
    else:
        folder_bed = "/bed_files/{}/kits/twist_exome".format(genome_build)
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
            break
        except IOError:
            pass

    if vcf == "":
        raise IOError("VCF file not found in recent 002"
                      + " project for assay {}".format(assay))

    try:
        bed = find_dx_file(ref_proj_id, folder_bed, bed_name)
    except IOError:
        pass

    if bed == "":
        raise IOError("Panel bed file not found in 001"
                      + " ref project for assay {}".format(assay))

    return vcf, bed
