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
from annotation.compare_annotation import compare_annotation
from .utils import check_proj_folder_exists
from .utils import find_dx_file
from .inspect_vep_logs import inspect_logs
from .utils import get_recent_002_projects


def vep_testing_config(
    project_id, dev_config_id, dx_update_folder, ref_proj_id, assay,
    genome_build, clinvar_id
) -> str:
    """performs testing for vep config and generates summary file

    Args:
        project_id (str): DNAnexus project ID for dev project
        dev_config_id (str): DNAnexus ID of dev config file
        dx_update_folder (str): dev folder for current vep update
        ref_proj_id (str): DNAnexus project ID for 001 reference
        assay (str): vep assay name
        genome_build (str): build of genome
        clinvar_id: DNAnexus ID of clinvar vcf file

    Returns:
        test_summary_id (str): DNAnexus file ID for summary file
    """
    vcf_id, bed_id = get_recent_vep_vcf_bed(
        assay, ref_proj_id, genome_build
    )
    # Run vep
    vep_job_folder = f"vep_run_{assay}"
    vep_job = run_vep(
        project_id, vep_job_folder, dev_config_id,
        vcf_id, bed_id, dx_update_folder
    )
    # Pause until jobs have finished
    vep_job.wait_on_done()

    log = "temp/vep_job_log.txt"
    job_id = vep_job.get_id()
    os.system(f"dx watch {job_id} > {log}")

    try:
        config_name = DXFile(
            dxid=dev_config_id, project=project_id
        ).describe()["name"]
    except dxpy.DXError:
        raise RuntimeError(
            f"DXfile {dev_config_id} could not be found in"
            + f" project {project_id}"
        )
    test_passed, results_file = inspect_logs(
        log, vep_job, config_name, clinvar_id, assay
    )

    # upload file to DNAnexus
    evidence_folder = f"{dx_update_folder}/Evidence"
    if not check_proj_folder_exists(
        project_id=project_id, folder_path=evidence_folder
    ):
        dev_project = dxpy.bindings.dxproject.DXProject(dxid=project_id)
        dev_project.new_folder(evidence_folder, parents=True)
    test_summary_id = dxpy.upload_local_file(
        filename=results_file, project=project_id, folder=evidence_folder
    )

    return test_summary_id


