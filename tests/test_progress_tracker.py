import unittest

from bin.util.progress_tracker import ClinvarProgressTracker as Tracker
from unittest.mock import Mock, patch


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
        tracker_b37 = Tracker(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        assert tracker_b37.perform_checks() is None

    @patch("bin.util.progress_tracker.find_dx_file",  Mock(return_value="file-1234567890"))
    @patch("bin.util.progress_tracker.check_proj_folder_exists",  Mock(return_value=False))
    def test_check_clinvar_fetched_true(self):
        """tests that check can be made if clinvar was fetched
        """
        clinvar_version = "010124"
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        dev_proj_id = "project-1234"
        ref_proj_id = "project-4321"
        tracker_b37 = Tracker(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )

        with self.subTest():
            assert tracker_b37.check_clinvar_fetched() is None
        with self.subTest():
            assert not tracker_b37.clinvar_fetched


if __name__ == "__main__":
    unittest.main()
