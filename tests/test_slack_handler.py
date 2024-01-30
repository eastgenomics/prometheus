import unittest

from bin.util import slack_handler as sh
from bin.util import login_handler as lh


class testSlackHandler(unittest.TestCase):

    def test_send_message_invalid_token(self):
        """test slack message fails to send when invalid token is provided
        """
        handler = sh.SlackHandler("invalid-token")
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("egg-test", test_message)

    def test_send_message_invalid_channel(self):
        """test slack message fails to send when slack channel is provided
        """
        # load config files
        login_handler = lh.LoginHandler()
        dx_token, slack_token = login_handler.load_credentials()

        handler = sh.SlackHandler(slack_token)
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("invalid-channel", test_message)

    def test_send_message_invalid_token_channel(self):
        """test slack message fails to send when invalid slack token
        and channel are provided
        """
        handler = sh.SlackHandler("invalid-token")
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("invalid-channel", test_message)

    def test_send_message_valid(self):
        """test SlackHandler can send a message with a valid slack token
        and channel
        """
        # load config files
        login_handler = lh.LoginHandler()
        dx_token, slack_token = login_handler.load_credentials()

        handler = sh.SlackHandler(slack_token)
        test_message = "This message is part of a Prometheus unit test"
        assert handler.send_message("egg-test", test_message) is None


if __name__ == "__main__":
    unittest.main()
