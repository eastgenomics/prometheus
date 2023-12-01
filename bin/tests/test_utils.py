import unittest

from bin.utils import check_project_exists
from bin.utils import check_proj_folder_exists
from bin.utils import check_jobs_finished
from bin.utils import get_prod_version
from bin.utils import find_dx_file
from .context import utils

import re
import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_check_project_exists(self):
        test_proj_id = "project-this-id-will-fail"
        assert not check_project_exists(test_proj_id)

        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        assert check_project_exists(test_proj_id)

    def test_check_proj_folder_exists(self):
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/annotation/b37/clinvar"
        assert check_proj_folder_exists(test_proj_id, test_folder)

        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/invalid_name"
        assert not check_proj_folder_exists(test_proj_id, test_folder)

    def test_check_jobs_finished(self):
        test_job_id_list = ["job-this-id-will-fail"]
        with self.assertRaises(IOError):
            check_jobs_finished(test_job_id_list, 1, 2)

        test_job_id_list = ["job-this-id-will-fail",
                            "job-this-id-will-also-fail",
                            "job-this-id-will-fail-too"]
        with self.assertRaises(IOError):
            check_jobs_finished(test_job_id_list, 1, 2)

        test_job_id_list = ["job-GYJYgp04FK2b07Pyxb04zk6V"]
        assert check_jobs_finished(test_job_id_list, 1, 2) is None

        test_job_id_list = ["job-GYJYgp04FK2b07Pyxb04zk6V",
                            "job-GYJYgkj4FK2g7KBpKvV5Y8xy",
                            "job-GYJYbv84FK2yg6K4BZ07YPkK"]
        assert check_jobs_finished(test_job_id_list, 1, 2) is None

    def test_get_prod_version(self):
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar"
        check_proj_folder_exists(ref_proj_id, folder)
        (prod_version, prod_annotation_file_id,
            prod_index_file_id) = get_prod_version(ref_proj_id,
                                                   folder,
                                                   "b37")
        assert re.match(r"\d{6}", prod_version)
        assert re.match(r"^file-.+$", prod_annotation_file_id)
        assert re.match(r"^file-.+$", prod_index_file_id)

        ref_proj_id = "project-invalid"
        folder = "/annotation/b37/clinvar"

        with self.assertRaises(Exception):
            get_prod_version(ref_proj_id, folder, "b37")

        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b371/clinvar"

        with self.assertRaises(Exception):
            get_prod_version(ref_proj_id, folder, "b37")

    def test_find_dx_file(self):
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar/"
        file = "invalid_file.xyz"
        with self.assertRaises(IOError):
            find_dx_file(ref_proj_id, folder, file)

        file = "clinvar_20230107_b37.vcf.gz"
        file_id = find_dx_file(ref_proj_id, folder, file)
        assert re.match(r"^file-.+$", file_id)

    def test_load_config(self):
        ref_proj_id, dev_proj_id, slack_channel = utils.load_config()
        assert ref_proj_id is not None
        assert dev_proj_id is not None
        assert slack_channel is not None

    def test_load_config_repo(self):
        assay = "TSO500"
        repo = utils.load_config_repo(assay)
        assert repo is not None

        assay = "TWE"
        repo = utils.load_config_repo(assay)
        assert repo is not None

        assay = "CEN"
        repo = utils.load_config_repo(assay)
        assert repo is not None

    def test_load_config_reports_workflow(self):
        repo = utils.load_config_reports_workflow()
        assert repo is not None

    def test_increment_version(self):
        ver = "1.1.1"
        new_ver = utils.increment_version(ver)
        assert new_ver == "1.1.2"

    def test_search_for_regex(self):
        path = "temp/unittest_log.txt"
        # Note: all sample info used is fictional
        lines = ["This\n",
                 "sentence\n",
                 "is\n",
                 "false\n"]
        with open(path, "w") as file:
            file.writelines(lines)
        regex = ".+e"
        results = utils.search_for_regex(path, regex)
        assert len(results) == 2


if __name__ == "__main__":
    unittest.main()
