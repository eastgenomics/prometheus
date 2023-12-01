from .context import inspect_workflow_logs as iwl
import unittest

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):
    def test_inspect_workflow_info(self):
        analysis_id = "analysis-GbYVXPj4FK2zjPzgf72P9ybK"
        workflow_name = "TSO500_reports_workflow_v1.3.2"
        test_passed, results_file = iwl.inspect_workflow_info(analysis_id,
                                                              workflow_name)
        os.remove(results_file)
        assert test_passed
        output_filename = ("temp/{}_helios_workflow_testing_summary.txt"
                           .format("pass"))
        assert results_file == output_filename

        workflow_name = "TSO500_reports_workflow_v1.3.1"
        test_passed, results_file = iwl.inspect_workflow_info(analysis_id,
                                                              workflow_name)
        os.remove(results_file)
        assert not test_passed
        output_filename = ("temp/{}_helios_workflow_testing_summary.txt"
                           .format("fail"))
        assert results_file == output_filename

    def test_generate_workflow_summary(self):
        filename = "temp/unittest_file.txt"
        test_passed = True
        workflow_name = "my_workflow"
        iwl.generate_workflow_summary(filename,
                                      test_passed,
                                      workflow_name)
        file_exists = os.path.isfile(filename)
        assert file_exists
        if file_exists:
            os.remove(filename)

    def test_inspect_vep_logs(self):
        log_path = "temp/unittest_vep_job_log.txt"
        log_lines = ["2023-11-17 08:53:55 eggd_vep STDERR + local file=/home/dnanexus/in/config_file/my_config.json\n",
                     "2023-11-17 08:53:53 eggd_vep STDERR + ANNOTATION_STRING+=/data/clinvar_12345678_b37.vcf.gz,\n",
                     "/usr/bin/time -v docker run.+clinvar_12345678_b37.vcf.gz\n"]
        with open(log_path, "w") as file:
            file.writelines(log_lines)

        config_name = "tso500_vep_config_v1.2.1.json"
        clinvar_version = "12345678"
        job_id = "job-GbYVXQ04FK2zjPzgf72P9ybb"
        test_passed, results_file = iwl.inspect_vep_logs(log_path,
                                                         job_id,
                                                         config_name,
                                                         clinvar_version)
        os.remove(results_file)
        assert test_passed
        output_filename = ("temp/{}_helios_workflow_vep_testing_summary.txt"
                           .format("pass"))
        assert results_file == output_filename

        config_name = "my_incorrect_config.json"
        clinvar_version = "87654321"
        job_id = "job-GbYVXQ04FK2zjPzgf72P9ybb"
        test_passed, results_file = iwl.inspect_vep_logs(log_path,
                                                         job_id,
                                                         config_name,
                                                         clinvar_version)
        os.remove(results_file)
        assert not test_passed
        output_filename = ("temp/{}_helios_workflow_vep_testing_summary.txt"
                           .format("fail"))
        assert results_file == output_filename

        os.remove(log_path)

    def test_generate_vep_summary(self):
        filename = "temp/unittest_file.txt"
        config_matched = True
        clinvar_line = "this is the line containing clinvar_20230101.vcf"
        clinvar_version = "20230101"
        vep_config_name = "vep_config.json"
        job_id = "job-4242424242"
        iwl.generate_vep_summary(filename,
                                 job_id,
                                 config_matched,
                                 clinvar_line,
                                 clinvar_version,
                                 vep_config_name)
        file_exists = os.path.isfile(filename)
        assert file_exists
        if file_exists:
            os.remove(filename)
