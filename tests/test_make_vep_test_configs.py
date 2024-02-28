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


if __name__ == "__main__":
    unittest.main()
