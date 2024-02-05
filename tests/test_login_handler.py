import unittest
from bin.util import login_handler as lh
from unittest.mock import Mock, patch


class testLoginHandler(unittest.TestCase):

    @patch("dxpy.api.system_whoami", Mock(return_value=None))
    def test_login_DNAnexus(self):
        """test LoginHandler can log into DNAnexus
        """
        bin_folder = config_path = ""
        with patch(
            "bin.util.login_handler.LoginHandler.load_credentials",
            Mock(return_value=("invalid_token", "", ""))
        ):
            login = lh.LoginHandler(bin_folder, config_path)
        assert login.login_DNAnexus("") is None

    def test_login_DNAnexus_invalid(self):
        """test LoginHandler fails to log on to DNAnexus
        when provided with an invalid token
        """
        bin_folder = config_path = ""
        with patch(
            "bin.util.login_handler.LoginHandler.load_credentials",
            Mock(return_value=("invalid_token", "", ""))
        ):
            login = lh.LoginHandler(bin_folder, config_path)
        with self.assertRaises(RuntimeError):
            login.login_DNAnexus("")

    @patch(
            "bin.util.login_handler.LoginHandler.load_credentials",
            Mock(return_value=("dx_token", "slack_token"))
    )
    def test_load_credentials(self):
        """test load_credentials can load credentials with valid format
        """
        bin_folder = config_path = ""
        with patch(
            "bin.util.login_handler.LoginHandler.load_credentials",
            Mock(return_value=("invalid_token", "", ""))
        ):
            login = lh.LoginHandler(bin_folder, config_path)
        dx_token, slack_token = login.load_credentials()
        assert (
            dx_token is not None
            and slack_token is not None
        )


if __name__ == "__main__":
    unittest.main()
