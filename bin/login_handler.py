"""
Handles all logins for Prometheus
"""

import sys

import dxpy as dx
import logging
import json


class LoginHandler:
    """Handles all logins for Prometheus
    """
    def __init__(self):
        """loads credentials
        """
        (self.dx_token,
         self.slack_token,
         self.github_token) = self.load_credentials()

    def login_DNAnexus(self, dev_proj_id) -> None:
        """logs into DNAnexus

        Raises:
            Exception: DNAnexus user authentification check fails
        """
        DX_SECURITY_CONTEXT = {
            "auth_token_type": "Bearer",
            "auth_token": self.dx_token
        }

        # Set up logger
        logger = logging.getLogger("main log")

        dx.set_security_context(DX_SECURITY_CONTEXT)
        # to prevent files being accidentally generated outside of dev project
        dx.set_workspace_id(dev_proj_id)

        try:
            dx.api.system_whoami()
            logger.info("DNAnexus login successful")
        except Exception:
            logger.error("Error logging in to DNAnexus")
            sys.exit(1)

    def load_credentials(self):
        """loads credentials from json file

        Returns:
        dx_token: string
            API token for DNAnexus
        slack_token: string
            API token for Slack
        """
        # Get tokens etc from credentials file
        location = "resources/credentials.json"
        with open(location, "r", encoding='utf8') as json_file:
            creds = json.load(json_file)

        dx_token = creds.get('DX_TOKEN')
        slack_token = creds.get('SLACK_TOKEN')
        github_token = creds.get('GITHUB_TOKEN')

        return dx_token, slack_token, github_token
