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

    def announce_clinvar_update(self, channel, file_name, date, genome_build):
        """announces Clinvar update to team

        Args:
            channel (str): name of slack channel to post to
            file_name (_type_): file name of Clinvar file
            date (str): date of ClinVar file version
            genome_build (str): genome build of ClinVar file
        """
        update_message = ("The new version of the ClinVar"
                          + " {} annotation resource file".format(genome_build)
                          + " {} ({}) has been deployed".format(file_name,
                                                                date)
                          + " into 001_reference.")
        self.send_message(channel, update_message)

    def announce_config_update(self, channel, file_name, assay,
                               genome_build, clinvar_version):
        """announces VEP config update to team

        Args:
            channel (str): name of slack channel to post to
            file_name (_type_): file name of config file
            genome_build (str): genome build of config ClinVar file
        """
        vcf_name = "clinvar_{}_{}.vcf.gz".format(clinvar_version, genome_build)
        tbi_name = (vcf_name + ".tbi")
        update_message = ("The latest version of the {}".format(assay)
                          + " vep config file has been deployed into the 001"
                          + " reference project as {}.".format(file_name)
                          + "\nThe update consists of updating the ClinVar"
                          + " annotation resource files specificed to"
                          + " {} and {}."
                          .format(vcf_name, tbi_name))
        self.send_message(channel, update_message)

    def announce_workflow_update(self, channel, file_name, vep_config_name):
        """announces workflow update to team

        Args:
            channel (str): name of slack channel to post to
            file_name (_type_): file name of workflow
        """
        update_message = ("The latest version of the Helios reports workflow"
                          + " has been deployed into the 001"
                          + " reference project as {}.".format(file_name)
                          + "\nThe update consists of updating the Helios VEP"
                          + (" config file specificed to {}"
                             .format(vep_config_name)))
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
        full_message = "🔥 Prometheus: " + message

        http = requests.Session()
        retries = Retry(total=5, backoff_factor=10, allowed_methods=['POST'])
        http.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            response = http.post(
                'https://slack.com/api/chat.postMessage', {
                    'token': self.slack_token,
                    'channel': "#{}".format(channel),
                    'text': full_message
                }).json()

            if not response['ok']:
                # error in sending slack notification
                raise Exception("Error sending slack notification: {}"
                      .format(response.get('error')))
        except Exception as err:
            raise Exception("Error sending post request for slack "
                            + "notification: {}".format(err))
