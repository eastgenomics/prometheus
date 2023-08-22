import unittest

from bin.utils import check_project_exists
from bin.utils import check_proj_folder_exists
from bin.utils import check_jobs_finished

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


if __name__ == "__main__":
    unittest.main()
