import unittest

from .context import login_handler as lh

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_login_valid(self):
        login = lh.LoginHandler()
        assert login.login_DNAnexus() is None


if __name__ == "__main__":
    unittest.main()
