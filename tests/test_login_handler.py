import unittest
from bin.util import login_handler as lh
import re


class testLoginHandler(unittest.TestCase):

    def test_login_DNAnexus(self):
        """test LoginHandler can log into DNAnexus
        """
        login = lh.LoginHandler()
        assert login.login_DNAnexus() is None

    def test_login_DNAnexus_invalid(self):
        """test LoginHandler fails to log on to DNAnexus
        when provided with an invalid token
        """
        login = lh.LoginHandler()
        login.dx_token = "invalid-token"
        with self.assertRaises(RuntimeError):
            login.login_DNAnexus()

    def test_load_credentials(self):
        """test load_credentials can load credentials with valid format
        """
        login = lh.LoginHandler()
        dx_token, slack_token = login.load_credentials()
        assert (
            re.match(r".{32}", dx_token)
            and re.match(r".+-.+-.+-.+", slack_token)
        )


if __name__ == "__main__":
    unittest.main()
