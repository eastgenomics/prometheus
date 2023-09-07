import unittest

from .context import login_handler as lh

import re
import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_login_DNAnexus(self):
        login = lh.LoginHandler()
        assert login.login_DNAnexus() is None

    def test_load_credentials(self):
        login = lh.LoginHandler()
        dx_token, slack_token = login.load_credentials()
        assert re.match(r".{32}", dx_token)
        assert re.match(r".+-.+-.+-.+", slack_token)


if __name__ == "__main__":
    unittest.main()
