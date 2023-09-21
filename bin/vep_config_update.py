"""
Runs prometheus ClinVar vep config
This program is to be run on a DNAnexus node once a week as
new clinvar updates come in
"""
import json
import logging

from get_clinvar_files import get_ftp_files, retrieve_clinvar_files
import make_vep_test_configs as vep
import vep_testing
import deployer
from login_handler import LoginHandler
from slack_handler import SlackHandler
from progress_tracker import ClinvarProgressTracker as Tracker

logger = logging.getLogger("main log")


def run_vep_config_update(bin_folder, assay):
    # download latest vep config for genome build and assay
    # replace old clinvar version with new version and increment version number
    # upload new config file to 003 project
    pass

    # run vep using updated config file and record results to 003 project
    pass

    # test results automatically to ensure results are valid
    # fail and exit prometheus and notify team if results are invalid
    pass

    # deploy new config to 001 referenc eproject
    pass

    # notify team of completed vep config update
    pass


if __name__ == "__main__":
    # TODO: send either "bin" or "nextflow-bin" from nextflow script depending
    # on where program is run
    # This will either be "bin" for local, or "nextflow-bin" for running it as
    # a DNAnexus app/applet
    # TODO: send the assay name from nextflow script
    run_vep_config_update("bin", "TWE", "b37")