def vep_testing_annotation(
    project_id, dev_config_id, prod_config_id, clinvar_version, bin_folder,
    ref_proj_id, genome_build
) -> tuple[str, str, str, str, str]:
    """compares vep output for dev and prod files and outputs reports

    Args:
        project_id (str): DNAnexus file ID for 003 dev project
        dev_config_id (str): DNAnexus file ID for dev vep config file
        prod_config_id (str): DNAnexus file ID for prod vep config file
        clinvar_version (str): version of ClinVar vcf
        bin_folder (str): path to bin folder
        ref_proj_id (str): DNAnexus ID of reference project
        genome_build (str): build of genome

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
    twe_vcf_id, twe_bed_id = get_recent_vep_vcf_bed(
        "TWE", ref_proj_id, genome_build
    )
    tso_vcf_id, tso_bed_id = get_recent_vep_vcf_bed(
        "TSO500", ref_proj_id, genome_build
    )

    update_folder = (
        f"/ClinVar_version_{clinvar_version}"
        + "_annotation_resource_update"
    )

    # Run on Dev TWE VCF
    dev_twe_folder = "clinvar_testing_dev_twe"
    dev_twe_job = run_vep(
        project_id, dev_twe_folder, dev_config_id,
        twe_vcf_id, twe_bed_id, update_folder
    )
    # Run on Dev TSO500 VCF
    dev_tso_folder = "clinvar_testing_dev_tso500"
    dev_tso_job = run_vep(
        project_id, dev_tso_folder, dev_config_id,
        tso_vcf_id, tso_bed_id, update_folder
    )
    # Run on Prod TWE VCF
    prod_twe_folder = "clinvar_testing_prod_twe"
    prod_twe_job = run_vep(
        project_id, prod_twe_folder, prod_config_id,
        twe_vcf_id, twe_bed_id, update_folder
    )
    # Run on Prod TSO500 VCF
    prod_tso_folder = "clinvar_testing_prod_tso500"
    prod_tso_job = run_vep(
        project_id, prod_tso_folder, prod_config_id,
        tso_vcf_id, tso_bed_id, update_folder
    )

    # Wait until jobs have finished
    job_list = [dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job]
    for job in job_list:
        job.wait_on_done()

    # Add job IDs to report text file
    job_report = make_job_report(
        dev_twe_job.describe().get("id"),
        dev_tso_job.describe().get("id"),
        prod_twe_job.describe().get("id"),
        prod_tso_job.describe().get("id"),
        "./temp/job_report.txt"
    )

    # parse VEP run output vcf using bcftools
    dev_twe_output = parse_vep_output(
        project_id, dev_twe_folder, "dev_twe", update_folder
    )
    dev_tso_output = parse_vep_output(
        project_id, dev_tso_folder, "dev_tso500", update_folder
    )
    prod_twe_output = parse_vep_output(
        project_id, prod_twe_folder, "prod_twe", update_folder
    )
    prod_tso_output = parse_vep_output(
        project_id, prod_tso_folder, "prod_tso500", update_folder
    )

    # Perform comparison of differences when using prod vs. dev
    # Get diff for twe
    twe_diff_filename = get_diff_output(
        prod_twe_output, dev_twe_output, "twe", bin_folder
    )
    # Get diff for tso500
    tso_diff_filename = get_diff_output(
        prod_tso_output, dev_tso_output, "tso500", bin_folder
    )

    # Get detailed table of differences for twe and tso500
    (added_csv, deleted_csv, changed_csv, detailed_csv) = (
        compare_annotation(
            twe_diff_filename, tso_diff_filename, bin_folder
        )
    )

    return added_csv, deleted_csv, changed_csv, detailed_csv, job_report


def parse_vep_output(project_id, folder, label, update_folder) -> str:
    """parses output from running vep and returns path to processed output

    Args:
        project_id (str): DNAnexus project ID for 003 dev project
        folder (str): folder name to output to in current update folder
        label (str): label for naming the end of the output file
        update_folder (str): path to folder in 003 project for current update

    Raises:
        RuntimeError: Folder not found in project
        IOError: Input vcf file not found

    Returns:
        str: path to parsed vep output
    """
    # Download files output from vep
    folder_path = f"{update_folder}/{folder}"
    if not check_proj_folder_exists(project_id, folder_path):
        raise RuntimeError(f"Folder {folder_path} not found in {project_id}")
    download_folder(
        project_id, f"temp/{label}", folder=folder_path, overwrite=True
    )

    # Parse the variant and ClinVar annotation fields
    glob_path = f"temp/{label}/*.vcf.gz"
    vcf_input_path = ""
    try:
        vcf_input_path = glob.glob(glob_path)[0]
    except IndexError:
        raise IOError(f"File matching glob {glob_path} not found")
    vcf_output_path = f"temp/parsed_vcf_{label}.txt"
    vcf_reader = vcfpy.Reader.from_path(vcf_input_path)

    with open(vcf_output_path, "w") as file:
        for record in vcf_reader:
            csq_fields = (record.INFO["CSQ"][0]).split("|")
            info = "."
            if len(csq_fields) < 5:
                raise RuntimeError("VEP output vcf has invalid format")
            if csq_fields[4] != "":
                info = csq_fields[4]

            new_record = (
                f"{record.CHROM}:{record.POS}:{record.REF}:"
                + f"{record.ALT[0].value} {csq_fields[2]} {csq_fields[3]}"
                + f" {info}\n"
            )
            file.write(new_record)

    return vcf_output_path


def get_diff_output(dev_output, prod_output, label, bin_folder) -> str:
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
    output_file = f"temp/{label}_diff_output.txt"
    diff_input = [
        "sh", f"{bin_folder}/get_diff.sh", dev_output, prod_output,
        output_file
    ]
    subprocess.run(diff_input, stderr=subprocess.STDOUT)

    return output_file


def make_job_report(
    dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job, path
) -> str:
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
            file.write(f"Development TWE job: {dev_twe_job}\n")
            file.write(f"Development TSO500 job: {dev_tso_job}\n")
            file.write(f"Production TWE job: {prod_twe_job}\n")
            file.write(f"Production TSO500 job: {prod_tso_job}\n")
    except FileNotFoundError:
        print(
            f"The directory for saving the job report {path} does not exist"
        )
    except FileExistsError:
        print(
            f"The file {path} already exists and job report cannot be saved"
        )

    return path


def run_vep(
    project_id, project_folder, config_file, vcf_file, panel_bed_file,
    update_folder
) -> dxpy.bindings.DXJob:
    """runs the DNAnexus app vep

    Args:
        project_id (str): DNAnexus project ID for 003 dev project
        project_folder (str): DNAnexus folder name to run vep in
        config_file (str): DNAnexus file ID for vep config file
        vcf_file (str): DNAnexus file ID for vep vcf file
        panel_bed_file (str): DNAnexus file ID for vep panel bed file
        update_folder (str): DNAnexus folder in 003 project for current update

    Returns:
        dxpy.bindings.DXJob: DNAnexus job for vep run
    """
    inputs = {
        "config_file": {'$dnanexus_link': config_file},
        "vcf": {'$dnanexus_link': vcf_file},
        "panel_bed": {'$dnanexus_link': panel_bed_file}
    }

    folder_path = f"/{update_folder}/{project_folder}"

    job = dxpy.bindings.dxapp.DXApp(name="eggd_vep").run(
        app_input=inputs, project=project_id,
        folder=folder_path, priority='high'
    )

    return job


def get_recent_vep_vcf_bed(
    assay, ref_proj_id, genome_build
) -> tuple[str, str]:
    """gets most recent vcf and panel bed files in use for given assay

    Args:
        assay (str): name of assay
        ref_proj_id (str): DNAnexus project ID of reference project
        genome_build (str): build of genome

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
        folder_bed = f"/bed_files/{genome_build}/kits/tso500"
        vcf_name = "*Hotspots.vcf.gz"
    else:
        folder_bed = f"/bed_files/{genome_build}/kits/twist_exome"
        vcf_name = "*_markdup_recalibrated_Haplotyper.vcf.gz"

    bed_name = "*.bed"
    vcf = bed = ""

    for index, row in df.iterrows():
        # attempt to find vcf and bed files
        try:
            project_id = row["id"]
            # final all vcf files matching name glob and pick first
            vcf = find_dx_file(project_id, "", vcf_name, False)
            break
        except IOError:
            pass

    if vcf == "":
        raise IOError(
            f"VCF file not found in recent 002 project for assay {assay}"
        )

    try:
        bed = find_dx_file(ref_proj_id, folder_bed, bed_name, False)
    except IOError:
        pass

    if bed == "":
        raise IOError(
            f"Panel bed file not found in 001 ref project for assay {assay}"
        )

    return vcf, bed
