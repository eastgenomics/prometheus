import dxpy
import subprocess
import glob
import compare_annotation

from utils import check_jobs_finished

def perform_vep_testing(project_id, dev_config_id, prod_config_id, clinvar_version, bin_folder):
    # TODO: automatically get recent vcf files for twe and tso500. Should also get bed file ID
    # must be from most recent 002 project that is not archived and contains vcf and bed files
    # Also check with Jethro for recent 002 folder structure
    twe_vcf_id = "file-GPJ4xzQ4BG0j66gZyGZX2Bb2"
    tso_vcf_id = "file-GXB0qxj47QVbX6Gz507Fz7Yx"
    twe_bed_id = "file-G2V8k90433GVQ7v07gfj0ggX"
    tso_bed_id = "file-G4F6jX04ZFVV3JZJG62ZQ5yJ"

    update_folder = "ClinVar_version_{}_annotation_resource_update".format(clinvar_version)

    # Run on Dev TWE VCF
    dev_twe_folder = "clinvar_testing_dev_twe"
    dev_twe_job = run_vep(project_id, dev_twe_folder, dev_config_id, twe_vcf_id, twe_bed_id, update_folder)
    # Run on Dev TSO500 VCF
    dev_tso_folder = "clinvar_testing_dev_tso500"
    dev_tso_job = run_vep(project_id, dev_tso_folder, dev_config_id, tso_vcf_id, tso_bed_id, update_folder)
    # Run on Prod TWE VCF
    prod_twe_folder = "clinvar_testing_prod_twe"
    prod_twe_job = run_vep(project_id, prod_twe_folder, prod_config_id, twe_vcf_id, twe_bed_id, update_folder)
    # Run on Prod TSO500 VCF
    prod_tso_folder = "clinvar_testing_prod_tso500"
    prod_tso_job = run_vep(project_id, prod_tso_folder, prod_config_id, tso_vcf_id, tso_bed_id, update_folder)

    # Pause until jobs have finished
    job_list = [dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job]
    check_jobs_finished(job_list, 2, 20)

    # Add job IDs to report text file
    job_report = make_job_report(dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job, "./temp/job_report.txt")

    # parse VEP run output vcf using bcftools
    dev_twe_output = parse_vep_output(project_id, dev_twe_folder, "dev_twe", update_folder, bin_folder)
    dev_tso_output = parse_vep_output(project_id, dev_tso_folder, "dev_tso500", update_folder, bin_folder)
    prod_twe_output = parse_vep_output(project_id, prod_twe_folder, "prod_twe", update_folder, bin_folder)
    prod_tso_output = parse_vep_output(project_id, prod_tso_folder, "prod_tso500", update_folder, bin_folder)

    # Perform comparison of differences when using dev vs. prod
    # Get diff for twe
    twe_diff_filename = get_diff_output(dev_twe_output, prod_twe_output, "twe", bin_folder)
    # Get diff for tso500
    tso_diff_filename = get_diff_output(dev_tso_output, prod_tso_output, "tso500", bin_folder)

    # Get detailed table of differences for twe and tso500
    added_csv, deleted_csv, changed_csv = compare_annotation.compare_annotation(twe_diff_filename, tso_diff_filename)

    return added_csv, deleted_csv, changed_csv, job_report

def parse_vep_output(project_id, folder, label, update_folder, bin_folder):
    folder_path = "/{0}/{1}".format(update_folder, folder)

    # Download files locally
    # TODO: check that folder exists before downloading. Handle error if folder not found
    dxpy.bindings.dxfile_functions.download_folder(project_id, "temp/{}".format(label), folder=folder_path, overwrite=True)

    # Use bcftools to parse the variant and ClinVar annotation fields
    #subprocess.run(["sh", "nextflow-bin/parse.sh", "temp/{}".format(label) + "/*.vcf", label])
    # TODO: uncomment above line to run as applet
    subprocess.run(["sh", "{}/parse.sh".format(bin_folder), "temp/{}".format(label) + "/*.vcf.gz", label, "temp/"])

    # find results output by parse and take first match (there should only be 1 matching file)
    glob_path = "temp/" + "*.vcf.gz.{}.txt".format(label)

    filename = ""

    try:
        filename = glob.glob(glob_path)[0]
    except IndexError:
        print("Error: cannot find file at: {}".format(glob_path))

    return filename

def get_diff_output(dev_output, prod_output, label, bin_folder):
    # run diff
    output_file = "temp/{}_diff_output.txt".format(label)
    # TODO: switch to nextflow-bin for use as a nextflow script
    diff_input = ["sh", "{}/get_diff.sh".format(bin_folder), dev_output, prod_output, output_file]
    subprocess.run(diff_input, stderr=subprocess.STDOUT)

    return output_file

def make_job_report(dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job, path) -> str:
    try:
        with open(path, "w") as file:
            file.write("Development TWE job: {}\n".format(dev_twe_job))
            file.write("Development TSO500 job: {}\n".format(dev_tso_job))
            file.write("Production TWE job: {}\n".format(prod_twe_job))
            file.write("Production TSO500 job: {}\n".format(prod_tso_job))
    except FileNotFoundError:
        print("The directory for saving the job report ({}) does not exist".format(path))
    except FileExistsError:
        print("The file ({}) already exists and job report cannot be saved".format(path))

    return path

def run_vep(project_id, project_folder, config_file, vcf_file, panel_bed_file, update_folder):
    inputs = {
        "config_file" : {'$dnanexus_link': config_file},
        "vcf" : {'$dnanexus_link': vcf_file},
        "panel_bed" : {'$dnanexus_link': panel_bed_file}
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
