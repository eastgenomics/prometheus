"""
Inspects the contents of VEP log files searching for specific strings
"""

from .utils import search_for_regex

regex_config_location = "resources/annotation_regex.json"
output_location = "temp"


def inspect_logs(
    log_file, job_id, config_name, vcf_name, assay
) -> tuple[bool, str]:
    """checks that specified config and vcf names are present in logs

    Args:
        log_file (str): file path of log file
        job_id (str): ID of log file job
        config_name (str): name of config to search for
        vcf_name (str): name of vcf to search for
        assay (str): assay name

    Returns:
        test_passed (bool): has inspection of logs passed
        output_file (str): path to report summary file generated
    """
    # check config_name is present in logs
    # output all lines containing config_name as human-readable text
    config_results = search_for_regex(log_file, config_name)
    vcf_results = search_for_regex(log_file, vcf_name)

    if (len(config_results) > 0 and len(vcf_results) > 0):
        test_passed = True
    else:
        test_passed = False

    pass_fail = pass_fail_to_text(test_passed)
    output_filename = f"temp/{pass_fail}_{assay}_testing_summary.txt"
    output_file = generate_test_summary(
        output_filename, test_passed, config_name, vcf_name,
        config_results, vcf_results, job_id
    )

    return test_passed, output_file


def generate_test_summary(
    filename, test_passed, config_name, vcf_name, config_results, vcf_results,
    job_id
) -> str:
    """generates a summary of log file testing performed

    Args:
        filename (str): path to summary file to be generated
        test_passed (bool): has log file passed testing
        config_name (str): name of config file searched for
        vcf_name (str): name of vcf file searched for
        config_results (list (str)): list of lines containing config file
        vcf_results (list (str)): list of lines containing vcf file
        job_id (str): ID of log file job

    Returns:
        filename (str): path to summary file generated
    """
    with open(filename, "w") as f:
        test_results = pass_fail_to_text(test_passed)
        f.write(f"Overall testing result: {test_results}\n\n")
        f.write(f"DNAnexus Job ID: {job_id}\n\n")
        config_line_count = len(config_results)
        vcf_line_count = len(vcf_results)

        write_summary_content(
            f, True, config_name, config_line_count, config_results
        )
        write_summary_content(
            f, False, vcf_name, vcf_line_count, vcf_results
        )

    return filename


def write_summary_content(
        file, include_linebreaks, file_name, line_count, results
):
    """writes content to summary file

    Args:
        f (TextIOWrapper): text IO wrapper for wriitng to file
        include_linebreaks (bool): sould 2 new lines be included after content
        file_name (str): name of file being commented on
        line_count (int): number of lines found within file summarised
        results (list[str]): list containing strings found in file summarised
    """
    file.write(f"Name of new config file: {file_name}\n")
    if line_count > 0:
        file.write(
            f"Pass: There were {line_count}"
            + f" lines containing \"{file_name}\"\n"
        )
        file.write("Lines containing new file name:\n\n")
        for line in results:
            file.write(line)
    else:
        file.write(
            f"Fail: There were {line_count} lines"
            + f" containing \"{file_name}\"\n"
        )
    if include_linebreaks:
        file.write("\n\n")


def pass_fail_to_text(has_passed) -> str:
    """converts boolean to Pass or Fail

    Args:
        has_passed (bool): has test passed

    Returns:
        str: Pass or Fail
    """
    if has_passed:
        return "Pass"
    else:
        return "Fail"
