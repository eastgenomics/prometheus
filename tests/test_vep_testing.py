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

    # TODO: fix package not recognised problem
    @patch("bin.util.vep_testing.dxpy.upload_local_file")
    @patch("bin.util.vep_testing.dxpy.bindings.dxproject.DXProject.new_folder")
    @patch("bin.util.vep_testing.dxpy.bindings.dxproject.DXProject")
    @patch("bin.util.vep_testing.check_proj_folder_exists")
    @patch("bin.util.vep_testing.inspect_logs")
    @patch("bin.util.vep_testing.dxpy.bindings.dxfile.DXFile.describe")
    @patch("bin.util.vep_testing.dxpy.bindings.dxfile.DXFile")
    @patch("bin.util.vep_testing.dxpy.bindings.dxjob.DXJob.get_id")
    @patch("bin.util.vep_testing.dxpy.bindings.dxjob.DXJob.DXJob.wait_on_done")
    @patch("bin.util.vep_testing.run_vep")
    @patch("bin.util.vep_testing.get_recent_vep_vcf_bed")
    def test_vep_testing_config(
        self, mock_recent, mock_run, mock_wait, mock_id,
        mock_file, mock_describe, mock_logs, mock_check,
        mock_proj, mock_folder, mock_upload
    ):
        mock_recent.return_value = ("file-5432", "file-6543")
        mock_run.return_value.mock_id.return_value = "file-7654"
        mock_file.return_value.mock_describe.return_value = {"name": "config.json"}
        mock_logs.return_value = (True, "pass_file.txt")
        mock_check.return_value = False
        mock_upload.return_value = "file-8888"

        project_id = "project-1234"
        dev_config_id = "file-1234"
        dx_update_folder = "example_folder"
        ref_proj_id = "project-2345"
        assay = "TSO500"
        genome_build = "b37"
        clinvar_id = "file-2345"
        assert vt.vep_testing_config(
            project_id, dev_config_id, dx_update_folder, ref_proj_id,
            assay, genome_build, clinvar_id
        ) == "file-8888"

    @patch("builtins.open", mock_open())
    @patch("bin.util.vep_testing.vcfpy.Reader.from_path")
    @patch("bin.util.vep_testing.glob.glob")
    @patch("bin.util.vep_testing.download_folder")
    @patch("bin.util.vep_testing.check_proj_folder_exists")
    def test_parse_vep_output(
        self, mock_folder, mock_download, mock_glob, mock_reader
    ):
        mock_folder.return_value = True
        mock_glob.return_value = ["path"]
        # TODO: mock vcfpy.Reader and provide contents
        mock_reader.return_value = None

        project_id = "project-1234"
        folder = "folder"
        label = "label"
        update_folder = "update_folder"
        # TODO: check write calls of mocked file written to
        assert vt.parse_vep_output(
            project_id, folder, label, update_folder
        ) is str

    @patch("dxpy.bindings.dxapp.DXApp.run")
    @patch("dxpy.bindings.dxapp.DXApp")
    def test_run_vep(self, mock_app, mock_run):
        project_id = "project-1234"
        project_folder = "folder"
        config_file = "file-1234"
        vcf_file = "file-2345"
        panel_bed_file = "file-3456"
        update_folder = "folder"
        assert vt.run_vep(
            project_id, project_folder, config_file, vcf_file, panel_bed_file,
            update_folder
        ) is not None


if __name__ == "__main__":
    unittest.main()
