"""
Checks if parts of the update have already been performed
"""

import dxpy
from pathlib import Path
import pandas as pd
import glob
import shutil
import re

import utils
from git_handler import GitHandler


class ClinvarProgressTracker:
    """Checks and records update steps already performed
    """
    STATUS_UNCHECKED = "unchecked"
    STATUS_PASSED = "passed"
    STATUS_REVIEW = "awaiting review"

    def __init__(self, dev_proj_id, ref_proj_id, evidence_folder,
                 ref_deploy_folder, genome_build, dev_version):
        self.dev_proj_id = dev_proj_id
        self.ref_proj_id = ref_proj_id
        self.evidence_folder = evidence_folder
        self.ref_deploy_folder = ref_deploy_folder
        self.genome_build = genome_build
        self.dev_version = dev_version

        self.clinvar_fetched = False
        self.configs_made = False
        self.evidence_uploaded = False
        # unchecked, passed, awaiting manual review
        self.changes_status = self.STATUS_UNCHECKED
        self.clinvar_deployed = False

        self.clinvar_vcf_id = ""
        self.clinvar_tbi_id = ""
        self.vep_config_dev = ""
        self.vep_config_prod = ""

    def perform_checks(self):
        self.clinvar_fetched = False
        self.configs_made = False
        self.evidence_uploaded = False
        # unchecked, passed, awaiting manual review
        self.changes_status = self.STATUS_UNCHECKED
        self.clinvar_deployed = False

        self.check_clinvar_fetched()
        if not self.clinvar_fetched:
            return
        self.check_configs_made()
        if not self.configs_made:
            return
        self.check_evidence_uploaded()
        if not self.evidence_uploaded:
            return
        self.check_changes_status()
        if self.changes_status == self.STATUS_UNCHECKED:
            return
        self.check_clinvar_deployed()

    def check_clinvar_fetched(self):
        """checks if clinvar files have been uploaded to 003 dev project
        """
        # check .vcf and .tbi files exist for update in DNAnexus
        folder = (self.evidence_folder + "/Testing")
        if not utils.check_proj_folder_exists(self.dev_proj_id, folder):
            self.clinvar_fetched = False
            return

        try:
            vcf_name = ("clinvar_{}_{}.vcf.gz"
                        .format(self.dev_version, self.genome_build))
            vcf = utils.find_dx_file(self.dev_proj_id, self.evidence_folder,
                                     vcf_name)
            tbi_name = ("clinvar_{}_{}.vcf.gz.tbi"
                        .format(self.dev_version, self.genome_build))
            tbi = utils.find_dx_file(self.dev_proj_id, self.evidence_folder,
                                     tbi_name)
            self.clinvar_fetched = True
            self.clinvar_vcf_id = vcf
            self.clinvar_tbi_id = tbi
        except IOError:
            self.clinvar_fetched = False

    def check_configs_made(self):
        """checks if VEP config files have been uploaded to dev project
        """
        # check dev and prod vep config files exist for update in DNAnexus
        try:
            folder = self.evidence_folder + "/Testing"
            dev_filename = "Clinvar_annotation_vep_config_dev_*.json"
            prod_filename = "Clinvar_annotation_vep_config_prod_*.json"
            dev = utils.find_dx_file(self.dev_proj_id,
                                     folder,
                                     dev_filename)
            prod = utils.find_dx_file(self.dev_proj_id,
                                      folder,
                                      prod_filename)
            self.configs_made = True
            self.vep_config_dev = dev
            self.vep_config_prod = prod
        except IOError:
            self.configs_made = False

    def check_evidence_uploaded(self):
        """checks if evidence of VEP testing has been uploaded
        """
        # check evidence files have been uploaded to DNAnexus
        try:
            folder = self.evidence_folder + "/Evidence"
            added = "added_variants.csv"
            deleted = "deleted_variants.csv"
            changed = "changed_variants.csv"
            jobs = "job_report.txt"
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               added)
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               deleted)
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               changed)
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               jobs)
            self.evidence_uploaded = True
        except IOError:
            self.evidence_uploaded = False

    def check_changes_status(self):
        """checks if evidence passes validation checks
        """
        # check if manual or automatic review has been performed
        # for testing purposes, this is a text file named "manual_review.txt"
        # for manual review or "auto_review.txt" for automatic.
        # this must be present in the DNAnexus update evidence directory
        try:
            folder = self.evidence_folder + "/Evidence"
            auto = ("auto_review.txt")
            utils.find_dx_file(self.dev_proj_id, folder,
                               auto)
            self.changes_status = self.STATUS_PASSED
            return
        except IOError:
            pass

        try:
            folder = self.evidence_folder + "/Evidence"
            auto = ("manual_review.txt")
            utils.find_dx_file(self.dev_proj_id, folder,
                               auto)
            self.changes_status = self.STATUS_PASSED
            return
        except IOError:
            pass

        # get file ID, download file
        folder = self.evidence_folder + "/Evidence"
        changed = "changed_variants.csv"
        changed_id = utils.find_dx_file(self.dev_proj_id,
                                        folder,
                                        changed)
        Path("temp/validation").mkdir(parents=True, exist_ok=True)
        download_dest = "temp/validation/changed_variants.csv"
        dxpy.download_dxfile(changed_id, download_dest)

        # perform review to check if changes can be passed automatically
        changed = pd.read_csv(download_dest)
        benign_1 = "benign"
        benign_2 = "benign/likely benign"
        patho_1 = "pathogenic"
        patho_2 = "pathogenic/likely pathogenic"
        for index, row in changed.iterrows():
            if ((row["changed from"] == benign_1
                or row["changed from"] == benign_2)
                and (row["changed to"] == patho_1
                     or row["changed to"] == patho_2)):
                self.changes_status == self.STATUS_REVIEW
                return
            if ((row["changed to"] == benign_1
                or row["changed to"] == benign_2)
                and (row["changed from"] == patho_1
                     or row["changed from"] == patho_2)):
                self.changes_status == self.STATUS_REVIEW
                return
        self.upload_check_passed()
        self.changes_status = self.STATUS_PASSED

    def check_clinvar_deployed(self):
        """checks if clinvar files have been deployed to 001 reference project
        """
        # check that clinvar files have been deployed to 001
        try:
            folder = self.ref_deploy_folder
            vcf_name = ("clinvar_{}_{}.vcf.gz"
                        .format(self.dev_version, self.genome_build))
            utils.find_dx_file(self.ref_proj_id, folder,
                               vcf_name)
            tbi_name = ("clinvar_{}_{}.vcf.gz.tbi"
                        .format(self.dev_version, self.genome_build))
            utils.find_dx_file(self.ref_proj_id, folder,
                               tbi_name)
            self.clinvar_deployed = True
        except IOError:
            self.clinvar_deployed = False

    def upload_check_passed(self):
        """upload text file to 003 folder confirming auto-review passed
        """
        # upload txt file to 003 evidence folder
        file_name = "temp/auto_review.txt"
        with open(file_name, "w") as file:
            file.write("ClinVar changes have passed automatic review")
        folder = self.evidence_folder + "/Evidence"
        dxpy.upload_local_file(filename=file_name,
                               project=self.dev_proj_id,
                               folder=folder)


