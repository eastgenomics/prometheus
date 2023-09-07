import unittest

from bin.utils import check_project_exists
from bin.utils import check_proj_folder_exists
from bin.utils import check_jobs_finished
from bin.utils import get_prod_version

import re
import os
os.chdir("..")


class testCase(unittest.TestCase):

    def test_invalid_proj_id(self):
        test_proj_id = "project-this-id-will-fail"
        assert not check_project_exists(test_proj_id)

    def test_valid_proj_id(self):
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        assert check_project_exists(test_proj_id)

    def test_valid_folder(self):
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/annotation/b37/clinvar"
        assert check_proj_folder_exists(test_proj_id, test_folder)

    def test_invalid_folder(self):
        test_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        test_folder = "/invalid_name"
        assert not check_proj_folder_exists(test_proj_id, test_folder)

    def test_check_jobs_finished_invalid(self):
        test_job_id_list = ["job-this-id-will-fail"]
        with self.assertRaises(IOError):
            check_jobs_finished(test_job_id_list, 1, 2)

        test_job_id_list = ["job-this-id-will-fail",
                            "job-this-id-will-also-fail",
                            "job-this-id-will-fail-too"]
        with self.assertRaises(IOError):
            check_jobs_finished(test_job_id_list, 1, 2)

    def test_check_jobs_finished_valid(self):
        test_job_id_list = ["job-GYJYgp04FK2b07Pyxb04zk6V"]
        assert check_jobs_finished(test_job_id_list, 1, 2) is None

        test_job_id_list = ["job-GYJYgp04FK2b07Pyxb04zk6V",
                            "job-GYJYgkj4FK2g7KBpKvV5Y8xy",
                            "job-GYJYbv84FK2yg6K4BZ07YPkK"]
        assert check_jobs_finished(test_job_id_list, 1, 2) is None

    def test_get_prod_version(self):
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar"
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


if __name__ == "__main__":
    unittest.main()
