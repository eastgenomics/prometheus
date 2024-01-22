import unittest

from .context import make_vep_test_configs as mv

import os
os.chdir("..")
os.chdir("..")


class testMakeVepTestCOnfigs(unittest.TestCase):

    def test_make_config_file(self):
        """test that make_config_file can generate a config file
        """
        output = "test_output.txt"
        assert (
            mv.make_config_file(
                output,
                "file-1234",
                "file-5678"
            ) == output
            and os.path.isfile(output)
        )
        os.remove(output)


if __name__ == "__main__":
    unittest.main()
