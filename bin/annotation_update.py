"""
Runs prometheus ClinVar annotation resource update
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import logging
import sys

from get_clinvar_files import get_ftp_files, retrieve_clinvar_files
import make_vep_test_configs as vep
import vep_testing
import deployer
from login_handler import LoginHandler
from slack_handler import SlackHandler
from progress_tracker import ClinvarProgressTracker as Tracker
from utils import load_config

logger = logging.getLogger("main log")


def run_annotation_update(bin_folder, genome_build):
    """runs all steps of prometheus ClinVar annotation resource update

    Args:
        bin_folder (str): folder scripts are run from
    """
    # load config files and log into websites
    ref_proj_id, dev_proj_id, slack_channel = load_config()
    login_handler = LoginHandler()
    login_handler.login_DNAnexus(dev_proj_id)
    slack_handler = SlackHandler(login_handler.slack_token)

    # check which clinvar version is most recent
    logger.info("Fetching latest ClinVar annotation resource files")
    (recent_vcf_file,
     recent_tbi_file,
     earliest_time,
     clinvar_version) = get_ftp_files()
    update_folder = ("/ClinVar_version_{}_annotation_resource_update"
                     .format(clinvar_version))
    genome_build_folder = "/annotation/{}/clinvar".format(genome_build)

    # check if any steps have already been completed
    tracker = Tracker(dev_proj_id, ref_proj_id, update_folder,
                      genome_build_folder, genome_build, clinvar_version)
    tracker.perform_checks()

    # Step 1 - Fetch latest ClinVar files and add to new 003 project
    if not tracker.clinvar_fetched:
        logger.info("Downloading the clinvar annotation resource files "
                    + "{} and {} from {}".format(recent_vcf_file,
                                                 recent_tbi_file,
                                                 earliest_time))
        (clinvar_vcf_id,
         clinvar_tbi_id) = retrieve_clinvar_files(dev_proj_id,
                                                  recent_vcf_file,
                                                  recent_tbi_file,
                                                  clinvar_version,
                                                  genome_build)
    else:
        clinvar_vcf_id = tracker.clinvar_vcf_id
        clinvar_tbi_id = tracker.clinvar_tbi_id
        logger.info("The clinvar annotation resource files "
                    + "{} and {} from {}".format(recent_vcf_file,
                                                 recent_tbi_file,
                                                 earliest_time)
                    + " have already been downloaded")

    # Verification that step 1 has been completed
    tracker.check_clinvar_fetched()
    if not tracker.clinvar_fetched:
        raise Exception("ClinVar files were not downloaded to DNAnexus")

    # Step 2 - Make dev and prod VEP config files from template
    # and store local paths
    if not tracker.configs_made:
        logger.info("Creating development and production "
                    + "config files from template")
        (vep_config_dev,
         vep_config_prod) = vep.generate_config_files(clinvar_version,
                                                      clinvar_vcf_id,
                                                      clinvar_tbi_id,
                                                      dev_proj_id,
                                                      ref_proj_id)
    else:
        vep_config_dev = tracker.vep_config_dev
        vep_config_prod = tracker.vep_config_prod
        logger.info("Development and production "
                    + "config files already created")

    # Verification that step 2 has been completed
    tracker.check_configs_made()
    if not tracker.configs_made:
        raise Exception("Config files were not uploaded to DNAnexus")

    # Step 3 - Run vep for dev and prod configs,
    # find differences, and get evidence of changes
    if not tracker.evidence_uploaded:
        logger.info("Running vep for development and production configs")
        (added_csv,
         deleted_csv,
         changed_csv,
         detailed_csv,
         job_report) = vep_testing.vep_testing_annotation(dev_proj_id,
                                                          vep_config_dev,
                                                          vep_config_prod,
                                                          clinvar_version,
                                                          bin_folder,
                                                          ref_proj_id,
                                                          genome_build)

        # step 4 - upload .csv files to DNAnexus
        logger.info("Documenting testing on DNAnexus")
        deployer.deploy_testing_to_development(dev_proj_id, clinvar_version,
                                               added_csv, deleted_csv,
                                               changed_csv, detailed_csv,
                                               job_report)
    else:
        logger.info("Clinvar VEP evidence already uploaded to DNAnexus")

    # Verification that steps 3 and 4 have been completed
    tracker.check_evidence_uploaded()
    if not tracker.evidence_uploaded:
        raise Exception("Evidence not uploaded to DNAnexus")

    # verify that the changes between dev and prod config files pass checks
    if tracker.changes_status == Tracker.STATUS_UNCHECKED:
        tracker.check_changes_status()
        if tracker.changes_status == Tracker.STATUS_PASSED:
            logger.info("Clinvar changes passed checks")
        elif tracker.changes_status == Tracker.STATUS_REVIEW:
            announce_manual_check(slack_handler, slack_channel,
                                  dev_proj_id, update_folder)
        else:
            Exception("Clinvar changes status could not be checked")
    elif tracker.changes_status == Tracker.STATUS_PASSED:
        logger.info("Clinvar changes passed checks")
    elif tracker.changes_status == Tracker.STATUS_REVIEW:
        announce_manual_check(slack_handler, slack_channel,
                              dev_proj_id, update_folder)

    # Step 5 - deploy clinvar file to 001
    if not tracker.clinvar_deployed:
        logger.info("Deploying clinvar files to 001 reference project")
        deployer.deploy_clinvar_to_production(ref_proj_id, dev_proj_id,
                                              clinvar_vcf_id, clinvar_tbi_id,
                                              genome_build_folder)
    else:
        logger.info("Clinvar files already deployed to 001 reference project")

    # Verification that step 5 has been completed
    tracker.check_clinvar_deployed()
    if not tracker.clinvar_deployed:
        raise Exception("Clinvar files not deployed to 001 reference project")

    # Step 6 - announce update to team
    vcf_name = ("clinvar_{}_{}.vcf.gz"
                .format(clinvar_version, genome_build))
    slack_handler.announce_clinvar_update(slack_channel, vcf_name,
                                          earliest_time, genome_build)


def announce_manual_check(slack_handler, channel, dev_project, update_folder):
    """announces that manual check of evidence files must be performed

    Args:
        slack_handler (SlackHandler): slack handler for Prometheus
        channel (str): name of slack channel to post message to
        dev_project (str): DNAnexus project ID for dev project
        update_folder (str): DNAnexus folder path for current update folder
    """
    # send slack message announcing manual check must be made for evidence
    slack_handler.send_message(channel,
                               "Latest ClinVar annotation resource file update"
                               + " awaiting manual review in DNAnexus project"
                               + " {} folder {}".format(dev_project,
                                                        update_folder))
    exit_prometheus()


def exit_prometheus():
    """safely exits Prometheus
    """
    logger.info("Exiting prometheus")
    exit()


if __name__ == "__main__":
    # Send either "bin" or "nextflow-bin" from nextflow script depending
    # on where program is run
    # This will either be "bin" for local, or "nextflow-bin" for running it as
    # a DNAnexus app/applet

    # validate arguments
    if len(sys.argv) < 3:
        logger.error("2 command line args are required"
                     + " to run annotation_update.py"
                     + " but {} were provided".format(len(sys.argv)))
        exit_prometheus()

    run_annotation_update(sys.argv[1], sys.argv[2])
