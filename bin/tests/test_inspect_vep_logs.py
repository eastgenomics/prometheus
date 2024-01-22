from .context import inspect_vep_logs as ivl
import unittest

import os
os.chdir("..")
os.chdir("..")


class testInspectVepLogs(unittest.TestCase):
    def test_inspect_logs_pass(self):
        """test that inspect_vep_logs passes with correct file name
        when provided with data which should cause testing to pass
        """
        log_path = "temp/unittest_vep_job_log.txt"
        log_lines = [
            "2023-11-17 08:53:55 eggd_vep STDERR + local file=/home/dnanexus/in/config_file/my_config.json\n",
            "2023-11-17 08:53:53 eggd_vep STDERR + ANNOTATION_STRING+=/data/clinvar_12345678_b37.vcf.gz,\n"
        ]
        with open(log_path, "w") as file:
            file.writelines(log_lines)

        config_name = "my_config.json"
        vcf_name = "clinvar_12345678_b37.vcf"
        assay = "TSO500"
        vep_job = "job-myvepjob12345"
        test_passed, results_file = ivl.inspect_logs(
            log_path, vep_job, config_name, vcf_name, assay)
        os.remove(results_file)
        output_filename = f"temp/pass_{assay}_testing_summary.txt"
        assert (
            test_passed
            and results_file == output_filename
        )

    def test_inspect_logs_fail(self):
        """test that inspect_vep_logs fails with correct file name
        when provided with data which should cause testing to fail
        """
        log_path = "temp/unittest_vep_job_log.txt"
        log_lines = [
            "2023-11-17 08:53:55 eggd_vep STDERR + local file=/home/dnanexus/in/config_file/my_config.json\n",
            "2023-11-17 08:53:53 eggd_vep STDERR + ANNOTATION_STRING+=/data/clinvar_12345678_b37.vcf.gz,\n"
        ]
        with open(log_path, "w") as file:
            file.writelines(log_lines)

        config_name = "my_incorrect_config.json"
        vcf_name = "clinvar_87654321_b37.vcf"
        assay = "TSO500"
        vep_job = "job-myvepjob54321"
        test_passed, results_file = ivl.inspect_logs(
            log_path, vep_job, config_name, vcf_name, assay
        )
        os.remove(results_file)
        output_filename = f"temp/fail_{assay}_testing_summary.txt"
        assert (
            not test_passed
            and results_file == output_filename
        )

        os.remove(log_path)

    def test_generate_test_summary(self):
        """test that generate_test_summary generates summary file
        """
        filename = "temp/unittest_file.txt"
        test_passed = True
        config_name = "config.json"
        vcf_name = "clinvar.vcf"
        config_results = ["aaa", "bb", "c"]
        vcf_results = ["d", "ee", "fff"]
        job_id = "job-4242424242"
        ivl.generate_test_summary(
            filename, test_passed, config_name, vcf_name, config_results,
            vcf_results, job_id
        )
        file_exists = os.path.isfile(filename)
        assert file_exists
        if file_exists:
            os.remove(filename)
