import unittest
from unittest.mock import Mock, patch, mock_open
import sys
import os
sys.path.append(os.path.abspath(
    os.path.join(os.path.realpath(__file__), '../../bin')
))
from bin.util import vep_testing as vt


class testVepTesting(unittest.TestCase):

    @patch("subprocess.run")
    def test_get_diff_output(self, mock_subprocess):
        """test get_diff_output generates output file successfully
        """
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
        ) == output

    @patch("bin.util.utils.find_dx_file", Mock(return_value="test"))
    def test_get_recent_vep_vcf_bed(self):
        """test get_recent_vcf_bed returns a value for a vcf file and bed file
        """
        assay = "TSO500"
        ref_proj = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        genome_build = "b37"
        response = [{
            "id": "file-1234512345",
            "describe": {"name": "clinvar_20240101"}
        }]
        projects = [
            {
                "id": "project-1234512345",
                "describe": {
                    "id": "project-1234512345",
                    "name": "my_project",
                    "created": "240101"
                }
            },
            {
                "id": "project-5432154321",
                "describe": {
                    "id": "project-5432154321",
                    "name": "my_project_2",
                    "created": "230101"
                }
            }
        ]
        with patch(
            "dxpy.find_projects",
            Mock(return_value=projects)
        ):
            with patch("dxpy.find_data_objects", Mock(return_value=response)):
                vcf, bed = vt.get_recent_vep_vcf_bed(
                    assay, ref_proj, genome_build
                )
        with self.subTest():
            assert vcf == "file-1234512345"
        with self.subTest():
            assert bed == "file-1234512345"


if __name__ == "__main__":
    unittest.main()
