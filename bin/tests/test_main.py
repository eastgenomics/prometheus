import unittest

from bin.main import load_config

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_load_config(self):
        assert load_config() == ["project-GXZ0qvj4kbfjZ2fKpKZbxy8q",
                                 "project-GXXb2K04FK2bGyvV5GVxpYFf",
                                 "egg-test"]


if __name__ == "__main__":
    unittest.main()
