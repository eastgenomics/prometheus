"""
Runs prometheus ClinVar vep config
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import json
import logging
import dxpy
import os
import re
import glob

from get_clinvar_files import get_ftp_files, retrieve_clinvar_files
import make_vep_test_configs as vep
import vep_testing
import deployer
from login_handler import LoginHandler
from slack_handler import SlackHandler
from progress_tracker import ClinvarProgressTracker as Tracker
from utils import get_prod_version, load_config, check_proj_folder_exists
from git_handler import GitHandler

logger = logging.getLogger("main log")


def run_vep_config_update(bin_folder, assay, genome_build):
    # load config files and log into websites
    ref_proj_id, dev_proj_id, slack_channel = load_config()
    login_handler = LoginHandler(dev_proj_id)
    login_handler.login_DNAnexus()
    slack_handler = SlackHandler(login_handler.slack_token)

    # find latest clinvar name and ID from 001 reference project
    # check that update folder for this version exists in DNAnexus
    # make new vep update folder in overall update folder
    (clinvar_version, vcf_id, index_id) = get_prod_version(ref_proj_id,
                                                           dev_proj_id,
                                                           genome_build)
    clinvar_version = ""
    clinvar_subfolder = ("/ClinVar_version_{}".format(clinvar_version)
                         + "_annotation_resource_update")
    if not check_proj_folder_exists(dev_proj_id, clinvar_subfolder):
        raise Exception("ClinVar annotation resource update folder"
                        + " for version {}".format(clinvar_version)
                        + " does not exist")
    config_subfolder = ("/ClinVar_version_{}".format(clinvar_version)
                        + "_vep_config_update_{}").format(assay)
    dev_project = dxpy.bindings.dxproject.DXProject(dxid=dev_proj_id)
    dev_project.new_folder(config_subfolder)

    # download git repo for latest vep config for genome build and assay
    # make branch on repo and switch to new branch
    # git mv to rename config with incremented version (e.g., v1.0.1 to v1.0.2)
    # check old clinvar version is less recent than new clinvar version
    # replace old clinvar version with new version and increment version number
    # push repo to github
    # create pull request
    # merge pull request to main branch
    repo_dir = "temp/vep_repo_{}".format(assay)
    remote_url = "https://github.com/org/repo_name"
    invalid_test_url = "invalid"
    git_handler = GitHandler(repo_dir, invalid_test_url, "main")
    git_handler.pull_repo()
    # switch to new branch
    branch_name = "prometheus_dev_branch"
    git_handler.make_branch(branch_name)
    git_handler.switch_branch(branch_name)
    # search through pulled dir, get old version, update to new
    repo_files = os.listdir(repo_dir)
    old_config = ""
    new_config = ""
    new_version = ""
    for file in repo_files:
        match = re.match(r".*_vep_config_v(.*).json")
        if match:
            old_config = file
            version = match.group(1)
            new_version_end = int(version.split(".")[2]) + 1
            search = r".*_vep_config_v.*\..*\.(.*).json"
            new_config = re.sub(search, new_version_end, old_config)
            new_version = re.sub(r".*\..*\.(.*)", new_version_end, version)
            break
    if old_config == "":
        raise Exception("No file matching config regex was found in repo")
    git_handler.rename_file(old_config, new_config)
    # TODO: edit file contents to update version and config files
    # TODO: check old clinvar version is older than new version
    git_handler.add_file("{}/{}".format(repo_dir, new_config))
    commit_message = ("Updated clinvar file and index IDs and incremented"
                      + " version number for"
                      + " {} config file".format(assay))
    git_handler.commit_changes(commit_message)
    git_handler.make_pull_request(branch_name)
    git_handler.merge_pull_request(branch_name, "main")

    # clone git repo to get latest config file for given assay
    # upload config file to DNAnexus
    # fetch a valid panel bed and vcf file to run VEP for a given assay
    # run vep using updated config file and record results to 003 project
    git_handler = GitHandler(repo_dir, invalid_test_url, "main")
    updated_config = glob.glob("temp/*_vep_config_*.json")[0]
    # TODO: upload to specific 003 test directory
    #dxpy.upload_local_file(updated_config)

    # test results automatically to ensure results are valid
    # output human readable evidence to 003 project
    # format of evidence is expected, pasted results, compariosn, pass/fail
    # fail, record evidence, exit prometheus, notify team if test fails
    pass

    # Make github release of current config version
    # deploy new config from 003 to 001 reference project
    pass

    # notify team of completed vep config update
    config_name = ("{}_test_config_v1.0.0.json"
                   .format(assay))
    slack_handler.announce_config_update(slack_channel, config_name,
                                         assay, genome_build, clinvar_version)


if __name__ == "__main__":
    # TODO: send either "bin" or "nextflow-bin" from nextflow script depending
    # on where program is run
    # This will either be "bin" for local, or "nextflow-bin" for running it as
    # a DNAnexus app/applet
    # TODO: send the assay name from nextflow script
    run_vep_config_update("bin", "TWE", "b37")
