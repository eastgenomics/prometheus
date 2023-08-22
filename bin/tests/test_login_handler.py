import unittest

from bin.login_handler import LoginHandler

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_login_valid(self):
        print(os.getcwd())
        login = LoginHandler()
        assert login.login_DNAnexus() is None


if __name__ == "__main__":
    unittest.main()
