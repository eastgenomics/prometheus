"""
Runs prometheus ClinVar annotation resource update
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import logging
import sys
import os

from annotation.get_clinvar_files import (
    get_ftp_files, retrieve_clinvar_files
)
from annotation.make_vep_test_configs import generate_config_files
from util.vep_testing import vep_testing_annotation
from util.deployer import (
    deploy_testing_to_development, deploy_clinvar_to_production
)
from util.login_handler import LoginHandler
from util.slack_handler import SlackHandler
from util.progress_tracker import ClinvarProgressTracker as Tracker
from util.utils import load_config

logger = logging.getLogger("main log")


def run_annotation_update(
        bin_folder, genome_build, config_path, creds_path) -> None:
    """runs all steps of prometheus ClinVar annotation resource update

    Args:
        bin_folder (str): folder scripts are run from
        genome_build (str): build of genome used e.g., b38
        config_path (str): path to config file
        creds_path (str): path to credentials file
    """
    # make temp dir
    os.makedirs("temp", exist_ok=True)
    # load config files and log into websites
    (
        ref_proj_id, dev_proj_id, slack_channel, base_vcf_link, base_vcf_path
    ) = load_config(bin_folder, config_path)
    login_handler = LoginHandler(bin_folder, creds_path)
    login_handler.login_DNAnexus(dev_proj_id)
    slack_handler = SlackHandler(login_handler.slack_token)

    # check which clinvar version is most recent
    logger.info("Fetching latest ClinVar annotation resource files")
    (
        recent_vcf_file, recent_tbi_file, earliest_time, clinvar_version
    ) = get_ftp_files(base_vcf_link, base_vcf_path, genome_build)
    update_folder = (
        f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
    )
    genome_build_folder = f"/annotation/{genome_build}/clinvar"

    # check if any steps have already been completed
    tracker = Tracker(
        dev_proj_id, ref_proj_id, update_folder, genome_build_folder,
        genome_build, clinvar_version
    )
    tracker.perform_checks()

    # Step 1 - Fetch latest ClinVar files and add to new 003 project
    if not tracker.clinvar_fetched:
        logger.info(
            "Downloading the clinvar annotation resource files "
            + f"{recent_vcf_file} and {recent_tbi_file} from {earliest_time}"
        )
        full_clinvar_link = base_vcf_link + base_vcf_path
        (clinvar_vcf_id,
         clinvar_tbi_id) = retrieve_clinvar_files(
            dev_proj_id, recent_vcf_file, recent_tbi_file,
            clinvar_version, genome_build, full_clinvar_link
        )
    else:
        clinvar_vcf_id = tracker.clinvar_vcf_id
        clinvar_tbi_id = tracker.clinvar_tbi_id
        logger.info(
            "The clinvar annotation resource files "
            + f"{recent_vcf_file} and {recent_tbi_file}"
            + f" from {earliest_time} have already been downloaded"
        )

    # Verification that step 1 has been completed
    tracker.check_clinvar_fetched()
    if not tracker.clinvar_fetched:
        error_message = "Error: ClinVar files were not downloaded to DNAnexus"
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Step 2 - Make dev and prod VEP config files from template
    # and store local paths
    if not tracker.configs_made:
        logger.info(
            "Creating development and production config files from template"
        )
        (vep_config_dev,
         vep_config_prod) = generate_config_files(
            clinvar_version, clinvar_vcf_id, clinvar_tbi_id,
            dev_proj_id, ref_proj_id, bin_folder, genome_build)
    else:
        vep_config_dev = tracker.vep_config_dev
        vep_config_prod = tracker.vep_config_prod
        logger.info(
            "Development and production config files already created"
        )

    # Verification that step 2 has been completed
    tracker.check_configs_made()
    if not tracker.configs_made:
        error_message = "Error: Config files were not uploaded to DNAnexus"
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Step 3 - Run vep for dev and prod configs,
    # find differences, and get evidence of changes
    if not tracker.evidence_uploaded:
        logger.info("Running vep for development and production configs")
        (added_csv,
         deleted_csv,
         changed_csv,
         detailed_csv,
         job_report) = vep_testing_annotation(
            dev_proj_id, vep_config_dev, vep_config_prod,
            clinvar_version, bin_folder, ref_proj_id, genome_build
        )

        # step 4 - upload .csv files to DNAnexus
        logger.info("Documenting testing on DNAnexus")
        deploy_testing_to_development(
            dev_proj_id, clinvar_version, added_csv, deleted_csv,
            changed_csv, detailed_csv, job_report)
    else:
        logger.info("Clinvar VEP evidence already uploaded to DNAnexus")

    # Verification that steps 3 and 4 have been completed
    tracker.check_evidence_uploaded()
    if not tracker.evidence_uploaded:
        error_message = "Error: Evidence not uploaded to DNAnexus"
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # verify that the changes between dev and prod config files pass checks
    if tracker.changes_status == Tracker.STATUS_UNCHECKED:
        tracker.check_changes_status()
        if tracker.changes_status == Tracker.STATUS_PASSED:
            logger.info("Clinvar changes passed checks")
        elif tracker.changes_status == Tracker.STATUS_REVIEW:
            announce_manual_check(
                slack_handler, slack_channel, dev_proj_id, update_folder
            )
        else:
            error_message = (
                "Error: Clinvar changes status could not be checked"
            )
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()
    elif tracker.changes_status == Tracker.STATUS_PASSED:
        logger.info("Clinvar changes passed checks")
    elif tracker.changes_status == Tracker.STATUS_REVIEW:
        announce_manual_check(
            slack_handler, slack_channel, dev_proj_id, update_folder
        )

    # Step 5 - deploy clinvar file to 001
    if not tracker.clinvar_deployed:
        logger.info("Deploying clinvar files to 001 reference project")
        deploy_clinvar_to_production(
            ref_proj_id, dev_proj_id, clinvar_vcf_id, clinvar_tbi_id,
            genome_build_folder
        )
    else:
        logger.info("Clinvar files already deployed to 001 reference project")

    # Verification that step 5 has been completed
    tracker.check_clinvar_deployed()
    if not tracker.clinvar_deployed:
        error_message = (
            "Error: Clinvar files not deployed to 001 reference project"
        )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Step 6 - announce update to team
    vcf_name = (f"clinvar_{clinvar_version}_{genome_build}.vcf.gz")
    slack_handler.announce_clinvar_update(
        slack_channel, vcf_name, earliest_time, genome_build
    )


def announce_manual_check(
        slack_handler, channel, dev_project, update_folder) -> None:
    """announces that manual check of evidence files must be performed

    Args:
        slack_handler (SlackHandler): slack handler for Prometheus
        channel (str): name of slack channel to post message to
        dev_project (str): DNAnexus project ID for dev project
        update_folder (str): DNAnexus folder path for current update folder
    """
    # send slack message announcing manual check must be made for evidence
    slack_handler.send_message(
        channel,
        ("Latest ClinVar annotation resource file update awaiting manual"
         + f" review in DNAnexus project {dev_project} folder {update_folder}")
        )
    exit_prometheus()


def exit_prometheus() -> None:
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
    num_args = len(sys.argv)
    if num_args < 5:
        logger.error(
            "5 command line args are required to run annotation_update.py"
            + f" but {num_args} were provided"
        )
        exit_prometheus()

    run_annotation_update(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
