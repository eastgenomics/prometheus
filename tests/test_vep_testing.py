import unittest
from bin.util import vep_testing as vt
import os


class testVepTesting(unittest.TestCase):

    def test_get_diff_output(self):
        """test get_diff_output generates output file successfully
        """
        dev_content = [
            "1:2488153:A:G 135349 not_provided .",
            "1:11181327:C:T 516652 Benign .",
            "1:11188164:G:A 584432 Pathogenic .",
            "1:11190646:G:A 380311 Likely_Benign ."
        ]

        prod_content = [
            "1:2488153:A:G 135349 not_provided .",
            "1:11181327:C:T 516652 Likely_Benign .",
            "1:11188164:G:A 584432 Pathogenic .",
            "1:11190646:G:A 380311 Benign ."
        ]

        with open("test_dev.txt", "w") as f:
            f.writelines(dev_content)
            f.write("\n")
        with open("test_prod.txt", "w") as f:
            f.writelines(prod_content)
            f.write("\n")

        output = "temp/tso500_diff_output.txt"

        assert vt.get_diff_output(
            "test_dev.txt", "test_prod.txt", "tso500", "bin"
        ) == output
        os.remove(output)
        os.remove("test_dev.txt")
        os.remove("test_prod.txt")

    def test_make_job_report(self):
        """test make_job_report generates job report file successfully
        """
        dev_twe_job = "job-myjob12345"
        dev_tso_job = "job-myjob12346"
        prod_twe_job = "job-myjob12347"
        prod_tso_job = "job-myjob12348"
        output = "temp/unittest_file.txt"
        vt.make_job_report(
            dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job, output
        )
        file_exists = os.path.isfile(output)
        assert file_exists
        if file_exists:
            os.remove(output)

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
