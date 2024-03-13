from bin.util import inspect_vep_logs as ivl
import unittest
from unittest import mock
from unittest.mock import patch, mock_open
import os


class testInspectVepLogs(unittest.TestCase):
    def test_inspect_logs_pass(self):
        """test that inspect_vep_logs passes with correct file name
        when provided with data which should cause testing to pass
        """
        log_path = "temp/unittest_vep_job_log.txt"
        log_lines = (
            "2023-11-17 08:53:55 eggd_vep STDERR + local file=/home/dnanexus/in/config_file/my_config.json\n"
            + "2023-11-17 08:53:53 eggd_vep STDERR + ANNOTATION_STRING+=/data/clinvar_12345678_b37.vcf.gz,\n"
        )

        config_name = "my_config.json"
        vcf_name = "clinvar_12345678_b37.vcf"
        assay = "TSO500"
        vep_job = "job-myvepjob12345"
        with patch("builtins.open", mock_open(read_data=log_lines)):
            test_passed, results_file = ivl.inspect_logs(
                log_path, vep_job, config_name, vcf_name, assay
            )
        output_filename = f"temp/pass_{assay}_testing_summary.txt"
        with self.subTest():
            assert test_passed
        with self.subTest():
            assert results_file == output_filename

    def test_inspect_logs_fail(self):
        """test that inspect_vep_logs fails with correct file name
        when provided with data which should cause testing to fail
        """
        log_path = "temp/unittest_vep_job_log.txt"
        log_lines = (
            "2023-11-17 08:53:55 eggd_vep STDERR + local file=/home/dnanexus/in/config_file/my_config.json\n"
            + "2023-11-17 08:53:53 eggd_vep STDERR + ANNOTATION_STRING+=/data/clinvar_12345678_b37.vcf.gz,\n"
        )

        config_name = "my_incorrect_config.json"
        vcf_name = "clinvar_87654321_b37.vcf"
        assay = "TSO500"
        vep_job = "job-myvepjob54321"
        with patch("builtins.open", mock_open(read_data=log_lines)):
            test_passed, results_file = ivl.inspect_logs(
                log_path, vep_job, config_name, vcf_name, assay
            )
        output_filename = f"temp/fail_{assay}_testing_summary.txt"
        print(f"{results_file} == {output_filename}")
        with self.subTest():
            assert not test_passed
        with self.subTest():
            assert results_file == output_filename

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_test_summary(self, mock_write):
        """test that generate_test_summary generates summary file
        """
        filename = "temp/unittest_file.txt"
        test_passed = True
        config_name = "config.json"
        vcf_name = "clinvar.vcf"
        config_results = ["aaa", "bb", "c"]
        vcf_results = ["d", "ee", "fff"]
        job_id = "job-4242424242"
        with self.subTest():
            assert ivl.generate_test_summary(
                filename, test_passed, config_name, vcf_name, config_results,
                vcf_results, job_id
            ) == filename

        # check the correct file name is written to file
        with self.subTest():
            mock_write.assert_called_once_with(
                filename, "w"
            )

        # check the expected contents are written to file
        with self.subTest():
            mock_write.assert_has_calls(
                [
                    mock.call().write(
                        "Overall testing result: pass\n\n"
                    ),
                    mock.call().write(
                        "DNAnexus Job ID: job-4242424242\n\n"
                    ),
                    mock.call().write(
                        "Name of new config file: config.json\n"
                    ),
                    mock.call().write(
                        "Pass: There were 3 lines containing \"config.json\"\n"
                    ),
                    mock.call().write(
                        "Lines containing new file name:\n\n"
                    ),
                    mock.call().write(
                        "aaa"
                    ),
                    mock.call().write(
                        "bb"
                    ),
                    mock.call().write(
                        "c"
                    ),
                    mock.call().write(
                        "\n\n"
                    ),
                    mock.call().write(
                        "Name of new config file: clinvar.vcf\n"
                    ),
                    mock.call().write(
                        "Pass: There were 3 lines containing \"clinvar.vcf\"\n"
                    ),
                    mock.call().write(
                        "Lines containing new file name:\n\n"
                    ),
                    mock.call().write(
                        "d"
                    ),
                    mock.call().write(
                        "ee"
                    ),
                    mock.call().write(
                        "fff"
                    ),
                ]
            )


if __name__ == "__main__":
    unittest.main()
