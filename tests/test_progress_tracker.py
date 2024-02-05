import unittest

from bin.util.progress_tracker import ClinvarProgressTracker as Tracker
from unittest.mock import Mock, patch


class testProgressTracker(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