class VepProgressTracker:
    """Checks and records update steps already performed
    """
    STATUS_UNCHECKED = "unchecked"
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"

    def __init__(self, dev_proj_id, ref_proj_id, evidence_folder,
                 ref_deploy_folder, genome_build, dev_version,
                 config_github_link, assay, github_token,
                 clinvar_id):
        self.dev_proj_id = dev_proj_id
        self.ref_proj_id = ref_proj_id
        self.evidence_folder = evidence_folder
        self.ref_deploy_folder = ref_deploy_folder
        self.genome_build = genome_build
        self.dev_version = dev_version
        self.config_github_link = config_github_link
        self.assay = assay
        self.github_token = github_token
        self.clinvar_id = clinvar_id

        self.pr_merged = False
        self.evidence_uploaded = False
        # unchecked, passed, failed
        self.changes_status = self.STATUS_UNCHECKED
        self.config_deployed = False

        self.config_name = ""
        self.config_version = ""

    def perform_checks(self):
        self.pr_merged = False
        self.evidence_uploaded = False
        # unchecked, passed, failed
        self.changes_status = self.STATUS_UNCHECKED

        self.check_pr_merged()
        if not self.pr_merged:
            return
        self.check_evidence_uploaded()
        if not self.evidence_uploaded:
            return
        self.check_testing_status()
        if self.changes_status == self.STATUS_UNCHECKED:
            return
        self.check_config_deployed()

    def check_pr_merged(self):
        """checks if VEP config PR has been merged and new config is present
        """
        # download repo locally
        repo_dir = "temp/tracker/prod_vep_repo_{}".format(self.assay)
        split_assay_url = self.config_github_link.split("/")
        repo_name = "{}/{}".format(split_assay_url[3],
                                   split_assay_url[4])
        git_handler = GitHandler(repo_dir,
                                 repo_name,
                                 self.config_github_link,
                                 "main",
                                 self.github_token)
        updated_config = glob.glob("{}/*_vep_config_*.json"
                                   .format(repo_dir))[0]
        # set config name
        self.config_name = updated_config.split("/")[-1]
        self.config_version = re.match(r"(.*_vep_config_v)(.*).json",
                                       self.config_name).group(2)
        # read latest config
        # check if production clinvar files are already in config
        match_regex = r"\"name\": \"ClinVar\""
        file_id_regex = r"\"file_id\":\"(.*)\""
        is_different = utils.is_json_content_different(updated_config,
                                                       match_regex,
                                                       file_id_regex,
                                                       self.clinvar_id)
        # clean up files generated by check
        git_handler.exit_github()
        shutil.rmtree(repo_dir)
        # if version matches, return true
        if not is_different:
            self.pr_merged = True
        else:
            self.pr_merged = False

    def check_evidence_uploaded(self):
        """checks if evidence of VEP testing has been uploaded
        """
        # check evidence files have been uploaded to DNAnexus
        passed = False
        try:
            folder = self.evidence_folder
            summary = "pass_{}_testing_summary.txt".format(self.assay)
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               summary)
            passed = True
        except IOError:
            passed = False
        failed = False
        try:
            folder = self.evidence_folder
            summary = "fail_{}_testing_summary.txt".format(self.assay)
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               summary)
            failed = True
        except IOError:
            failed = False

        if passed or failed:
            self.evidence_uploaded = True

    def check_testing_status(self):
        """checks if evidence passes validation checks
        """
        # check if manual or automatic review has been performed
        # for testing purposes, this is a text file named "manual_review.txt"
        # for manual review or "auto_review.txt" for automatic.
        # this must be present in the DNAnexus update evidence directory
        output_filename = ("pass_{}_testing_summary.txt".format(self.assay))
        try:
            utils.find_dx_file(self.dev_proj_id,
                               self.evidence_folder,
                               output_filename)
            self.changes_status = self.STATUS_PASSED
        except Exception:
            self.changes_status = self.STATUS_FAILED

    def check_config_deployed(self):
        """checks if clinvar files have been deployed to 001 reference project
        """
        # check that clinvar files have been deployed to 001
        try:
            utils.find_dx_file(self.ref_proj_id,
                               self.ref_deploy_folder,
                               self.config_name)
            self.config_deployed = True
        except IOError:
            self.config_deployed = False


