import dxpy
from subprocess import check_output
from subprocess import run
import glob
import compareAnnotation

def perform_vep_testing(project_id, dev_config_id, prod_config_id):
    # TODO: automatically get recent vcf files for twe and tso500. Should also get bed file ID
    # must be from most recent 002 project that is not archived and contains vcf and bed files
    # Also check with Jethro for recent 002 folder structure
    twe_vcf_id = "file-GPJ4xzQ4BG0j66gZyGZX2Bb2"
    tso_vcf_id = "file-GPgfQpQ4vbbBjvJ6XX89Q35q"
    twe_bed_id = "file-G2V8k90433GVQ7v07gfj0ggX"
    tso_bed_id = "file-G4F6jX04ZFVV3JZJG62ZQ5yJ"

    # Run on Dev TWE VCF
    dev_twe_folder = "clinvar_testing_dev_twe"
    dev_twe_job = run_vep(project_id, dev_twe_folder, dev_config_id, twe_vcf_id, twe_bed_id)
    # Run on Dev TSO500 VCF
    dev_tso_folder = "clinvar_testing_dev_tso500"
    dev_tso_job = run_vep(project_id, dev_tso_folder, dev_config_id, tso_vcf_id, tso_bed_id)
    # Run on Prod TWE VCF
    prod_twe_folder = "clinvar_testing_prod_twe"
    prod_twe_job = run_vep(project_id, prod_twe_folder, prod_config_id, twe_vcf_id, twe_bed_id)
    # Run on Prod TSO500 VCF
    prod_tso_folder = "clinvar_testing_prod_tso500"
    prod_tso_job = run_vep(project_id, prod_tso_folder, prod_config_id, tso_vcf_id, tso_bed_id)

    # Add job IDs to report text file
    job_report = make_job_report(dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job)

    # parse VEP run output vcf using bcftools
    dev_twe_output = parse_vep_output(project_id, dev_twe_folder, "dev_twe")
    dev_tso_output = parse_vep_output(project_id, dev_tso_folder, "dev_tso500")
    prod_twe_output = parse_vep_output(project_id, prod_twe_folder, "prod_twe")
    prod_tso_output = parse_vep_output(project_id, prod_tso_folder, "prod_tso500")

    # Perform comparison of differences when using dev vs. prod
    # Get diff for twe
    twe_diff = get_diff_output(dev_twe_output, prod_twe_output)
    # Get diff for tso500
    tso_diff = get_diff_output(dev_tso_output, prod_tso_output)

    # Get detailed table of differences for twe and tso500
    added_csv, deleted_csv, changed_csv = compareAnnotation.compare_annotation(twe_diff, tso_diff)

    return added_csv, deleted_csv, changed_csv, twe_diff, tso_diff, job_report

def parse_vep_output(project_id, folder, label):
    # Download files locally
    dxpy.bindings.dxfile_functions.download_folder(project_id, ".", folder="/" + folder)

    # Use bcftools to parse the variant and ClinVar annotation fields
    run("sh", "nextflow-bin/parse.sh", folder + "/*.vcf", label)

    # find results output by parse
    filename = glob.glob("*.vcf.{}.txt".format(label))

    return filename

def get_diff_output(dev_output, prod_output):
    # run diff
    diff_output = check_output("diff", "--suppress-common-lines", "--color=always", dev_output, prod_output)

    return diff_output

def make_job_report(dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job, path) -> str:
    try:
        with open(path, "w") as file:
            file.write("Development TWE job: {}\n".format(dev_twe_job))
            file.write("Development TSO500 job: {}\n".format(dev_tso_job))
            file.write("Production TWE job: {}\n".format(prod_twe_job))
            file.write("production TSO500 job: {}\n".format(prod_tso_job))
    except FileNotFoundError:
        print("The directory for saving the job report ({}) does not exist".format(path))
    except FileExistsError:
        print("The file ({}) already exists and job report cannot be saved".format(path))

    return path

def run_vep(project_id, project_folder, config_file, vcf_file, panel_bed_file):
    inputs = {
        "config_file" : config_file,
        "vcf" : vcf_file,
        "panel_bed" : panel_bed_file
    }

    job = dxpy.bindings.dxapp.DXApp(name="eggd_vep").run(
                app_input=inputs,
                project=project_id,
                folder="/" + project_folder,
                priority='high'
            )

    job_id = job.describe().get('id')

    return job_id
