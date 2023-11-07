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

import vep_testing
import deployer
from login_handler import LoginHandler
from slack_handler import SlackHandler
from utils import (get_prod_version,
                   load_config,
                   load_config_repo,
                   check_proj_folder_exists)
from git_handler import GitHandler
import utils

logger = logging.getLogger("main log")


def run_vep_config_update(bin_folder, assay, genome_build):
    # load config files and log into websites
    ref_proj_id, dev_proj_id, slack_channel = load_config()
    assay_repo = load_config_repo(assay)
    login_handler = LoginHandler()
    login_handler.login_DNAnexus(dev_proj_id)
    slack_handler = SlackHandler(login_handler.slack_token)

    # find latest clinvar name and ID from 001 reference project
    # check that update folder for this version exists in DNAnexus
    # make new vep update folder in overall update folder
    ref_clinvar_folder = "/annotation/b37/clinvar/"
    (clinvar_version, vcf_id, index_id) = get_prod_version(ref_proj_id,
                                                           ref_clinvar_folder,
                                                           genome_build)
    clinvar_subfolder = ("/ClinVar_version_{}".format(clinvar_version)
                         + "_annotation_resource_update")
    if not check_proj_folder_exists(dev_proj_id, clinvar_subfolder):
        raise Exception("ClinVar annotation resource update folder"
                        + " for version {}".format(clinvar_version)
                        + " does not exist")
    config_subfolder = ("/ClinVar_version_{}".format(clinvar_version)
                        + "_vep_config_update_{}").format(assay)
    dev_project = dxpy.bindings.dxproject.DXProject(dxid=dev_proj_id)
    if not check_proj_folder_exists(dev_proj_id, config_subfolder):
        dev_project.new_folder(config_subfolder)

    # download git repo for latest vep config for genome build and assay
    # check old clinvar version is less recent than new clinvar version
    # make branch on repo and switch to new branch
    # git mv to rename config with incremented version (e.g., v1.0.1 to v1.0.2)
    # replace old clinvar version with new version and increment version number
    # push repo to github
    # create pull request
    # merge pull request to main branch
    repo_dir = "temp/vep_repo_{}".format(assay)
    split_assay_url = assay_repo.split("/")
    repo_name = "{}/{}".format(split_assay_url[3],
                               split_assay_url[4])
    git_handler = GitHandler(repo_dir,
                             repo_name,
                             assay_repo,
                             "main",
                             login_handler.github_token)
    git_handler.pull_repo()

    # check if production clinvar files are already in config
    filename_glob = "{}/*_vep_config_v*.json".format(repo_dir)
    match_regex = r"\"name\": \"ClinVar\""
    file_id_regex = r"\"file_id\":\"(.*)\""
    is_different = utils.is_json_content_different(filename_glob,
                                                   match_regex,
                                                   file_id_regex,
                                                   vcf_id)
    if not is_different:
        error_message = ("Error: The ClinVar vcf ID in the production"
                         + " {} VEP config".format(assay)
                         + (" is identical to the new ClinVar vcf ID {}"
                            .format(vcf_id))
                         + ". Therefore, this config file does not need to"
                         + " be updated")
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    file_id_regex = r"\"index_id\":\"(.*)\""
    is_different = utils.is_json_content_different(filename_glob,
                                                   match_regex,
                                                   file_id_regex,
                                                   index_id)
    if not is_different:
        error_message = ("Error: The ClinVar vcf index ID in the current VEP"
                         + " config is identical to the new ClinVar vcf index"
                         + (" ID {}".format(index_id))
                         + ". Therefore, this config file does not need to"
                         + " be updated")
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # switch to new branch
    branch_name = "prometheus_dev_branch_{}".format(clinvar_version)
    git_handler.make_branch(branch_name)
    git_handler.switch_branch(branch_name)
    # search through pulled dir, get old version, update to new
    repo_files = os.listdir(repo_dir)
    old_config = ""
    new_config = ""
    new_version = ""
    for file in repo_files:
        match = re.match(r"(.*_vep_config_v)(.*).json", file)
        if match:
            old_config = file
            version = match.group(2)
            split_version = version.split(".")
            new_version_end = str(int(split_version[2]) + 1)
            new_version = "{}.{}.{}".format(split_version[0],
                                            split_version[1],
                                            new_version_end)
            new_config = "{}{}.json".format(match.group(1), new_version)
            break
    if old_config == "":
        raise Exception("No file matching config regex was found in repo")
    git_handler.rename_file("vep_repo_{}".format(assay),
                            old_config,
                            new_config)
    # edit file contents to update version and config files
    filename_glob = "{}/*_vep_config_v*.json".format(repo_dir)
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
    commit_message = ("Updated clinvar file and index IDs and incremented"
                      + " version number for"
                      + " {} config file".format(assay))
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
    repo_dir = "temp/prod_vep_repo_{}".format(assay)
    git_handler = GitHandler(repo_dir,
                             repo_name,
                             assay_repo,
                             "main",
                             login_handler.github_token)
    updated_config = glob.glob("{}/*_vep_config_*.json".format(repo_dir))[0]
    # upload to specific 003 test directory
    folder_path = "{}/Testing".format(config_subfolder)
    if not check_proj_folder_exists(dev_proj_id, folder_path):
        dev_project.new_folder(folder_path, parents=True)
    dev_config_id = (dxpy.upload_local_file(filename=updated_config,
                                            project=dev_proj_id,
                                            folder=folder_path)
                     .describe().get('id'))
    vep_testing.vep_testing_config(dev_proj_id,
                                   dev_config_id,
                                   config_subfolder,
                                   ref_proj_id,
                                   assay)

    # Check if test passed or failed based on presence of DXFile
    evidence_folder = "{}/Evidence".format(config_subfolder)
    output_filename = ("pass_{}_testing_summary.txt".format(assay))
    try:
        utils.find_dx_file(dev_proj_id, evidence_folder, output_filename)
    except Exception:
        error_message = ("Error: Testing failed for VEP config file update for"
                         + (" {} with clinvar version {}"
                            .format(assay, clinvar_version)))
        slack_handler.send_message(slack_channel, error_message)
        exit_prometheus()

    # Make github release of current config version
    # deploy new config from 003 to 001 reference project
    comment = (("Updated config version from \"config_version\": \"{}\" to"
                .format(version[1:]))
               + " \"config_version\": \"{}\"\n".format(new_version[1:])
               + "\n"
               + "Updated ClinVar annotation reference file source:\n"
               + "\"file_id\":\"{}\"\n".format(vcf_id)
               + "\"index_id\":\"{}\"\n".format(index_id))
    git_handler.make_release(new_version, comment)
    deploy_folder = "/dynamic_files/vep_configs"
    deployer.deploy_config_to_production(ref_proj_id, dev_proj_id,
                                         dev_config_id, deploy_folder)

    # notify team of completed vep config update
    config_name = ("{}_test_config_v{}.json"
                   .format(assay, new_version))
    slack_handler.announce_config_update(slack_channel, config_name,
                                         assay, genome_build, clinvar_version)


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
    run_vep_config_update("bin", "TWE", "b37")
