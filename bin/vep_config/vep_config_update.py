"""
Runs prometheus ClinVar vep config update
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import logging
import dxpy
import os
import re
import glob
import sys

import util.vep_testing as vep_testing
import util.deployer as deployer
from util.login_handler import LoginHandler
from util.slack_handler import SlackHandler
from util.utils import (
    get_prod_version, load_config, load_config_repo, check_proj_folder_exists
)
from util.git_handler import GitHandler
import util.utils as utils
from util.progress_tracker import VepProgressTracker as Tracker

logger = logging.getLogger("main log")


def run_vep_config_update(
    bin_folder, assay, genome_build, config_path, creds_path
) -> None:
    """runs all steps in vep config update

    Args:
        bin_folder (str): folder scripts are run from
        assay (str): vep assay being updated
        genome_build (str): genome build used for update
        config_path (str): path to config file
        creds_path (str): path to credentials file
    """
    # make temp dir
    os.mkdir("temp", exist_ok=True)
    # load config files and log into websites
    ref_proj_id, dev_proj_id, slack_channel = load_config(
        bin_folder, config_path
    )
    assay_repo = load_config_repo(assay, bin_folder, config_path)
    login_handler = LoginHandler(bin_folder, creds_path)
    login_handler.login_DNAnexus(dev_proj_id)
    slack_handler = SlackHandler(login_handler.slack_token)

    # find latest clinvar name and ID from 001 reference project
    # check that update folder for this version exists in DNAnexus
    # make new vep update folder in overall update folder
    ref_clinvar_folder = f"/annotation/{genome_build}/clinvar/"
    (clinvar_version, vcf_id, index_id) = get_prod_version(
        ref_proj_id, ref_clinvar_folder, genome_build
    )
    clinvar_subfolder = (
        f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
    )
    if not check_proj_folder_exists(dev_proj_id, clinvar_subfolder):
        error_message = (
            "ClinVar annotation resource update folder"
            + f" for version {clinvar_version} does not exist"
        )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()
    config_subfolder = (
        f"/ClinVar_version_{clinvar_version}_vep_config_update_{assay}"
    )
    dev_project = dxpy.bindings.dxproject.DXProject(dxid=dev_proj_id)
    if not check_proj_folder_exists(dev_proj_id, config_subfolder):
        dev_project.new_folder(config_subfolder)

    # check if any steps have already been completed
    evidence_folder = f"{config_subfolder}/Evidence"
    deploy_folder = "/dynamic_files/vep_configs"
    tracker = Tracker(
        dev_proj_id, ref_proj_id, evidence_folder, deploy_folder,
        genome_build, clinvar_version, assay_repo, assay,
        login_handler.github_token, vcf_id)
    tracker.perform_checks()

    # download git repo for latest vep config for genome build and assay
    # check old clinvar version is less recent than new clinvar version
    # make branch on repo and switch to new branch
    # git mv to rename config with incremented version (e.g., v1.0.1 to v1.0.2)
    # replace old clinvar version with new version and increment version number
    # push repo to github
    # create pull request
    # merge pull request to main branch
    split_assay_url = assay_repo.split("/")
    repo_name = f"{split_assay_url[3]}/{split_assay_url[4]}"
    if not tracker.pr_merged:
        repo_dir = f"temp/vep_repo_{assay}"
        git_handler = GitHandler(
            repo_dir, repo_name, assay_repo, "main",
            login_handler.github_token
        )
        git_handler.pull_repo()

        # check if production clinvar files are already in config
        filename_glob = f"{repo_dir}/*_vep_config_v*.json"
        match_regex = r"\"name\": \"ClinVar\""
        file_id_regex = r"\"file_id\":\"(.*)\""
        is_different = utils.is_json_content_different(
            filename_glob, match_regex, file_id_regex, vcf_id
        )
        if not is_different:
            error_message = (
                "Error: The ClinVar vcf ID in the production"
                + f" {assay} VEP config is identical to the new ClinVar vcf ID"
                + f" {vcf_id}. Therefore, this config file does not need to be"
                + " updated"
            )
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()

        file_id_regex = r"\"index_id\":\"(.*)\""
        is_different = utils.is_json_content_different(
            filename_glob, match_regex, file_id_regex, index_id
        )
        if not is_different:
            error_message = (
                "Error: The ClinVar vcf index ID in the current"
                + " VEP config is identical to the new ClinVar"
                + f" vcf index ID {index_id}. Therefore, this"
                + " config file does not need to be updated"
            )
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()

        # switch to new branch
        branch_name = f"prometheus_dev_branch_{clinvar_version}"
        git_handler.make_branch(branch_name)
        git_handler.switch_branch(branch_name)
        # search through pulled dir, get old version, update to new
        repo_files = os.listdir(repo_dir)
        old_config = new_config = new_version = ""
        for file in repo_files:
            match = re.match(r"(.*_vep_config_v)(.*).json", file)
            if match:
                old_config = file
                version = match.group(2)
                split_version = version.split(".")
                new_version_end = str(int(split_version[2]) + 1)
                new_version = (f"{split_version[0]}.{split_version[1]}"
                               f".{new_version_end}")
                new_config = f"{match.group(1)}{new_version}.json"
                break
        if old_config == "":
            error_message = (
                "Error: No file matching config regex was found"
                + f" in repo for VEP config update for assay {assay}"
            )
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()
        git_handler.rename_file(
            f"temp/vep_repo_{assay}", old_config, new_config
        )
        # edit file contents to update version and config files
        filename_glob = f"{repo_dir}/*_vep_config_v*.json"
        match_regex = r"\"name\": \"ClinVar\""
        replace_regex = r"\"file_id\":\"(.*)\""
        utils.update_json(filename_glob, match_regex, replace_regex, vcf_id)
        replace_regex = r"\"index_id\":\"(.*)\""
        utils.update_json(filename_glob, match_regex, replace_regex, index_id)
        # replace version
        match_regex = r"\"config_information\":"
        replace_regex = r"\"config_version\": \"(.*)\""
        utils.update_json(filename_glob, match_regex, replace_regex, version)

        git_handler.add_file(new_config)
        commit_message = (
            "Updated clinvar file and index IDs and incremented"
            + f" version number for {assay} config file"
        )
        git_handler.commit_changes(commit_message)
        git_handler.make_branch_github(branch_name, "main")
        git_handler.push_to_remote()

        pr_title = (
            f"VEP config update for assay {assay} and"
            + f" clinvar annotation resource version {clinvar_version}"
            )
        pr_num = git_handler.make_pull_request(
            branch_name, "main", pr_title, commit_message
        )
        git_handler.merge_pull_request(pr_num)
        git_handler.exit_github()
    else:
        logger.info(
            f"The vep config file for assay {assay} has already been uploaded"
            + " to github and merged to the main branch"
        )

    # Verification that step 1 has been completed
    tracker.check_pr_merged()
    if not tracker.pr_merged:
        error_message = (
            f"Error: PR for vep config update for assay {assay} was not merged"
        )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # clone git repo to get latest config file for given assay
    # upload config file to DNAnexus
    # fetch a valid panel bed and vcf file to run VEP for a given assay
    # run vep using updated config file and record results to 003 project
    # test results automatically to ensure results are valid
    # output human readable evidence to 003 project
    # format of evidence is expected, pasted results, compariosn, pass/fail
    # fail, record evidence, exit prometheus, notify team if test fails
    if not tracker.evidence_uploaded:
        repo_dir = f"temp/prod_vep_repo_{assay}"
        git_handler = GitHandler(
            repo_dir, repo_name, assay_repo, "main",
            login_handler.github_token
        )
        updated_config = glob.glob(f"{repo_dir}/*_vep_config_*.json")[0]
        # upload to specific 003 test directory
        folder_path = f"{config_subfolder}/Testing"
        if not check_proj_folder_exists(dev_proj_id, folder_path):
            dev_project.new_folder(folder_path, parents=True)
        dev_config_id = (dxpy.upload_local_file(
            filename=updated_config, project=dev_proj_id, folder=folder_path
        ).describe().get('id'))
        try:
            vep_testing.vep_testing_config(
                dev_proj_id, dev_config_id, config_subfolder, ref_proj_id,
                assay, genome_build, vcf_id
            )
        except Exception:
            error_message = (
                f"Error: Vep config file for assay {assay}"
                + f" build {genome_build} took over max wait time"
                + " for DNAnexus vep job to complete"
            )
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()
        git_handler.exit_github()
    else:
        logger.info(
            f"The vep config file for assay {assay} has already been tested"
            + " and testing evidence uploaded to DNAnexus"
        )

    # Verification that testing has been uploaded to DNAnexus
    tracker.check_evidence_uploaded()
    if not tracker.evidence_uploaded:
        error_message = (
            "Error: Vep config testing evidence for"
            + f"assay {assay} was not uploaded to DNAnexus"
        )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Check if test passed or failed based on presence of DXFile
    if tracker.changes_status == Tracker.STATUS_UNCHECKED:
        tracker.check_testing_status()
    if tracker.changes_status == Tracker.STATUS_PASSED:
        logger.info("Vep config passed testing")
    elif tracker.changes_status == Tracker.STATUS_FAILED:
        error_message = (
            "Error: Testing failed for VEP config file update"
            + f" for {assay} clinvar version {clinvar_version}"
        )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()
    else:
        error_message = (
            "Error: Vep config testing evidence for assay"
            + f" {assay} could not be checked"
        )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Make github release of current config version
    # deploy new config from 003 to 001 reference project
    if not tracker.config_deployed:
        repo_dir = f"temp/prod_vep_repo_{assay}"
        git_handler = GitHandler(
            repo_dir, repo_name, assay_repo, "main",
            login_handler.github_token
        )
        new_version = tracker.config_version
        comment = (
            "Updated config version to"
            + f" \"config_version\": \"{new_version}\"\n\n"
            + "Updated ClinVar annotation reference file source:\n"
            + f"\"file_id\":\"{vcf_id}\"\n"
            + f"\"index_id\":\"{index_id}\"\n"
        )
        git_handler.make_release(new_version, comment)
        git_handler.exit_github()
        # find dev config id from 003 project
        folder_path = f"{config_subfolder}/Testing"
        dev_config_id = utils.find_dx_file(
            dev_proj_id, folder_path, tracker.config_name
        )
        deployer.deploy_config_to_production(
            ref_proj_id, dev_proj_id, dev_config_id, deploy_folder
        )
    else:
        new_version = tracker.config_version
        error_message = (
            "Info: The vep config update update for assay"
            + f" {assay} config version {new_version}"
            + f" clinvar version {clinvar_version} has already been completed"
            )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Verification that vep config has been deployed to 001
    tracker.check_config_deployed()
    if not tracker.config_deployed:
        error_message = (
            f"Error: Vep config file for assay {assay}"
            + f" build {genome_build} was not deployed to 001"
        )
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()
    else:
        # notify team of completed vep config update
        config_name = f"{assay}_test_config_v{new_version}.json"
        slack_handler.announce_config_update(
            slack_channel, config_name, assay, genome_build, clinvar_version
        )
        exit_prometheus()


def exit_prometheus() -> None:
    """safely exits Prometheus
    """
    logger.info("Exiting prometheus")
    exit()


if __name__ == "__main__":
    """
    Send either "bin" or "nextflow-bin" from nextflow script depending
    on where program is run
    This will either be "bin" for local, or "nextflow-bin" for running it as
    a DNAnexus app/applet
    This is followed by the assay name from nextflow script e.g., TSO500
    followed by the genome build e.g., b38

    Example command:
        python3 bin/vep_config_update.py nextflow-bin TSO500 b38
        path/config.json path.creds.json

    Args:
        bin_folder (str): folder scripts are run from
        assay (str): vep assay being updated
        genome_build (str): genome build used for update
        config_path (str): path to config file
        creds_path (str): path to credentials file
    """

    # validate arguments
    num_args = len(sys.argv)
    if num_args < 6:
        logger.error(
            "6 command line args are required to run vep_config_update.py"
            + f" but {num_args} were provided"
        )
        exit_prometheus()

    run_vep_config_update(
        sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    )
