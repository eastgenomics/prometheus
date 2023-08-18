import unittest

from bin.utils import check_project_exists
from bin.utils import check_proj_folder_exists

import os
os.chdir("..")


class testCase(unittest.TestCase):

    def test_invalid_proj_id(self):
        test_proj_id = "this-id-will-fail"
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


if __name__ == "__main__":
    unittest.main()
