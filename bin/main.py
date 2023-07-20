"""
Runs prometheus
This program is to be run on a DNAnexus node once a week as new clinvar updates come in
"""

import get_clinvar_files as get_clinvar_files
import make_vep_test_configs as vep
import vep_testing
import deployer
import json
from login_handler import LoginHandler
from slack_handler import SlackHandler

def run_prometheus():
    # load config files
    ref_proj_id, dev_proj_id, slack_channel = load_config()
    login_handler = LoginHandler()
    login_handler.login_DNAnexus()
    login_handler.login_slack()

    # Step 1 - Fetch latest ClinVar files and add to new 003 project
    print("Fetching latest ClinVar annotation resource files")
    recent_vcf_file, recent_tbi_file, earliest_time, clinvar_version = get_clinvar_files.get_ftp_files()
    print("Downloading the clinvar annotation resource files {0} and {1} from {2}".format(recent_vcf_file,
    recent_tbi_file, earliest_time))
    download_dir = "./downloads"
    clinvar_vcf_id, clinvar_tbi_id = get_clinvar_files.retrieve_clinvar_files(dev_proj_id, 
        download_dir, recent_vcf_file, recent_tbi_file, clinvar_version)

    # Step 2 - Make dev and prod VEP config files from template and store local paths
    print("Creating development and production config files from template")
    vep_config_dev, vep_config_prod = vep.generate_config_files(clinvar_version, clinvar_vcf_id, clinvar_tbi_id, dev_proj_id, ref_proj_id)

    # Step 3 - Run vep for dev and prod configs, find differences, get evidence of changes
    print("Running vep for development and production configs")
    added_csv, deleted_csv, changed_csv, job_report = vep_testing.perform_vep_testing(dev_proj_id, vep_config_dev, vep_config_prod, clinvar_version)

    # step 4 - upload .csv files to DNAnexus
    print("Documenting testing on DNAnexus")
    deployer.deploy_testing_to_development(dev_proj_id, clinvar_version, added_csv, deleted_csv, changed_csv, job_report)

    # Step 5 - deploy clinvar file to 001
    print("Deploying clinvar files to 001 reference project")
    deployer.deploy_clinvar_to_production(ref_proj_id, dev_proj_id, clinvar_vcf_id, clinvar_tbi_id)

    # Step 6 - announce update to team
    slack_handler = SlackHandler(login_handler.slack_token)
    slack_handler.announce_clinvar_update(slack_channel, recent_vcf_file, earliest_time)

def load_config():
    with open("resources/config.json", "r", encoding="utf8") as json_file:
        config = json.load(json_file)

    ref_proj_id = config.get('001_REFERENCE_PROJ_ID')
    dev_proj_id = config.get('003_DEV_CLINVAR_UPDATE_PROJ_ID')
    slack_channel = config.get('SLACK_CHANNEL')

    return ref_proj_id, dev_proj_id, slack_channel

if __name__ == "__main__":
    run_prometheus()
