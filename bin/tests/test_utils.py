import unittest

from .context import check_project_exists
from .context import check_proj_folder_exists
from .context import check_jobs_finished
from .context import get_prod_version
from .context import find_dx_file
from .context import utils

import re
import os
os.chdir("..")
os.chdir("..")


class testUtils(unittest.TestCase):

    def test_check_project_exists(self):
        """test check_project_exists passes for existing id
        """
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        assert check_project_exists(test_proj_id)

    def test_check_project_exists_invalid(self):
        """test check_project_exists fails for invalid id
        """
        test_proj_id = "project-this-id-will-fail"
        assert not check_project_exists(test_proj_id)

    def test_check_proj_folder_exists(self):
        """test check_proj_folder_exists passes for existing folder
        """
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/annotation/b37/clinvar"
        assert check_proj_folder_exists(test_proj_id, test_folder)

    def test_check_proj_folder_exists_invalid(self):
        """test check_proj_folder_exists fails for folder not present
        """
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/this-folder-does-not-exist"
        assert not check_proj_folder_exists(test_proj_id, test_folder)

    def test_check_jobs_finished_single_invalid(self):
        """test check_jobs_finished fails for single invalid id
        """
        test_job_id_list = ["job-this-id-will-fail"]
        with self.assertRaises(IOError):
            check_jobs_finished(test_job_id_list, 1, 2)

    def test_check_jobs_finished_multiple_invalid(self):
        """test check_jobs_finished fails for multiple invalid ids
        """
        test_job_id_list = ["job-this-id-will-fail",
                            "job-this-id-will-also-fail",
                            "job-this-id-will-fail-too"]
        with self.assertRaises(IOError):
            check_jobs_finished(test_job_id_list, 1, 2)

    def test_check_jobs_finished_single_valid(self):
        """test check_jobs_finished succeeds for single valid id
        """
        test_job_id_list = ["job-GYJYgp04FK2b07Pyxb04zk6V"]
        assert check_jobs_finished(test_job_id_list, 1, 2) is None

    def test_check_jobs_finished_multiple_valid(self):
        """test check_jobs_finished succeeds for multiple valid ids
        """
        test_job_id_list = ["job-GYJYgp04FK2b07Pyxb04zk6V",
                            "job-GYJYgkj4FK2g7KBpKvV5Y8xy",
                            "job-GYJYbv84FK2yg6K4BZ07YPkK"]
        assert check_jobs_finished(test_job_id_list, 1, 2) is None

    def test_get_prod_version_valid(self):
        """test get_prod_version returns valid version and file ids
        for valid input data
        """
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar"
        check_proj_folder_exists(ref_proj_id, folder)
        (prod_version, prod_annotation_file_id,
            prod_index_file_id) = get_prod_version(
                ref_proj_id, folder, "b37"
            )
        assert (
            re.match(r"\d{6}", prod_version)
            and re.match(r"^file-.+$", prod_annotation_file_id)
            and re.match(r"^file-.+$", prod_index_file_id)
        )

    def test_get_prod_version_invalid_project(self):
        """test get_prod_version raises exception when provided
        with invalid project id
        """
        ref_proj_id = "project-invalid"
        folder = "/annotation/b37/clinvar"

        with self.assertRaises(Exception):
            get_prod_version(ref_proj_id, folder, "b37")

    def test_get_prod_version_invalid_folder(self):
        """test get_prod_version raises exception when provided
        with invalid folder path
        """
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b371/clinvar"

        with self.assertRaises(Exception):
            get_prod_version(ref_proj_id, folder, "b37")

    def test_find_dx_file_invalid(self):
        """test find_dx_file fails when provided with invalid file name
        """
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar/"
        file = "invalid_file.xyz"
        with self.assertRaises(IOError):
            find_dx_file(ref_proj_id, folder, file)

    def test_find_dx_file_valid(self):
        """test find_dx_file returns valid file id when provided with
        existing file
        """
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar/"
        file = "clinvar_20230107_b37.vcf.gz"
        file_id = find_dx_file(ref_proj_id, folder, file)
        assert re.match(r"^file-.+$", file_id)

    def test_load_config(self):
        """test load_config loads contents of config file
        """
        ref_proj_id, dev_proj_id, slack_channel = utils.load_config()
        assert (
            ref_proj_id is not None
            and dev_proj_id is not None
            and slack_channel is not None
        )

    def test_load_config_repo_TSO500(self):
        """test load_config_repo returns repo name for TSO500 assay
        """
        assay = "TSO500"
        repo = utils.load_config_repo(assay)
        assert repo is not None

    def test_load_config_repo_TWE(self):
        """test load_config_repo returns repo name for TWE assay
        """
        assay = "TWE"
        repo = utils.load_config_repo(assay)
        assert repo is not None

    def test_load_config_repo_CEN(self):
        """test load_config_repo returns repo name for CEN assay
        """
        assay = "CEN"
        repo = utils.load_config_repo(assay)
        assert repo is not None

    def test_increment_version(self):
        """test increment_version can increment version
        """
        ver = "1.1.1"
        new_ver = utils.increment_version(ver)
        assert new_ver == "1.1.2"

    def test_update_json(self):
        """test update_json can update contents of json file
        """
        path = "temp/unittest_update_json.txt"
        lines = [
            "This\n", "sentence\n", "is\n", "false\n"]
        with open(path, "w") as file:
            file.writelines(lines)
        json_path_glob = "temp/unit*_update_json.txt"
        first_match = "sentence"
        replace_regex = r"(is)"
        replace_with = "is not"
        search_regex = r"(is.+ot)"

        with self.assertRaises(Exception):
            utils.search_json(
                json_path_glob, first_match, search_regex)
        utils.update_json(
            json_path_glob, first_match, replace_regex, replace_with
        )

        found = utils.search_json(
            json_path_glob, first_match, search_regex
        )
        assert found == replace_with
        os.remove(path)

    def test_is_json_content_different_valid(self):
        """test is_json_content_different returns true when content
        of json file is different at specified point
        """
        path = "temp/unittest_content_different.txt"
        lines = [
            "Content\n", "Header\n", "File ID: \"file-myfile12345\"\n",
            "End\n"
        ]
        with open(path, "w") as file:
            file.writelines(lines)
        json_path_glob = "temp/unit*_content_different.txt"
        first_match = "Header"
        file_id_regex = r"File ID: \"(.+)\""
        new_file_id = "file-myfile23456"
        old_file_id = "file-myfile12345"
        assert utils.is_json_content_different(
            json_path_glob, first_match, file_id_regex, new_file_id
        )

        assert not utils.is_json_content_different(
            json_path_glob, first_match, file_id_regex, old_file_id
        )
        os.remove(path)

    def test_is_json_content_different_invalid_header(self):
        """test is_json_content_different raises exception when provided with
        invalid header
        """
        path = "temp/unittest_content_different.txt"
        lines = [
            "Content\n", "Header\n", "File ID: \"file-myfile12345\"\n",
            "End\n"
        ]
        with open(path, "w") as file:
            file.writelines(lines)
        json_path_glob = "temp/unit*_content_different.txt"
        file_id_regex = r"File ID: \"(.+)\""
        new_file_id = "file-myfile23456"
        first_match = "Header12345"
        with self.assertRaises(Exception):
            utils.is_json_content_different(
                json_path_glob, first_match, file_id_regex, new_file_id
            )
        os.remove(path)

    def test_is_json_content_different_invalid_match(self):
        """test is_json_content_different raises exception when provided with
        invalid match regex
        """
        path = "temp/unittest_content_different.txt"
        lines = [
            "Content\n", "Header\n", "File ID: \"file-myfile12345\"\n",
            "End\n"
        ]
        with open(path, "w") as file:
            file.writelines(lines)
        json_path_glob = "temp/unit*_content_different.txt"
        new_file_id = "file-myfile23456"
        first_match = "Header"
        file_id_regex = r"File ID Incorrect: \"(.+)\""
        with self.assertRaises(Exception):
            utils.is_json_content_different(
                json_path_glob, first_match, file_id_regex, new_file_id
            )
        os.remove(path)

    def test_search_json_invalid(self):
        """test search_json raises exception when provided with
        invalid search regex
        """
        path = "temp/unittest_search_json.txt"
        lines = [
            "This\n", "sentence\n", "is\n", "false\n"
        ]
        with open(path, "w") as file:
            file.writelines(lines)
        json_path_glob = "temp/unit*_search_json.txt"
        first_match = "sentence"
        search_regex = "(is12345)"

        with self.assertRaises(Exception):
            utils.search_json(
                json_path_glob,
                first_match,
                search_regex
            )
        os.remove(path)

    def test_search_json_valid(self):
        """test search_json finds match when provided with valid regex
        """
        path = "temp/unittest_search_json.txt"
        lines = [
            "This\n", "sentence\n", "is\n", "false\n"
        ]
        with open(path, "w") as file:
            file.writelines(lines)
        json_path_glob = "temp/unit*_search_json.txt"
        first_match = "sentence"
        search_regex = r"(is)"
        found = utils.search_json(
            json_path_glob, first_match, search_regex
        )
        assert found == "is"
        os.remove(path)

    def test_search_for_regex(self):
        """test search_for_regex finds the correct number of strings
        using regex provided
        """
        path = "temp/unittest_log.txt"
        lines = [
            "This\n", "sentence\n", "is\n", "false\n"
        ]
        with open(path, "w") as file:
            file.writelines(lines)
        regex = ".+e"
        results = utils.search_for_regex(path, regex)
        assert len(results) == 2
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
