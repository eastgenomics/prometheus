"""
Handles all logins for Prometheus
"""

import sys

import dxpy as dx
import logging
import json


class LoginHandler:
    def __init__(self):
        self.dx_token, self.slack_token = self.load_credentials()

    def login_DNAnexus(self) -> None:
        """
        Logs into DNAnexus
        Parameters
        ----------
        token : str
            authorisation token for DNAnexus, from credentials.json
        Raises
        ------
        Error
            Raised when DNAnexus user authentification check fails
        """
        DX_SECURITY_CONTEXT = {
            "auth_token_type": "Bearer",
            "auth_token": self.dx_token
        }

        # Set up logger
        logger = logging.getLogger("main log")

        dx.set_security_context(DX_SECURITY_CONTEXT)

        try:
            dx.api.system_whoami()
            logger.info("DNAnexus login successful")
        except Exception:
            logger.error("Error logging in to DNAnexus")
            sys.exit(1)

    def login_slack(self) -> None:
        print("logging into slack")

    def load_credentials(self):
        # Get tokens etc from credentials file
        location = "resources/credentials.json"
        with open(location, "r", encoding='utf8') as json_file:
            creds = json.load(json_file)

        dx_token = creds.get('DX_TOKEN')
        slack_token = creds.get('SLACK_TOKEN')

        return dx_token, slack_token
