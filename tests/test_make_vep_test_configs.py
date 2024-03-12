import unittest
import sys
import os
sys.path.append(os.path.abspath(
    os.path.join(os.path.realpath(__file__), '../../bin')
))
from bin.annotation import make_vep_test_configs as mv
from unittest.mock import Mock, patch, mock_open


class testMakeVepTestConfigs(unittest.TestCase):

    @patch("shutil.copy", Mock(return_value=None))
    def test_make_config_file(self):
        """test that make_config_file can generate a config file
        """
        output = "test_output.txt"
        file_content = "CLINVAR_VCF_FILE_ID\nCLINVAR_VCF_TBI_FILE_ID"
        with patch("builtins.open", mock_open(read_data=file_content)):
            assert (
                mv.make_config_file(
                    output,
                    "file-1234",
                    "file-5678",
                    ""
                ) == output
            )

    @patch("bin.annotation.make_vep_test_configs.dxpy.bindings.dxproject.DXContainer.get_id")
    @patch("dxpy.upload_local_file")
    @patch("bin.annotation.make_vep_test_configs.make_config_file")
    @patch("bin.annotation.make_vep_test_configs.get_prod_version")
    def test_generate_config_files(
        self, get_prod, make_config, upload_data, mock_id
    ):
        get_prod.return_value = (
            "010203", "file-1234567890", "file-0987654321"
        )
        make_config.return_value.get_id.return_value = "temp/my_file.json"
        upload_data.return_value.get_id.return_value = "file-1234555555"
        dev_id, prod_id = mv.generate_config_files(
            "020304", "file-1234", "file-2345", "project-1234",
            "project-2345", "bin", "b37"
            )
        with self.subTest():
            assert dev_id == "file-1234555555"
        with self.subTest():
            assert prod_id == "file-1234555555"


if __name__ == "__main__":
    unittest.main()
