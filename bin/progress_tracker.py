"""
Checks if parts of the update have already been performed
"""

import utils


class ClinvarProgressTracker:
    """Checks and records update steps already performed
    """
    STATUS_UNCHECKED = "unchecked"
    STATUS_PASSED = "passed"
    STATUS_REVIEW = "awaiting review"

    def __init__(self, dev_proj_id, ref_proj_id, evidence_folder,
                 ref_deploy_folder, genome_build):
        self.dev_proj_id = dev_proj_id
        self.ref_proj_id = ref_proj_id
        self.evidence_folder = evidence_folder
        self.ref_deploy_folder = ref_deploy_folder
        self.genome_build = genome_build
        self.perform_checks()

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
        # check .vcf and .tbi files exist for update in DNAnexus
        folder = self.evidence_uploaded + "/Testing"
        if not utils.check_proj_folder_exists(self.dev_proj_id, folder):
            self.clinvar_fetched = False
            return

    def check_configs_made(self):
        # check dev and prod vep config files exist for update in DNAnexus
        self.configs_made = False

    def check_evidence_uploaded(self):
        # check evidence files have been uploaded to DNAnexus
        self.evidence_uploaded = False

    def check_changes_status(self):
        # check if manual or automatic review has been performed
        # for testing purposes, this is a text file named "manual_review.txt"
        # for manual review or "auto_review.txt" for automatic.
        # this must be present in the DNAnexus update evidence directory

        # perform review to check if changes can be passed automatically
        self.changes_status = self.STATUS_UNCHECKED

    def check_clinvar_deployed(self):
        # check that clinvar files have been deployed to 001
        self.clinvar_deployed = False
