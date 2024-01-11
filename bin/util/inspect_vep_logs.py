"""
Inspects the contents of VEP log files searching for specific strings
"""

from utils import search_for_regex

regex_config_location = "resources/annotation_regex.json"
output_location = "temp"


def inspect_logs(log_file, job_id, config_name, vcf_name, assay):
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

    if test_passed:
        pass_fail = "pass"
    else:
        pass_fail = "fail"
    output_filename = ("temp/{}_{}_testing_summary.txt".format(pass_fail,
                                                               assay))
    output_file = generate_test_summary(output_filename,
                                        test_passed,
                                        config_name,
                                        vcf_name,
                                        config_results,
                                        vcf_results,
                                        job_id)

    return test_passed, output_file


def generate_test_summary(filename, test_passed, config_name, vcf_name,
                          config_results, vcf_results, job_id):
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
        if test_passed:
            test_results = "Pass"
        else:
            test_results = "Fail"
        f.write("Overall testing result: {}\n\n".format(test_results))
        f.write("DNAnexus Job ID: {}\n\n".format(job_id))
        f.write("Name of new config file: {}\n".format(config_name))
        config_line_count = len(config_results)
        if config_line_count > 0:
            f.write("Pass: There were {} lines containing \"{}\"\n"
                    .format(config_line_count, config_name))
            f.write("Lines containing new config file name:\n\n")
            for line in config_results:
                f.write(line)
        else:
            f.write("Fail: There were {} lines containing \"{}\"\n"
                    .format(config_line_count, config_name))
        f.write("\n\n")

        f.write("Name of new vcf file: {}\n\n".format(vcf_name))
        vcf_line_count = len(vcf_results)
        if vcf_line_count > 0:
            f.write("Pass: There were {} lines containing \"{}\"\n"
                    .format(vcf_line_count, vcf_name))
            f.write("Lines containing new vcf file name:\n\n")
            for line in vcf_results:
                f.write(line)
        else:
            f.write("Fail: There were {} lines containing \"{}\"\n"
                    .format(vcf_line_count, vcf_name))

    return filename
