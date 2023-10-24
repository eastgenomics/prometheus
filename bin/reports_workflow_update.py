"""
Runs prometheus ClinVar TSO500 reports workflow update
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import logging
import dxpy
import os
import re
import glob

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

logger = logging.getLogger("main log")


def run_workflow_config_update(bin_folder, genome_build):
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
    # TODO: add this function
    vep_config_id = get_prod_vep_config(assay)
    ref_clinvar_folder = "/annotation/b37/clinvar/"
    (clinvar_version, vcf_id, index_id) = get_prod_version(ref_proj_id,
                                                           ref_clinvar_folder,
                                                           genome_build)
    config_subfolder = ("/ClinVar_version_{}".format(clinvar_version)
                        + "_reports_workflow_update_{}").format(assay)
    dev_project = dxpy.bindings.dxproject.DXProject(dxid=dev_proj_id)
    if not check_proj_folder_exists(dev_proj_id, config_subfolder):
        dev_project.new_folder(config_subfolder)

    # download git repo for latest TSO500 reports workflow
    # make branch on repo and switch to new branch
    # git mv to rename workflow config with incremented version
    # (e.g., v1.0.1 to v1.0.2)
    # check old vep config ID is different to new vep config ID
    # replace old vep config ID with new ID
    # push repo to github
    # create pull request
    # merge pull request to main branch
    repo_dir = "temp/reports_workflow_repo_{}".format(assay)
    split_assay_url = workflow_repo.split("/")
    repo_name = "{}/{}".format(split_assay_url[3],
                               split_assay_url[4])
    git_handler = GitHandler(repo_dir,
                             repo_name,
                             workflow_repo,
                             "main",
                             login_handler.github_token)
    git_handler.pull_repo()

    # check if production vep config file is already in config
    filename_glob = "{}/*_vep_config_v*.json".format(repo_dir)
    match_regex = r"\"name\": \"ClinVar\""
    file_id_regex = r"\"file_id\":\"(.*)\""
    # TODO: add function
    is_different = utils.is_workflow_config_different(filename_glob,
                                                      match_regex,
                                                      file_id_regex,
                                                      vep_config_id)
    if not is_different:
        error_message = ("Error: The TSO500 VEP config ID in the production"
                         + " TSO500 reports workflow config"
                         + (" is identical to the new TSO500 vep config ID {}"
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
        raise Exception("No file matching config name {}".format(config_name)
                        + " was found in repo")
    # edit file contents to update version and config files
    # TODO: update to use correct regex for vep config file ID
    filename_glob = "{}/{}".format(repo_dir, config_name)
    match_regex = r"\"name\": \"ClinVar\""
    replace_regex = r"\"file_id\":\"(.*)\""
    utils.update_json(filename_glob, match_regex, replace_regex, vep_config_id)
    # replace version
    # TODO: find current version, increment version, provide to function
    version = "TODO"
    old_version = "TODO"
    match_regex = r"\"config_information\":"
    replace_regex = r"\"config_version\": \"(.*)\""
    utils.update_json(filename_glob, match_regex, replace_regex, version)

    git_handler.add_file(config_name)
    commit_message = ("Updated vep config ID and incremented"
                      + " version number for"
                      + " TSO500 reports workflow config file")
    git_handler.commit_changes(commit_message)
    git_handler.make_branch_github(branch_name, "main")
    git_handler.push_to_remote()
    # TODO: replace title and body
    pr_num = git_handler.make_pull_request(branch_name,
                                           "main",
                                           "my_pull_request",
                                           "test body")
    git_handler.merge_pull_request(pr_num)
    git_handler.exit_github()

    # clone git repo to get latest config file for given assay
    # upload config file to DNAnexus
    # fetch a valid panel bed and vcf file to run VEP for a given assay
    # run vep using updated config file and record results to 003 project
    # test results automatically to ensure results are valid
    # output human readable evidence to 003 project
    # format of evidence is expected, pasted results, compariosn, pass/fail
    # fail, record evidence, exit prometheus, notify team if test fails
    repo_dir = "temp/prod_reports_workflow_repo_{}".format(assay)
    git_handler = GitHandler(repo_dir,
                             repo_name,
                             workflow_repo,
                             "main",
                             login_handler.github_token)
    updated_config = glob.glob("{}/{}".format(repo_dir, config_name))[0]
    # upload to specific 003 test directory
    folder_path = "{}/Testing".format(config_subfolder)
    if not check_proj_folder_exists(dev_proj_id, folder_path):
        dev_project.new_folder(folder_path, parents=True)
    dev_config_id = (dxpy.upload_local_file(filename=updated_config,
                                            project=dev_proj_id,
                                            folder=folder_path)
                     .describe().get('id'))
    # TODO: implement workflow_testing module and function
    workflow_testing.workflow_testing(dev_proj_id,
                                      dev_config_id,
                                      config_subfolder,
                                      ref_proj_id,
                                      assay)

    # Check if test passed or failed based on presence of DXFile
    evidence_folder = "{}/Evidence".format(folder_path)
    output_filename = "reports_workflow_testing_summary.txt"
    try:
        utils.find_dx_file(dev_project, evidence_folder, output_filename)
    except Exception:
        error_message = ("Error: Testing failed for reports workflow"
                         + " config file update for"
                         + ("{} with clinvar version {}"
                            .format(assay, clinvar_version)))
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Make github release of current config version
    # deploy new config from 003 to 001 reference project
    # TODO: add correct names for placeholders "config_version" and "file_id"
    comment = (("Updated config version from \"config_version\": \"{}\" to"
                .format(old_version))
               + (" \"config_version\": \"{}\"\n"
                  .format(version))
               + "\n"
               + "Updated TSO500 vep config file source:\n"
               + "\"file_id\":\"{}\"\n".format(vep_config_id))
    git_handler.make_release(version, comment)
    deploy_folder = "/dynamic_files/vep_configs"
    deployer.deploy_config_to_production(ref_proj_id, dev_proj_id,
                                         dev_config_id, deploy_folder)

    # notify team of completed vep config update
    # TODO: implement announce_workflow_update function
    config_name = ("{}_test_config_v{}.json"
                   .format(assay, version))
    slack_handler.announce_workflow_update(slack_channel,
                                           config_name,
                                           assay,
                                           genome_build,
                                           clinvar_version)


def exit_prometheus():
    """safely exits Prometheus
    """
    logger.info("Exiting prometheus")
    exit()


if __name__ == "__main__":
    # TODO: send either "bin" or "nextflow-bin" from nextflow script depending
    # on where program is run
    # This will either be "bin" for local, or "nextflow-bin" for running it as
    # a DNAnexus app/applet
    # TODO: send the assay name from nextflow script
    run_workflow_config_update("bin", "b37")
