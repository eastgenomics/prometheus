import unittest

from .context import make_vep_test_configs as mv

import re
import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_get_prod_version(self):
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b37/clinvar"
        (prod_version, prod_annotation_file_id,
            prod_index_file_id) = mv.get_prod_version(ref_proj_id,
                                                      folder,
                                                      "b37")
        assert re.match(r"\d{6}", prod_version)
        assert re.match(r"^file-.+$", prod_annotation_file_id)
        assert re.match(r"^file-.+$", prod_index_file_id)

    def test_get_prod_invalid_proj(self):
        ref_proj_id = "project-invalid"
        folder = "/annotation/b37/clinvar"

        with self.assertRaises(Exception):
            mv.get_prod_version(ref_proj_id, folder, "b37")

    def test_get_prod_invalid_folder(self):
        ref_proj_id = "project-GXZ0qvj4kbfjZ2fKpKZbxy8q"
        folder = "/annotation/b371/clinvar"

        with self.assertRaises(Exception):
            mv.get_prod_version(ref_proj_id, folder, "b37")

    def test_make_config_file(self):
        output = "test_output.txt"
        assert mv.make_config_file(output,
                                   "file-1234",
                                   "file-5678") == output
        assert os.path.isfile(output)
        os.remove(output)


if __name__ == "__main__":
    unittest.main()
