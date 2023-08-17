"""
Runs prometheus
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import json
import logging

from get_clinvar_files import get_ftp_files, retrieve_clinvar_files
import make_vep_test_configs as vep
import vep_testing
import deployer
from login_handler import LoginHandler
from slack_handler import SlackHandler


def run_prometheus(bin_folder):
    """runs all steps of prometheus

    Args:
        bin_folder (str): folder scripts are run from
    """
    logger = logging.getLogger("main log")

    # load config files
    ref_proj_id, dev_proj_id, slack_channel = load_config()
    login_handler = LoginHandler()
    login_handler.login_DNAnexus()

    # Step 1 - Fetch latest ClinVar files and add to new 003 project
    logger.info("Fetching latest ClinVar annotation resource files")
    (recent_vcf_file,
     recent_tbi_file,
     earliest_time,
     clinvar_version) = get_ftp_files()
    logger.info("Downloading the clinvar annotation resource files "
                + "{} and {} from {}".format(recent_vcf_file, recent_tbi_file,
                                             earliest_time))
    genome_build = "b37"
    clinvar_vcf_id, clinvar_tbi_id = retrieve_clinvar_files(dev_proj_id,
                                                            recent_vcf_file,
                                                            recent_tbi_file,
                                                            clinvar_version,
                                                            genome_build)

    # Step 2 - Make dev and prod VEP config files from template
    # and store local paths
    logger.info("Creating development and production "
                + "config files from template")
    (vep_config_dev,
     vep_config_prod) = vep.generate_config_files(clinvar_version,
                                                  clinvar_vcf_id,
                                                  clinvar_tbi_id,
                                                  dev_proj_id,
                                                  ref_proj_id)

    # Step 3 - Run vep for dev and prod configs,
    # find differences, and get evidence of changes
    logger.info("Running vep for development and production configs")
    (added_csv,
     deleted_csv,
     changed_csv,
     job_report) = vep_testing.perform_vep_testing(dev_proj_id,
                                                   vep_config_dev,
                                                   vep_config_prod,
                                                   clinvar_version,
                                                   bin_folder)

    # step 4 - upload .csv files to DNAnexus
    logger.info("Documenting testing on DNAnexus")
    deployer.deploy_testing_to_development(dev_proj_id, clinvar_version,
                                           added_csv, deleted_csv,
                                           changed_csv, job_report)

    # Step 5 - deploy clinvar file to 001
    logger.info("Deploying clinvar files to 001 reference project")
    b37_folder = "/annotation/b37/clinvar"
    deployer.deploy_clinvar_to_production(ref_proj_id, dev_proj_id,
                                          clinvar_vcf_id, clinvar_tbi_id,
                                          b37_folder)

    # Step 6 - announce update to team
    slack_handler = SlackHandler(login_handler.slack_token)
    slack_handler.announce_clinvar_update(slack_channel, recent_vcf_file,
                                          earliest_time)


def load_config():
    """loads config file

    Returns:
        ref_proj_id: str
            DNAnexus project ID for 001 reference project
        dev_proj_id: str
            DNAnexus project ID for 003 development project
        slack_channel: str
            Slack API token
    """
    with open("resources/config.json", "r", encoding="utf8") as json_file:
        config = json.load(json_file)

    ref_proj_id = config.get('001_REFERENCE_PROJ_ID')
    dev_proj_id = config.get('003_DEV_CLINVAR_UPDATE_PROJ_ID')
    slack_channel = config.get('SLACK_CHANNEL')

    return ref_proj_id, dev_proj_id, slack_channel


if __name__ == "__main__":
    # TODO: send either "bin" or "nextflow-bin" from nextflow script depending
    # on where program is run
    # This will either be "bin" for local, or "nextflow-bin" for running it as
    # a DNAnexus app/applet
    run_prometheus("bin")
