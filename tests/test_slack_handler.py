import unittest

from bin.util import slack_handler as sh
from unittest.mock import Mock, patch
import requests


class testSlackHandler(unittest.TestCase):

    # TODO: patch over requests.Session.post to remove API call
    @patch("requests.Response.json")
    def test_send_message_invalid_token(self, mock_json):
        """test slack message fails to send when invalid token is provided
        """
        mock_json.return_value = {'ok': False, 'error': 'invalid_token'}

        handler = sh.SlackHandler("invalid-token")
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("egg-test", test_message)

    # TODO: patch over requests.Session.post to remove API call
    @patch("requests.Response.json")
    def test_send_message_invalid_channel(self, mock_json):
        """test slack message fails to send when invalid slack channel is
        provided
        """
        mock_json.return_value = {"ok": False, "error": "invalid_channel"}
        slack_token = "slack_token"

        handler = sh.SlackHandler(slack_token)
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(RuntimeError):
            handler.send_message("invalid-channel", test_message)

    # TODO: patch over requests.Session.post to remove API call
    @patch("requests.Response.json")
    def test_send_message_invalid_token_channel(self, mock_json):
        """test slack message fails to send when invalid slack token
        and channel are provided
        """
        mock_json.return_value = {"ok": False, "error": "invalid_token"}
        handler = sh.SlackHandler("invalid-token")
        test_message = "This message is part of a Prometheus unit test"
        with self.assertRaises(Exception):
            handler.send_message("invalid-channel", test_message)

    # TODO: patch over requests.Session.post to remove API call
    @patch("requests.Response.json")
    def test_send_message_valid(self, mock_json):
        """test SlackHandler can send a message with a valid slack token
        and channel
        """
        mock_json.return_value = {'ok': True}
        slack_token = "my_slack_token"
        handler = sh.SlackHandler(slack_token)
        test_message = "This message is part of a Prometheus unit test"
        assert handler.send_message("egg-test", test_message) is None


if __name__ == "__main__":
    unittest.main()
