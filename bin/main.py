"""
Runs prometheus
This program is to be run on a DNAnexus node once a week as new clinvar updates come in
"""

import getClinvarFiles
import makeVepTestConfigs as vep
import vepTesting
import deployer
import json
import loginHandler
import slackHandler

def run_prometheus():
    # load config files
    ref_proj_id, dev_proj_id, slack_channel = load_config()
    login_handler = loginHandler()
    login_handler.login_DNAnexus()
    login_handler.login_slack()

    # Step 1 - Fetch latest ClinVar files and add to new 003 project
    print("Fetching latest ClinVar annotation resource files")
    recent_vcf_file, recent_tbi_file, earliest_time, clinvar_version = getClinvarFiles.get_ftp_files()
    print("Downloading the clinvar annotation resource files {1} and {2} from {3}".format(recent_vcf_file,
    recent_tbi_file, earliest_time))
    project_id, clinvar_vcf_id, clinvar_tbi_id = getClinvarFiles.retrieve_clinvar_files(recent_vcf_file, recent_tbi_file, clinvar_version)

    # Step 2 - Make dev and prod VEP config files from template and store local paths
    print("Creating development and production config files from template")
    vep_config_dev, vep_config_prod = vep.generate_config_files(clinvar_version, clinvar_vcf_id, clinvar_tbi_id, project_id)

    # Step 3 - Run vep for dev and prod configs, find differences, get evidence of changes
    print("Running vep for development and production configs")
    added_csv, deleted_csv, changed_csv, job_report = vepTesting.perform_vep_testing(project_id, vep_config_dev, vep_config_prod)

    # step 4 - upload .csv files to DNAnexus
    print("Documenting testing on DNAnexus")
    deployer.deploy_testing_to_development(dev_proj_id, clinvar_version, added_csv, deleted_csv, changed_csv, job_report)

    # Step 5 - deploy clinvar file to 001
    print("Deploying clinvar files to 001 reference project")
    deployer.deploy_clinvar_to_production(ref_proj_id, recent_vcf_file, recent_tbi_file)

    # Step 6 - announce update to team
    slack_handler = slackHandler(login_handler.slack_token)
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
