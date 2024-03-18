import unittest

from bin.util.progress_tracker import ClinvarProgressTracker as TrackerClinvar
from bin.util.progress_tracker import VepProgressTracker as TrackerVep
from unittest.mock import Mock, patch, mock_open


class TestClinvarProgressTracker(unittest.TestCase):

    @patch(
        "bin.util.progress_tracker.ClinvarProgressTracker.check_clinvar_fetched",
        Mock(return_value=None)
    )
    @patch(
        "bin.util.progress_tracker.ClinvarProgressTracker.check_configs_made",
        Mock(return_value=None)
    )
    @patch(
        "bin.util.progress_tracker.ClinvarProgressTracker.check_evidence_uploaded",
        Mock(return_value=None)
    )
    @patch(
        "bin.util.progress_tracker.ClinvarProgressTracker.check_changes_status",
        Mock(return_value=None)
    )
    @patch(
        "bin.util.progress_tracker.ClinvarProgressTracker.check_clinvar_deployed",
        Mock(return_value=None)
    )
    def test_perform_checks(self):
        """test that ClinvarProgressTracker can complete all check stages
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )
        # TODO: replace methods in perform_checks() to set object variables to True/"checked" when mock is called
        # condition: all checks fail
        with self.subTest():
            assert tracker_b37.perform_checks() is None
        # condition: clinvar has been fetched
        tracker_b37.clinvar_fetched = True
        with self.subTest():
            assert tracker_b37.perform_checks() is None
        # condition: config files have been made
        tracker_b37.configs_made = True
        with self.subTest():
            assert tracker_b37.perform_checks() is None
        # condition: changes have been checked
        tracker_b37.changes_status = "checked"
        with self.subTest():
            assert tracker_b37.perform_checks() is None

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value="file-1234567890"))
    @patch("bin.util.progress_tracker.check_proj_folder_exists",  Mock(return_value=False))
    def test_check_clinvar_fetched_false(self):
        """tests that check can find if clinvar has not been fetched
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_clinvar_fetched() is None
        with self.subTest():
            assert not tracker_b37.clinvar_fetched

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value="file-1234567890"))
    @patch("bin.util.progress_tracker.check_proj_folder_exists",  Mock(return_value=True))
    def test_check_clinvar_fetched_true(self):
        """tests that check can find if clinvar has been fetched
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_clinvar_fetched() is None
        with self.subTest():
            assert tracker_b37.clinvar_fetched

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(side_effect=IOError))
    @patch("bin.util.progress_tracker.check_proj_folder_exists",  Mock(return_value=True))
    def test_check_clinvar_fetched_error(self):
        """tests that check can find if clinvar has not been fetched when
        correct folder is present but files within folder are not
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_clinvar_fetched() is None
        with self.subTest():
            assert not tracker_b37.clinvar_fetched

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value="file-1234"))
    def test_check_configs_made_pass(self):
        """tests that check_configs_made can determine if config files have
        been made
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_configs_made() is None
        with self.subTest():
            assert tracker_b37.vep_config_dev == "file-1234"
        with self.subTest():
            assert tracker_b37.vep_config_prod == "file-1234"
        with self.subTest():
            assert tracker_b37.configs_made

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(side_effect=IOError))
    def test_check_configs_made_fail(self):
        """tests that check_configs_made can determine if config files have
        not been made
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_configs_made() is None
        with self.subTest():
            assert not tracker_b37.configs_made

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value="file-1234"))
    def test_check_evidence_uploaded_pass(self):
        """tests that check_evidence_uploaded can determine if evidence
        of testing vep has been uploaded
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_evidence_uploaded() is None
        with self.subTest():
            assert tracker_b37.evidence_uploaded

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(side_effect=IOError))
    def test_check_evidence_uploaded_fail(self):
        """tests that check_evidence_uploaded can determine if evidence
        of testing vep has not been uploaded
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_evidence_uploaded() is None
        with self.subTest():
            assert not tracker_b37.evidence_uploaded

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value="file-1234"))
    def test_check_changes_status_pass(self):
        """tests that check_changes_status can determine if changes have
        already passed
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_changes_status() is None
        with self.subTest():
            assert tracker_b37.changes_status == TrackerClinvar.STATUS_PASSED

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value="file-1234"))
    def test_check_clinvar_deployed_pass(self):
        """tests that check_clinvar_deployed can confirm that clinvar files
        have been deployed
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_clinvar_deployed() is None
        with self.subTest():
            assert tracker_b37.clinvar_deployed

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(side_effect=IOError))
    def test_check_clinvar_deployed_fail(self):
        """tests that check_clinvar_deployed can confirm that clinvar files
        have not been deployed
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_clinvar_deployed() is None
        with self.subTest():
            assert not tracker_b37.clinvar_deployed

    @patch("builtins.open",  mock_open(read_data=""))
    @patch("bin.util.progress_tracker.dxpy.upload_local_file",  Mock(return_value=None))
    def test_upload_check_passed(self):
        """tests that check_clinvar_deployed can confirm that clinvar files
        have been deployed
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = TrackerClinvar(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.upload_check_passed() is None


class TestVepProgressTracker(unittest.TestCase):

    @patch(
        "bin.util.progress_tracker.VepProgressTracker.check_pr_merged",
        Mock(return_value=None)
    )
    @patch(
        "bin.util.progress_tracker.VepProgressTracker.check_evidence_uploaded",
        Mock(return_value=None)
    )
    @patch(
        "bin.util.progress_tracker.VepProgressTracker.check_testing_status",
        Mock(return_value=None)
    )
    @patch(
        "bin.util.progress_tracker.VepProgressTracker.check_config_deployed",
        Mock(return_value=None)
    )
    def test_perform_checks(self):
        """test that VepProgressTracker can complete all check stages
        """
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, "", "TSO500",
            "", ""
        )
        # TODO: replace methods in perform_checks() to set object variables to True/STATUS_PASSED when mock is called
        # condition: all checks fail
        with self.subTest():
            assert tracker.perform_checks() is None
        # condition: pr has been merged
        tracker.pr_merged = True
        with self.subTest():
            assert tracker.perform_checks() is None
        # condition: testing evidence has been uploaded
        tracker.evidence_uploaded = True
        with self.subTest():
            assert tracker.perform_checks() is None
        # condition: changes have been checked
        tracker.changes_status = TrackerVep.STATUS_PASSED
        with self.subTest():
            assert tracker.perform_checks() is None

    @patch("bin.util.progress_tracker.glob.glob")
    @patch("bin.util.progress_tracker.shutil.rmtree")
    @patch("bin.util.progress_tracker.is_vep_config_id_different")
    @patch("bin.util.progress_tracker.GitHandler.exit_github")
    @patch("bin.util.progress_tracker.GitHandler")
    def test_check_pr_merged_pass(
        self, mock_git, mock_exit, mock_different, mock_rmtree, mock_glob
    ):
        """test that VepProgressTracker can confirm pull request has been
        merged
        """
        mock_git.return_value.mock_exit.return_value = None
        mock_different.return_value = False
        mock_rmtree.return_value = None
        mock_glob.return_value = ["dir/sample_vep_config_v1.1.1.json"]
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_pr_merged() is None
        with self.subTest():
            assert tracker.pr_merged

    @patch("bin.util.progress_tracker.glob.glob")
    @patch("bin.util.progress_tracker.shutil.rmtree")
    @patch("bin.util.progress_tracker.is_vep_config_id_different")
    @patch("bin.util.progress_tracker.GitHandler.exit_github")
    @patch("bin.util.progress_tracker.GitHandler")
    def test_check_pr_merged_fail(
        self, mock_git, mock_exit, mock_different, mock_rmtree, mock_glob
    ):
        """test that VepProgressTracker can confirm pull request has not
        been merged
        """
        mock_git.return_value.mock_exit.return_value = None
        mock_different.return_value = True
        mock_rmtree.return_value = None
        mock_glob.return_value = ["dir/sample_vep_config_v1.1.1.json"]
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_pr_merged() is None
        with self.subTest():
            assert not tracker.pr_merged

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value=None))
    def test_check_evidence_uploaded_pass(self):
        """test that VepProgressTracker can confirm testing evidence has been
        uploaded
        """
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_evidence_uploaded() is None
        with self.subTest():
            assert tracker.evidence_uploaded

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(side_effect=IOError))
    def test_check_evidence_uploaded_fail(self):
        """test that VepProgressTracker can confirm testing evidence has not
        been uploaded
        """
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_evidence_uploaded() is None
        with self.subTest():
            assert not tracker.evidence_uploaded

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value=None))
    def test_check_testing_status_pass(self):
        """test that VepProgressTracker can confirm testing has passed
        """
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_testing_status() is None
        with self.subTest():
            assert tracker.changes_status == TrackerVep.STATUS_PASSED

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(side_effect=IOError))
    def test_check_testing_status_fail(self):
        """test that VepProgressTracker can confirm testing has failed
        """
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_testing_status() is None
        with self.subTest():
            assert tracker.changes_status == TrackerVep.STATUS_FAILED

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value=None))
    def test_check_config_deployed_pass(self):
        """test that VepProgressTracker can confirm config has been deployed
        """
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_config_deployed() is None
        with self.subTest():
            assert tracker.config_deployed

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(side_effect=IOError))
    def test_check_config_deployed_fail(self):
        """test that VepProgressTracker can confirm config has not been
        deployed
        """
        clinvar_version = "010124"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        repo_link = "this/is/a/valid/link"
        tracker = TrackerVep(
            dev_proj_id, ref_proj_id, "", "",
            genome_build, clinvar_version, repo_link, "TSO500",
            "", ""
        )
        with self.subTest():
            assert tracker.check_config_deployed() is None
        with self.subTest():
            assert not tracker.config_deployed


if __name__ == "__main__":
    unittest.main()
