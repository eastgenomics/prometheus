import unittest

from .context import progress_tracker
from progress_tracker import ClinvarProgressTracker as Tracker
from .context import annotation_update
from .context import get_clinvar_files

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_perform_checks(self):
        (ref_proj_id,
         dev_proj_id,
         slack_channel) = annotation_update.load_config()

        (recent_vcf_file,
         recent_tbi_file,
         earliest_time,
         clinvar_version) = get_clinvar_files.get_ftp_files()
        update_folder = (
            f"/ClinVar_version_{clinvar_version}_annotation_resource_update"
        )
        b37_folder = "/annotation/b37/clinvar"
        genome_build = "b37"
        tracker_b37 = Tracker(
            dev_proj_id, ref_proj_id, update_folder, b37_folder, genome_build,
            clinvar_version
        )
        assert type(tracker_b37) is Tracker

        assert tracker_b37.perform_checks() is None


if __name__ == "__main__":
    unittest.main()
