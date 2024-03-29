import unittest

from bin.util.utils import (
    check_project_exists, check_proj_folder_exists, get_prod_version,
    find_dx_file
)
from bin.util import utils
from unittest.mock import Mock, patch, mock_open
import re
import dxpy


class testUtils(unittest.TestCase):

    @patch("bin.util.utils.DXProject")
    def test_check_project_exists(self, mock_proj):
        """test check_project_exists passes for existing id
        """
        test_proj_id = "project-1234512345"
        assert check_project_exists(test_proj_id)

    @patch("dxpy.bindings.dxproject.DXProject")
    def test_check_project_exists_invalid(self, mock_proj):
        """test check_project_exists fails for invalid id
        """
        mock_proj.side_effect = dxpy.exceptions.DXError({"error": {"type": "test", "message": "test"}}, "")
        test_proj_id = "project-this-id-will-fail"
        assert not check_project_exists(test_proj_id)

    @patch("dxpy.api.project_list_folder", Mock(return_value=None))
    def test_check_proj_folder_exists(self):
        """test check_proj_folder_exists passes for existing folder
        """
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/annotation/b37/clinvar"
        assert check_proj_folder_exists(test_proj_id, test_folder)

    @patch(
        "dxpy.api.project_list_folder",
        Mock(side_effect=dxpy.exceptions.ResourceNotFound(
            {"error": {"type": "test", "message": "test"}}, "")
        )
    )
    def test_check_proj_folder_exists_invalid(self):
        """test check_proj_folder_exists fails for folder not present
        """
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/this-folder-does-not-exist"
        assert not check_proj_folder_exists(test_proj_id, test_folder)

    @patch("bin.util.utils.check_proj_folder_exists", Mock(return_value=True))
    @patch("bin.util.utils.find_dx_file", Mock(return_value="test"))
    def test_get_prod_version_valid(self):
        """test get_prod_version returns valid version and file ids
        for valid input data
        """
        response = [{"id": "file-1234512345", "describe": {"name": "clinvar_20240101"}}]
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar"
        with patch("dxpy.find_data_objects", Mock(return_value=response)):
            (
                prod_version, prod_annotation_file_id, prod_index_file_id
            ) = get_prod_version(
                ref_proj_id, folder, "b37"
            )
        with self.subTest():
            assert re.match(r"\d{6}", prod_version)
        with self.subTest():
            assert prod_annotation_file_id == "file-1234512345"
        with self.subTest():
            assert prod_index_file_id == "test"

    @patch("bin.util.utils.check_proj_folder_exists")
    def test_get_prod_version_invalid_project(self, mock_check):
        """test get_prod_version raises exception when provided
        with invalid project id
        """
        mock_check.return_value = False
        ref_proj_id = "project-invalid"
        folder = "/annotation/b37/clinvar"

        with self.assertRaises(RuntimeError):
            get_prod_version(ref_proj_id, folder, "b37")

    @patch("bin.util.utils.check_proj_folder_exists")
    def test_get_prod_version_invalid_folder(self, mock_check):
        """test get_prod_version raises exception when provided
        with invalid folder path
        """
        mock_check.return_value = False
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b371/clinvar"

        with self.assertRaises(RuntimeError):
            get_prod_version(ref_proj_id, folder, "b37")

    def test_find_dx_file_invalid(self):
        """test find_dx_file fails when provided with invalid file name
        """
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar/"
        file = "invalid_file.xyz"
        response = []
        with patch("dxpy.find_data_objects", Mock(return_value=response)):
            with self.assertRaises(IOError):
                find_dx_file(ref_proj_id, folder, file, False)

    def test_find_dx_file_valid(self):
        """test find_dx_file returns valid file id when provided with
        existing file
        """
        response = [{"id": "file-1234512345", "describe": {"name": "clinvar_20240101"}}]
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar/"
        file = "clinvar_20230107_b37.vcf.gz"
        with patch("dxpy.find_data_objects", Mock(return_value=response)):
            file_id = find_dx_file(ref_proj_id, folder, file, False)
        assert re.match(r"^file-.+$", file_id)

    @patch("builtins.open", mock_open(read_data="data"))
    def test_load_config(self):
        """test load_config loads contents of config file
        """
        config_path = ""
        json_content = {
            "001_REFERENCE_PROJ_ID": "project-123456789012345678901234",
            "003_DEV_CLINVAR_UPDATE_PROJ_ID": "project-123456789012345678901234",
            "SLACK_CHANNEL": "egg-test",
            "CLINVAR_BASE_LINK": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar",
            "CLINVAR_BASE_PATH": "path/to/content"
        }
        with patch("json.load", Mock(return_value=json_content)):
            (
                ref_proj_id, dev_proj_id, slack_channel, clinvar_link,
                clinvar_path
            ) = utils.load_config(config_path)
        with self.subTest():
            assert ref_proj_id is not None
        with self.subTest():
            assert dev_proj_id is not None
        with self.subTest():
            assert slack_channel is not None
        with self.subTest():
            assert clinvar_link is not None
        with self.subTest():
            assert clinvar_path is not None

    @patch("builtins.open", mock_open(read_data="data"))
    def test_load_config_repo_TSO500(self):
        """test load_config_repo returns repo name for TSO500 assay
        """
        json_data = {
            "TSO500_CONFIG_REPO": "test1",
            "TWE_CONFIG_REPO": "test2",
            "CEN_CONFIG_REPO": "test3"
        }
        assay = "TSO500"
        with patch("json.load", Mock(return_value=json_data)):
            repo = utils.load_config_repo(assay, "")
            assert repo == "test1"

    @patch("builtins.open", mock_open(read_data="data"))
    def test_load_config_repo_TWE(self):
        """test load_config_repo returns repo name for TWE assay
        """
        json_data = {
            "TSO500_CONFIG_REPO": "test1",
            "TWE_CONFIG_REPO": "test2",
            "CEN_CONFIG_REPO": "test3"
        }
        assay = "TWE"
        with patch("json.load", Mock(return_value=json_data)):
            repo = utils.load_config_repo(assay, "")
            assert repo == "test2"

    @patch("builtins.open", mock_open(read_data="data"))
    def test_load_config_repo_CEN(self):
        """test load_config_repo returns repo name for CEN assay
        """
        json_data = {
            "TSO500_CONFIG_REPO": "test1",
            "TWE_CONFIG_REPO": "test2",
            "CEN_CONFIG_REPO": "test3"
        }
        assay = "CEN"
        with patch("json.load", Mock(return_value=json_data)):
            repo = utils.load_config_repo(assay, "")
            assert repo == "test3"

    def test_increment_version(self):
        """test increment_version can increment version
        """
        ver = "1.1.1"
        new_ver = utils.increment_version(ver)
        assert new_ver == "1.1.2"

    @patch("glob.glob", Mock(return_value="test"))
    @patch("builtins.open", mock_open(read_data="data"))
    @patch("json.dump", Mock(return_value=None))
    def test_update_json(self):
        """test update_json can update contents of json file
        """
        json_content = {"Header": {"File ID": "file-myfile12345"}}
        json_path_glob = "temp/unit*_update_json.txt"
        replace_with = "file-myfile55555"
        nested_path = ("Header", "File ID")

        with patch("json.load", Mock(return_value=json_content)):
            assert utils.update_json(
                json_path_glob, nested_path, replace_with
            ) is None

    @patch("glob.glob", Mock(return_value="test"))
    @patch("builtins.open", mock_open(read_data="data"))
    def test_is_json_content_different_valid(self):
        """test is_json_content_different returns true when content
        of json file is different at specified point
        """
        json_content = {"Header": {"File ID": "file-myfile12345"}}
        json_path_glob = "temp/unit*_content_different.txt"
        new_file_id = "file-myfile23456"
        old_file_id = "file-myfile12345"
        nested_path = ("Header", "File ID")
        with patch("json.load", Mock(return_value=json_content)):
            assert utils.is_json_content_different(
                json_path_glob, nested_path, new_file_id
            )

        with patch("json.load", Mock(return_value=json_content)):
            assert not utils.is_json_content_different(
                json_path_glob, nested_path, old_file_id
            )

    @patch("glob.glob", Mock(return_value="test"))
    @patch("builtins.open", mock_open(read_data="data"))
    def test_search_json_invalid(self):
        """test search_json raises exception when provided with
        invalid nested path
        """
        json_content = {"Header": {"File ID": "file-myfile12345"}}
        json_path_glob = "temp/unit*_search_json.txt"
        nested_path = ("Header", "Incorrect File ID")
        with patch("json.load", Mock(return_value=json_content)):
            with self.assertRaises(RuntimeError):
                utils.search_json(
                    json_path_glob,
                    nested_path
                )

    @patch("glob.glob", Mock(return_value="test"))
    @patch("builtins.open", mock_open(read_data="data"))
    def test_search_json_valid(self):
        """test search_json finds match when provided with valid regex
        """
        json_content = {"Header": {"File ID": "file-myfile12345"}}
        json_path_glob = "temp/unit*_search_json.txt"
        nested_path = ("Header", "File ID")
        with patch("json.load", Mock(return_value=json_content)):
            found = utils.search_json(
                json_path_glob, nested_path
            )
        assert found == "file-myfile12345"

    def test_search_for_regex(self):
        """test search_for_regex finds the correct number of strings
        using regex provided
        """
        path = "temp/unittest_log.txt"
        content = "This\nis\nan\nexample"
        regex = ".+e"
        with patch("builtins.open", mock_open(read_data=content)):
            results = utils.search_for_regex(path, regex)
        assert len(results) == 1


if __name__ == "__main__":
    unittest.main()
