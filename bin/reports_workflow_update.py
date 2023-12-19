"""
Runs prometheus ClinVar TSO500 reports workflow update
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import logging
import dxpy
import os
import re
import sys

import deployer
from login_handler import LoginHandler
from slack_handler import SlackHandler
from utils import (get_prod_version,
                   get_prod_vep_config,
                   load_config,
                   load_config_reports_workflow,
                   check_proj_folder_exists)
from git_handler import GitHandler
import utils
import workflow_handler
from progress_tracker import WorkflowProgressTracker as Tracker

logger = logging.getLogger("main log")


def run_workflow_config_update(bin_folder, genome_build):
    """runs all steps in the helios reports workflow update

    Args:
        bin_folder (str): folder scripts are run from
        genome_build (str): genome build used for update
    """
    assay = "TSO500"
    # load config files and log into websites
    ref_proj_id, dev_proj_id, slack_channel = load_config()
    workflow_repo = load_config_reports_workflow()
    login_handler = LoginHandler()
    login_handler.login_DNAnexus(dev_proj_id)
    slack_handler = SlackHandler(login_handler.slack_token)

    # find latest TSO500 vep config from 001 reference project
    # find latest clinvar annotation resource version
    # make new vep update folder in overall update folder
    ref_vep_config_folder = "/dynamic_files/vep_configs"
    vep_config_id = get_prod_vep_config(ref_proj_id,
                                        ref_vep_config_folder,
                                        assay)
    ref_clinvar_folder = "/annotation/{}/clinvar/".format(genome_build)
    (clinvar_version, vcf_id, index_id) = get_prod_version(ref_proj_id,
                                                           ref_clinvar_folder,
                                                           genome_build)
    config_subfolder = ("/ClinVar_version_{}".format(clinvar_version)
                        + "_reports_workflow_update_{}").format(assay)
    dev_project = dxpy.bindings.dxproject.DXProject(dxid=dev_proj_id)
    if not check_proj_folder_exists(dev_proj_id, config_subfolder):
        dev_project.new_folder(config_subfolder)
    vep_config_name = utils.find_file_name_from_id(vep_config_id)

    # check if any steps have already been completed
    evidence_folder = "{}/Evidence".format(config_subfolder)
    testing_folder = "{}/Testing".format(config_subfolder)
    deploy_folder = "/apps_workflows"
    tracker = Tracker(dev_proj_id, ref_proj_id, evidence_folder,
                      deploy_folder, genome_build, clinvar_version,
                      workflow_repo, assay, login_handler.github_token,
                      vcf_id, vep_config_id)
    tracker.perform_checks()

    # download git repo for latest TSO500 reports workflow
    # make branch on repo and switch to new branch
    # check old vep config ID is different to new vep config ID
    # replace old vep config ID with new ID
    # push repo to github
    # create pull request
    # merge pull request to main branch
    repo_dir = "temp/reports_workflow_repo_{}".format(assay)
    split_assay_url = workflow_repo.split("/")
    repo_name = "{}/{}".format(split_assay_url[3],
                               split_assay_url[4])
    if not tracker.pr_merged:
        git_handler = GitHandler(repo_dir,
                                 repo_name,
                                 workflow_repo,
                                 "main",
                                 login_handler.github_token)
        git_handler.pull_repo()

        # check if production vep config file is already in config
        filename_glob = "{}/dxworkflow.json".format(repo_dir)
        match_regex = r"\"executable\": \"app-eggd_vep/.+\""
        file_id_regex = r"\"id\": \"(.*)\""
        is_different = utils.is_json_content_different(filename_glob,
                                                       match_regex,
                                                       file_id_regex,
                                                       vep_config_id)
        if not is_different:
            error_message = ("Error: The TSO500 VEP config ID in the"
                             + " production TSO500 reports workflow config"
                             + (" is identical to the new TSO500 vep"
                                + " config ID {}"
                                .format(vep_config_id))
                             + ". Therefore, this workflow config file does"
                             + " not need to be updated")
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()

        # switch to new branch
        branch_name = "prometheus_dev_branch_{}".format(clinvar_version)
        git_handler.make_branch(branch_name)
        git_handler.switch_branch(branch_name)
        # search through pulled dir, get old version, update to new
        repo_files = os.listdir(repo_dir)
        config_name = "dxworkflow.json"
        config_present = False
        for file in repo_files:
            match = re.match(config_name, file)
            if match:
                config_present = True
                break
        if not config_present:
            error_message = ("Error: No file matching config name {}"
                             .format(config_name)
                             + " was found in repo {}".format(repo_name))
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()
        # edit file contents to update version and config files
        # replace VEP config file pointed to in workflow config
        filename_glob = "{}/{}".format(repo_dir, config_name)
        match_regex = r"\"executable\": \"app-eggd_vep/.+\""
        replace_regex = r"\"id\": \"(.*)\""
        utils.update_json(filename_glob, match_regex,
                          replace_regex, vep_config_id)

        # replace version in name and title of workflow config
        match_regex = r"\{"
        replace_regex_name = r"\"name\": \"(.*)\""
        old_version = utils.search_json(filename_glob,
                                        match_regex,
                                        replace_regex_name)

        try:
            version = utils.increment_version(old_version)
        except Exception:
            error_message = ("Error: The helios workflow config file {}"
                             .format(config_name)
                             + " contains a version with invalid format")
            slack_handler.send_message(slack_channel, error_message)
            exit_prometheus()

        match_regex = r"\{"
        replace_regex_name = r"\"name\": \"(.*)\""
        replace_regex_title = r"\"title\": \"(.*)\""
        new_workflow_title = "TSO500_reports_workflow_v{}".format(version)
        utils.update_json(filename_glob, match_regex,
                          replace_regex_name, new_workflow_title)
        utils.update_json(filename_glob, match_regex,
                          replace_regex_title, new_workflow_title)

        git_handler.add_file(config_name)
        commit_message = ("Updated vep config ID and incremented"
                          + " version number for"
                          + " TSO500 reports workflow config file")
        git_handler.commit_changes(commit_message)
        git_handler.make_branch_github(branch_name, "main")
        git_handler.push_to_remote()

        pr_title = ("TSO500 reports workflow config update to use VEP config"
                    + " {}".format(vep_config_name))
        pr_num = git_handler.make_pull_request(branch_name,
                                               "main",
                                               pr_title,
                                               commit_message)
        git_handler.merge_pull_request(pr_num)
        git_handler.exit_github()
    else:
        logger.info("The reports workflow config file for assay"
                    + " {} has already been uploaded to github"
                    .format(assay)
                    + " and merged to the main branch")

    # Verification that step 1 has been completed
    tracker.check_pr_merged()
    if not tracker.pr_merged:
        error_message = ("Error: PR for workflow config update for assay {}"
                         .format(assay)
                         + " was not merged")
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
        repo_dir = "temp/prod_reports_workflow_repo_{}".format(assay)
        git_handler = GitHandler(repo_dir,
                                 repo_name,
                                 workflow_repo,
                                 "main",
                                 login_handler.github_token)
        # upload to specific 003 test directory
        folder_path = "{}/Testing".format(config_subfolder)
        if not check_proj_folder_exists(dev_proj_id, folder_path):
            dev_project.new_folder(folder_path, parents=True)
        workflow_path = repo_dir + "/dxworkflow.json"
        workflow_id = workflow_handler.build_reports_workflow(workflow_path,
                                                              dev_proj_id,
                                                              folder_path)

        evidence_folder = "{}/Evidence".format(config_subfolder)
        workflow_handler.test_reports_workflow(workflow_id,
                                               dev_proj_id,
                                               evidence_folder,
                                               tracker.workflow_version,
                                               vep_config_name,
                                               clinvar_version)
    else:
        logger.info("The workflow file for assay"
                    + " {} has already been tested"
                    .format(assay)
                    + " and testing evidence uploaded to DNAnexus")

    # Verification that testing has been uploaded to DNAnexus
    tracker.check_evidence_uploaded()
    if not tracker.evidence_uploaded:
        error_message = ("Error: Reports workflow testing evidence for assay"
                         + " {}".format(assay)
                         + " was not uploaded to DNAnexus")
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Check if test passed or failed based on presence of DXFile
    if tracker.changes_status == Tracker.STATUS_UNCHECKED:
        tracker.check_testing_status()
    if tracker.changes_status == Tracker.STATUS_PASSED:
        logger.info("Workflow passed testing")
    elif tracker.changes_status == Tracker.STATUS_FAILED:
        error_message = ("Error: Testing failed for reports workflow update"
                         + (" for {} with clinvar version {}"
                            .format(assay, clinvar_version)))
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()
    else:
        error_message = ("Error: Reports workflow testing evidence for assay"
                         + " {}".format(assay)
                         + " could not be checked")
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Make github release of current config version
    # deploy new workflow from 003 to 001 reference project
    if not tracker.workflow_deployed:
        repo_dir = "temp/prod_workflow_repo_{}".format(assay)
        git_handler = GitHandler(repo_dir,
                                 repo_name,
                                 workflow_repo,
                                 "main",
                                 login_handler.github_token)
        comment = ("Updated config name to"
                   + (" \"name\": \"{}\"\n"
                      .format(tracker.workflow_version))
                   + "\n"
                   + "Updated config title to"
                   + (" \"title\": \"{}\"\n"
                      .format(tracker.workflow_version))
                   + "\n"
                   + "Updated TSO500 vep config file source to"
                   + "  \"id\":\"{}\"\n".format(vep_config_id))
        regex = r"[0-9]+\.[0-9]+\.[0-9]+"
        version = re.search(regex, tracker.workflow_version)[0]
        git_handler.make_release(version, comment)
        git_handler.exit_github()
        # deploy new workflow to production
        workflow_id = utils.find_dx_file(dev_proj_id,
                                         testing_folder,
                                         tracker.workflow_version)
        deployer.deploy_workflow_to_production(ref_proj_id, dev_proj_id,
                                               workflow_id, deploy_folder)
    else:
        error_message = ("Error: The reports workflow update update for assay"
                         + " {} workflow version {}"
                         .format(assay, tracker.workflow_version)
                         + " clinvar version {}".format(clinvar_version)
                         + " has already been completed")
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Verification that workflow has been deployed to 001
    tracker.check_workflow_deployed()
    if not tracker.workflow_deployed:
        error_message = ("Error: Reports workfllow for assay {}"
                         .format(assay)
                         + " was not deployed to 001")
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()
    else:
        # notify team of completed workflow update
        slack_handler.announce_workflow_update(slack_channel,
                                               tracker.workflow_version,
                                               vep_config_id)
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
    # Followed by the genome build e.g., b38

    # validate arguments
    if len(sys.argv) != 3:
        logger.error("3 command line args are required"
                     + " to run reports_workflow_update.py")
        exit_prometheus()

    run_workflow_config_update(sys.argv[1], sys.argv[2])