class WorkflowProgressTracker:
    """Checks and records workflow update steps already performed
    """
    STATUS_UNCHECKED = "unchecked"
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"

    def __init__(self, dev_proj_id, ref_proj_id, evidence_folder,
                 ref_deploy_folder, genome_build, dev_version,
                 config_github_link, assay, github_token,
                 clinvar_id, vep_config_id):
        self.dev_proj_id = dev_proj_id
        self.ref_proj_id = ref_proj_id
        self.evidence_folder = evidence_folder
        self.ref_deploy_folder = ref_deploy_folder
        self.genome_build = genome_build
        self.dev_version = dev_version
        self.config_github_link = config_github_link
        self.assay = assay
        self.github_token = github_token
        self.clinvar_id = clinvar_id
        self.vep_config_id = vep_config_id

        self.pr_merged = False
        self.evidence_uploaded = False
        # unchecked, passed, failed
        self.changes_status = self.STATUS_UNCHECKED
        self.workflow_deployed = False

        self.workflow_version = ""

    def perform_checks(self):
        self.pr_merged = False
        self.evidence_uploaded = False
        # unchecked, passed, failed
        self.changes_status = self.STATUS_UNCHECKED

        self.check_pr_merged()
        if not self.pr_merged:
            return
        self.check_evidence_uploaded()
        if not self.evidence_uploaded:
            return
        self.check_testing_status()
        if self.changes_status == self.STATUS_UNCHECKED:
            return
        self.check_workflow_deployed()

    def check_pr_merged(self):
        """checks if workflow config PR is merged and new config is present
        """
        # download repo locally
        repo_dir = "temp/tracker/prod_workflow_repo_{}".format(self.assay)
        split_assay_url = self.config_github_link.split("/")
        repo_name = "{}/{}".format(split_assay_url[3],
                                   split_assay_url[4])
        git_handler = GitHandler(repo_dir,
                                 repo_name,
                                 self.config_github_link,
                                 "main",
                                 self.github_token)
        updated_config = glob.glob("{}/dxworkflow.json"
                                   .format(repo_dir))[0]
        # set config name
        self.config_name = updated_config.split("/")[-1]
        # read latest config
        # check if production vep config file is already in config
        filename_glob = "{}/dxworkflow.json".format(repo_dir)
        match_regex = r"\"executable\": \"app-eggd_vep/.+\""
        file_id_regex = r"\"id\": \"(.*)\""
        is_different = utils.is_json_content_different(filename_glob,
                                                       match_regex,
                                                       file_id_regex,
                                                       self.vep_config_id)
        # get version of workflow
        # replace version in name and title of workflow config
        match_regex = r"\{"
        find_regex = r"\"name\": \"(.*)\""
        self.workflow_version = utils.search_json(filename_glob,
                                                  match_regex,
                                                  find_regex)
        # clean up files generated by check
        git_handler.exit_github()
        shutil.rmtree(repo_dir)
        # if version matches, return true
        if not is_different:
            self.pr_merged = True
        else:
            self.pr_merged = False

    def check_evidence_uploaded(self):
        """checks if evidence of workflow + VEP testing has been uploaded
        """
        # check evidence files have been uploaded to DNAnexus
        passed = False
        try:
            folder = self.evidence_folder
            summary = "pass_helios_workflow_testing_summary.txt"
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               summary)
            passed = True
        except IOError:
            passed = False
        failed = False
        try:
            folder = self.evidence_folder
            summary = "fail_helios_workflow_testing_summary.txt"
            utils.find_dx_file(self.dev_proj_id,
                               folder,
                               summary)
            failed = True
        except IOError:
            failed = False

        if passed or failed:
            self.evidence_uploaded = True

    def check_testing_status(self):
        """checks if evidence passes validation checks
        """
        analyses_test = "analyses_launched.txt"
        workflow_test = "pass_helios_workflow_testing_summary.txt"
        vep_test = "pass_helios_workflow_vep_testing_summary.txt"
        try:
            utils.find_dx_file(self.dev_proj_id,
                               self.evidence_folder,
                               analyses_test)
            utils.find_dx_file(self.dev_proj_id,
                               self.evidence_folder,
                               workflow_test)
            utils.find_dx_file(self.dev_proj_id,
                               self.evidence_folder,
                               vep_test)
            self.changes_status = self.STATUS_PASSED
        except Exception:
            self.changes_status = self.STATUS_FAILED

    def check_workflow_deployed(self):
        """checks if workflow has been deployed to 001 reference project
        """
        try:
            utils.find_dx_file(self.ref_proj_id,
                               self.ref_deploy_folder,
                               self.workflow_version)
            self.workflow_deployed = True
        except IOError:
            self.workflow_deployed = False
