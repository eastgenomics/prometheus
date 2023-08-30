"""
Checks if parts of the update have already been performed
"""

import utils


class ClinvarProgressChecker:
    """Checks and records update steps already performed
    """
    def __init__(self, dev_proj_id, ref_proj_id, evidence_folder,
                 ref_deploy_folder):
        self.perform_checks()

    def perform_checks(self):
        self.check_clinvar_fetched()
        self.check_configs_made()
        self.check_evidence_uploaded()
        self.check_changes_passed()
        self.check_clinvar_deployed()

    def check_clinvar_fetched(self):
        # check .vcf and .tbi files exist for update in DNAnexus
        self.clinvar_fetched = False

    def check_configs_made(self):
        # check dev and prod vep config files exist for update in DNAnexus
        self.configs_made = False

    def check_evidence_uploaded(self):
        # check evidence files have been uploaded to DNAnexus
        self.evidence_uploaded = False

    def check_changes_passed(self):
        # check if manual or automatic review has been performed
        # for testing purposes, this is a text file named "manual_review.txt"
        # for manual review or "auto_review.txt" for automatic.
        # this must be present in the DNAnexus update evidence directory

        # perform review to check if changes can be passed automatically
        self.changes_passed = False

    def check_clinvar_deployed(self):
        # check that clinvar files have been deployed to 001
        self.clinvar_deployed = False
