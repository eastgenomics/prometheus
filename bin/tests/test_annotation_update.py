import unittest

from .context import annotation_update

import os
import re
os.chdir("..")
os.chdir("..")


class testAnnotationUpdate(unittest.TestCase):

    def test_load_config(self):
        """tests that the contents of the config file match
            the desired format
        """
        reference, development, channel = annotation_update.load_config()
        assert (
            re.match(r"project\-(.{24})", reference)
            and re.match(r"project\-(.{24})", development)
            and re.match(r".+\-.+", channel)
        )


if __name__ == "__main__":
    unittest.main()
