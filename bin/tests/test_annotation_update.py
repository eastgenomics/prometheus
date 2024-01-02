import unittest

from .context import annotation_update

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_load_config(self):
        assert annotation_update.load_config() == ("project-GXZ0qvj4kbfjZ2fKpKZbxy8q",
                                                   "project-GXXb2K04FK2bGyvV5GVxpYFf",
                                                   "egg-test")


if __name__ == "__main__":
    unittest.main()
