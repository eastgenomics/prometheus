import slack_sdk as slack

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util import Retry

class SlackHandler:
    def __init__(self, slack_token):
        self.slack_token = slack_token

    def announce_clinvar_update(self, channel, clinvar_date, month):
        # TODO: learn how to use slack API
        update_message = """
        The new version of the ClinVar annotation resource file {} ({}) has been deployed into 001_reference
        """.format(clinvar_date, month)
        self.send_message(channel, update_message)

    def send_message(self, channel, message):
        # send message to slack channel

        http = requests.Session()
        retries = Retry(total=5, backoff_factor=10, method_whitelist=['POST'])
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
                print("Error in sending slack notification: {}".format(response.get('error')))
        except Exception as err:
                print("Error in sending post request for slack notification: {}".format(err))
