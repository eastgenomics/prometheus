"""
Handles all slack interactions
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class SlackHandler:
    """Handles slack interactions
    """
    def __init__(self, slack_token):
        self.slack_token = slack_token

    def announce_clinvar_update(self, channel, version, date):
        """announces Clinvar update to team

        Args:
            channel (str): name of slack channel to post to
            version (_type_): version of Clinvar file
            date (str): date of ClinVar file version
        """
        update_message = "The new version of the ClinVar "
        + "annotation resource file"
        + " {} ({}) has been deployed into 001_reference".format(version,
                                                                 date)
        self.send_message(channel, update_message)

    def send_message(self, channel, message):
        """sends message to specified slack channel

        Args:
            channel (str): channel to post to
            message (str): message to post

        Raises:
            Exception: Error sending post request for slack
            Exception: Error sending slack notification
        """
        http = requests.Session()
        retries = Retry(total=5, backoff_factor=10, allowed_methods=['POST'])
        http.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            response = http.post(
                'https://slack.com/api/chat.postMessage', {
                    'token': self.slack_token,
                    'channel': "#{}".format(channel),
                    'text': message
                }).json()

            if not response['ok']:
                # error in sending slack notification
                raise Exception("Error sending slack notification: {}"
                      .format(response.get('error')))
        except Exception as err:
            raise Exception("Error sending post request for slack "
                            + "notification: {}".format(err))
