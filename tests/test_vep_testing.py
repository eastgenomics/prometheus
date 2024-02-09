import unittest
from bin.util import vep_testing as vt
from unittest.mock import Mock, patch, mock_open


class testVepTesting(unittest.TestCase):

    # TODO: replace open for 2 different files
    def test_get_diff_output(self):
        """test get_diff_output generates output file successfully
        """
        dev_content = (
            "1:2488153:A:G 135349 not_provided .\n"
            + "1:11181327:C:T 516652 Benign .\n"
            + "1:11188164:G:A 584432 Pathogenic .\n"
            + "1:11190646:G:A 380311 Likely_Benign ."
        )

        prod_content = (
            "1:2488153:A:G 135349 not_provided .\n"
            + "1:11181327:C:T 516652 Likely_Benign .\n"
            + "1:11188164:G:A 584432 Pathogenic .\n"
            + "1:11190646:G:A 380311 Benign ."
        )

        output = "temp/tso500_diff_output.txt"

        assert vt.get_diff_output(
            "test_dev.txt", "test_prod.txt", "tso500", "bin"
        ) == output

    @patch("builtins.open", mock_open(read_data="data"))
    def test_make_job_report(self):
        """test make_job_report can generate report
        """
        dev_twe_job = "job-myjob12345"
        dev_tso_job = "job-myjob12346"
        prod_twe_job = "job-myjob12347"
        prod_tso_job = "job-myjob12348"
        output = "temp/unittest_file.txt"
        assert vt.make_job_report(
            dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job, output
        ) is None

    def test_get_recent_vep_vcf_bed(self):
        """test get_recent_vcf_bed returns a value for a vcf file and bed file
        """
        assay = "TSO500"
        ref_proj = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        genome_build = "b37"
        vcf, bed = vt.get_recent_vep_vcf_bed(assay, ref_proj, genome_build)
        assert (
            vcf is not None
            and bed is not None
        )


if __name__ == "__main__":
    unittest.main()