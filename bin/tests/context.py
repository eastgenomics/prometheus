import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import compare_annotation
import deployer
import get_clinvar_files
import login_handler
import annotation_update as annotation_update
import make_vep_test_configs
import slack_handler
import utils
import vep_testing
import progress_tracker
