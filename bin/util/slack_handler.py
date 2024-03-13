"""
Handles all slack interactions
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class SlackHandler:
    """Handles slack interactions
    """
    def __init__(self, slack_token) -> None:
        self.slack_token = slack_token

    def announce_clinvar_update(
        self, channel, file_name, date, genome_build
    ) -> None:
        """announces Clinvar update to team

        Args:
            channel (str): name of slack channel to post to
            file_name (_type_): file name of Clinvar file
            date (str): date of ClinVar file version
            genome_build (str): genome build of ClinVar file
        """
        update_message = (
            f"The new version of the ClinVar {genome_build} annotation"
            + f" resource file {file_name} ({date}) has been deployed"
            + " into 001_reference.")
        self.send_message(channel, update_message)

    def announce_config_update(
        self, channel, file_name, assay, genome_build, clinvar_version
    ) -> None:
        """announces VEP config update to team

        Args:
            channel (str): name of slack channel to post to
            file_name (_type_): file name of config file
            assay (str): name of assay
            genome_build (str): genome build of config ClinVar file
            clinvar_version (str): version of clinvar
        """
        vcf_name = f"clinvar_{clinvar_version}_{genome_build}.vcf.gz"
        tbi_name = f"{vcf_name}.tbi"
        update_message = (
            f"The latest version of the {assay} vep config file has been"
            + f" deployed into the 001 reference project as {file_name}."
            + "\nThe update consists of updating the ClinVar"
            + " annotation resource files specificed to"
            + f" {vcf_name} and {tbi_name}.")
        self.send_message(channel, update_message)

    def send_message(self, channel, message) -> None:
        """sends message to specified slack channel

        Args:
            channel (str): channel to post to
            message (str): message to post

        Raises:
            Exception: Error sending post request for slack
            Exception: Error sending slack notification
        """
        full_message = "🔥 Prometheus: " + message

        http = requests.Session()
        retries = Retry(total=5, backoff_factor=10, allowed_methods=["POST"])
        http.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            post = http.post(
                "https://slack.com/api/chat.postMessage", {
                    "token": self.slack_token,
                    "channel": f"#{channel}",
                    "text": full_message
                }
            )
            response = post.json()

            if not response['ok']:
                # error in sending slack notification
                raise RuntimeError(
                    "Error sending slack"
                    + f" notification: {response.get('error')}"
                )
        except Exception as err:
            raise RuntimeError(
                f"Error sending post request for slack notification: {err}"
            )
