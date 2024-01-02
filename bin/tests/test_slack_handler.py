import unittest

from .context import slack_handler as sh
from .context import login_handler as lh

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_send_message(self):
        handler = sh.SlackHandler("invalid-token")
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("egg-test", test_message)

        # load config files
        login_handler = lh.LoginHandler()
        dx_token, slack_token = login_handler.load_credentials()

        handler = sh.SlackHandler(slack_token)
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("invalid-channel", test_message)

        handler = sh.SlackHandler("invalid-token")
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("invalid-channel", test_message)

        # load config files
        login_handler = lh.LoginHandler()
        dx_token, slack_token = login_handler.load_credentials()

        handler = sh.SlackHandler(slack_token)
        test_message = "This message is part of a Prometheus unit test"
        assert handler.send_message("egg-test", test_message) is None


if __name__ == "__main__":
    unittest.main()
