"""
Checks if parts of the update have already been performed
"""

import dxpy
from pathlib import Path
import pandas as pd
import glob
import shutil
import re

from .utils import (
    check_proj_folder_exists, find_dx_file, is_vep_config_id_different
)
from .git_handler import GitHandler


class ClinvarProgressTracker:
    """Checks and records update steps already performed
    """
    STATUS_UNCHECKED = "unchecked"
    STATUS_PASSED = "passed"
    STATUS_REVIEW = "awaiting review"

    def __init__(
        self, dev_proj_id, ref_proj_id, evidence_folder, ref_deploy_folder,
        genome_build, dev_version
    ) -> None:
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

    def perform_checks(self) -> None:
        """check if any stages have already been completed
        """
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

    def check_clinvar_fetched(self) -> None:
        """checks if clinvar files have been uploaded to 003 dev project
        """
        # check .vcf and .tbi files exist for update in DNAnexus
        folder = f"{self.evidence_folder}/Testing"
        if not check_proj_folder_exists(self.dev_proj_id, folder):
            self.clinvar_fetched = False
            return

        try:
            vcf_name = f"clinvar_{self.dev_version}_GRCh{self.genome_build[1:]}.vcf.gz"
            vcf = find_dx_file(
                self.dev_proj_id, self.evidence_folder, vcf_name, False
            )
            tbi_name = (
                f"clinvar_{self.dev_version}_GRCh{self.genome_build[1:]}.vcf.gz.tbi"
            )
            tbi = find_dx_file(
                self.dev_proj_id, self.evidence_folder, tbi_name, False
            )
            self.clinvar_fetched = True
            self.clinvar_vcf_id = vcf
            self.clinvar_tbi_id = tbi
        except IOError:
            self.clinvar_fetched = False

    def check_configs_made(self) -> None:
        """checks if VEP config files have been uploaded to dev project
        check dev and prod vep config files exist for update in DNAnexus
        """
        try:
            folder = f"{self.evidence_folder}/Testing"
            dev_filename = "Clinvar_annotation_vep_config_dev_*.json"
            prod_filename = "Clinvar_annotation_vep_config_prod_*.json"
            dev = find_dx_file(
                self.dev_proj_id, folder, dev_filename, False
            )
            prod = find_dx_file(
                self.dev_proj_id, folder, prod_filename, False
            )
            self.configs_made = True
            self.vep_config_dev = dev
            self.vep_config_prod = prod
        except IOError:
            self.configs_made = False

    def check_evidence_uploaded(self) -> None:
        """checks if evidence of VEP testing has been uploaded to DNAnexus
        """
        try:
            folder = f"{self.evidence_folder}/Evidence"
            added = "added_variants.csv"
            deleted = "deleted_variants.csv"
            changed = "changed_variants.csv"
            jobs = "job_report.txt"
            find_dx_file(
                self.dev_proj_id, folder, added, False
            )
            find_dx_file(
                self.dev_proj_id, folder, deleted, False
            )
            find_dx_file(
                self.dev_proj_id, folder, changed, False
            )
            find_dx_file(
                self.dev_proj_id, folder, jobs, False
            )
            self.evidence_uploaded = True
        except IOError:
            self.evidence_uploaded = False

    def check_changes_status(self) -> None:
        """checks if evidence passes validation checks
        check if manual or automatic review has been performed
        for testing purposes, this is a text file named "manual_review.txt"
        for manual review or "auto_review.txt" for automatic.
        this must be present in the DNAnexus update evidence directory
        """
        for file_name in ["auto_review.txt", "manual_review.txt"]:
            try:
                folder = f"{self.evidence_folder}/Evidence"
                find_dx_file(
                    self.dev_proj_id, folder, file_name, False
                )
                self.changes_status = self.STATUS_PASSED
                return
            except IOError:
                pass

        # get file ID, download file
        folder = f"{self.evidence_folder}/Evidence"
        changed = "changed_variants.csv"
        changed_id = find_dx_file(
            self.dev_proj_id, folder, changed, False
        )
        Path("temp/validation").mkdir(parents=True, exist_ok=True)
        download_dest = "temp/validation/changed_variants.csv"
        dxpy.download_dxfile(changed_id, download_dest)

        # perform review to check if changes can be passed automatically
        changed_df = pd.read_csv(download_dest)
        # TODO: move whitelist to config file to enable it to
        # be changed easily in future
        whitelisted_changes = [
            ("benign", "benign/likely benign"),
            ("benign/likely benign", "benign"),
            ("pathogenic", "pathogenic/likely pathogenic"),
            ("pathogenic/likely pathogenic", "pathogenic"),
            ("conflicting.*", "conflicting.*")
        ]
        for index, row in changed_df.iterrows():
            # if variant classification is changed from benign to
            # pathogenic, flag changes for manual review
            # or if variant classification is changed from pathogenic to
            # benign, flag changes for manual review
            # flag for manual review if any change is present which
            # is not whitelisted
            is_change_whitelisted = False
            for tuple in whitelisted_changes:
                if (
                    re.match(tuple[0], row["changed from"])
                    and re.match(tuple[1], row["changed to"])
                ):
                    is_change_whitelisted = True
                    break

            if not is_change_whitelisted:
                self.changes_status == self.STATUS_REVIEW
                return

        self.upload_check_passed()
        self.changes_status = self.STATUS_PASSED

    def check_clinvar_deployed(self) -> None:
        """checks if clinvar files have been deployed to 001 reference project
        """
        try:
            folder = self.ref_deploy_folder
            vcf_name = f"clinvar_{self.dev_version}_{self.genome_build}.vcf.gz"
            tbi_name = (
                f"clinvar_{self.dev_version}_{self.genome_build}.vcf.gz.tbi"
            )
            for name in [vcf_name, tbi_name]:
                find_dx_file(
                    self.ref_proj_id, folder, name, False
                )
            self.clinvar_deployed = True
        except IOError:
            self.clinvar_deployed = False

    def upload_check_passed(self) -> None:
        """upload text file to 003 folder confirming auto-review passed
        """
        file_name = "temp/auto_review.txt"
        with open(file_name, "w") as file:
            file.write("ClinVar changes have passed automatic review")
        folder = f"{self.evidence_folder}/Evidence"
        dxpy.upload_local_file(
            filename=file_name, project=self.dev_proj_id, folder=folder
        )


