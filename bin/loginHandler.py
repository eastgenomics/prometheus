"""
Handles all logins for Prometheus
"""

import dxpy as dx
import sys
import logging

class LoginHandler:

    def login(self) -> None:
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
        except Exception as err:
            logger.error("Error logging in to DNAnexus")
            sys.exit(1)

        
    def load_credential_info(self):
        """
        Load the tokens and Jira email from the credentials.json file

        Returns
        -------
        None
        """
        # Get tokens etc from credentials file
        with open(
            ROOT_DIR.joinpath("credentials.json"), "r", encoding='utf8'
        ) as json_file:
            credentials = json.load(json_file)

        self.dx_token = credentials.get('DX_TOKEN')
        self.jira_email = credentials.get('JIRA_EMAIL')
        self.jira_token = credentials.get('JIRA_TOKEN')
        self.staging_proj_id = credentials.get('STAGING_AREA_PROJ_ID')
        self.default_months = credentials.get('DEFAULT_MONTHS')

        return dx_token, jira_email, jira_token, staging_proj_id, default_months