class VepProgressTracker:
    """Checks and records update steps already performed
    """
    STATUS_UNCHECKED = "unchecked"
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"

    def __init__(
        self, dev_proj_id, ref_proj_id, evidence_folder, ref_deploy_folder,
        genome_build, dev_version, config_github_link, assay, github_token,
        clinvar_id
    ) -> None:
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

    def perform_checks(self) -> None:
        """check if any stages have already been completed
        """
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

    def check_pr_merged(self) -> None:
        """checks if VEP config PR has been merged and new config is present
        """
        # download repo locally
        repo_dir = f"temp/tracker/prod_vep_repo_{self.assay}"
        split_assay_url = self.config_github_link.split("/")
        repo_name = f"{split_assay_url[3]}/{split_assay_url[4]}"
        git_handler = GitHandler(
            repo_dir, repo_name, self.config_github_link, "main",
            self.github_token
        )
        updated_config = glob.glob(f"{repo_dir}/*_vep_config_*.json")[0]
        # set config name
        self.config_name = updated_config.split("/")[-1]
        self.config_version = re.match(
            r"(.*_vep_config_v)(.*).json", self.config_name
        ).group(2)
        # read latest config
        # check if production clinvar files are already in config
        is_different = is_vep_config_id_different(
            updated_config, self.clinvar_id, True
        )
        # clean up files generated by check
        git_handler.exit_github()
        shutil.rmtree(repo_dir)
        # if version matches, return true
        if not is_different:
            self.pr_merged = True
        else:
            self.pr_merged = False

    def check_evidence_uploaded(self) -> None:
        """checks if evidence of VEP testing has been uploaded to DNAnexus
        """
        pass_or_fail = False
        for name_start in ["pass", "fail"]:
            try:
                folder = self.evidence_folder
                summary = f"{name_start}_{self.assay}_testing_summary.txt"
                find_dx_file(
                    self.dev_proj_id, folder, summary, False
                )
                pass_or_fail = True
            except IOError:
                pass

        if pass_or_fail:
            self.evidence_uploaded = True

    def check_testing_status(self) -> None:
        """checks if evidence passes validation checks
        check if manual or automatic review has been performed
        for testing purposes, this is a text file named "manual_review.txt"
        for manual review or "auto_review.txt" for automatic.
        this must be present in the DNAnexus update evidence directory
        """

        output_filename = f"pass_{self.assay}_testing_summary.txt"
        try:
            find_dx_file(
                self.dev_proj_id, self.evidence_folder, output_filename, False
            )
            self.changes_status = self.STATUS_PASSED
        except IOError:
            self.changes_status = self.STATUS_FAILED

    def check_config_deployed(self) -> None:
        """checks if clinvar files have been deployed to 001 reference project
        """
        try:
            find_dx_file(
                self.ref_proj_id, self.ref_deploy_folder, self.config_name,
                False
            )
            self.config_deployed = True
        except IOError:
            self.config_deployed = False
