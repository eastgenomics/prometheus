"""
Inspects the contents of reports workflow log files for specific strings
"""

import re
import dxpy
import utils

regex_config_location = "resources/annotation_regex.json"
output_location = "temp"


def inspect_workflow_info(analysis_id, workflow_name):
    """checks that correct workflow name is present in analysis

    Args:
        analysis_id (str): DNAnexus analysis ID
        workflow_name (str): name of workflow

    Returns:
        test_passed (bool): has inspection of logs passed
        output_file (str): path to report summary file generated
    """
    analysis = dxpy.bindings.dxanalysis.DXAnalysis(analysis_id)
    analysis_description = analysis.describe()
    workflow_name_found = analysis_description["executableName"]
    if workflow_name == workflow_name_found:
        test_passed = True
        pass_fail = "pass"
    else:
        test_passed = False
        pass_fail = "fail"

    output_filename = ("temp/{}_helios_workflow_testing_summary.txt"
                       .format(pass_fail))
    summary = generate_workflow_summary(output_filename,
                                        test_passed,
                                        workflow_name)
    return test_passed, summary


def inspect_vep_logs(log_file, job_id, vep_config_name, clinvar_version):
    """checks that correct vep config name and clinvar version are in log

    Args:
        log_file (str): path to log file
        job_id (str): DNAnexus ID of log job
        vep_config_name (str): vep config name to be searched for
        clinvar_version (str): version of clinvar to be searched for

    Returns:
        test_passed (bool): has inspection of logs passed
        output_file (str): path to report summary file generated
    """
    vep_job = dxpy.bindings.dxapplet.DXJob(job_id)
    description = vep_job.describe(io=True)
    # get input from description
    config_matched = False
    input = description["input"]["config_file"]["$dnanexus_link"]
    name = utils.find_file_name_from_id(input)
    if name == vep_config_name:
        config_matched = True

    clinvar_regex = (r"/usr/bin/time -v docker run.+clinvar_"
                     + clinvar_version
                     + r"_b37.vcf.gz")
    clinvar_results = search_for_regex(log_file, clinvar_regex)

    clinvar_line = ""
    if (len(clinvar_results) > 0 and config_matched):
        pass_fail = "pass"
        test_passed = True
        clinvar_line = clinvar_results[0]
    else:
        pass_fail = "fail"
        test_passed = False

    output_filename = ("temp/{}_helios_workflow_vep_testing_summary.txt"
                       .format(pass_fail))
    summary = generate_vep_summary(output_filename,
                                   job_id,
                                   config_matched,
                                   clinvar_line,
                                   clinvar_version,
                                   vep_config_name)

    return test_passed, summary


def generate_workflow_summary(filename, test_passed, workflow_name):
    """generates a summary file of workflow testing

    Args:
        filename (str): path to summary file to be generated
        test_passed (bool): has testing passed
        workflow_name (str): name of workflow

    Returns:
        filename (str): path to summary file generated
    """
    with open(filename, "w") as f:
        if test_passed:
            test_results = "Pass"
        else:
            test_results = "Fail"
        f.write("Testing result: {}\n\n".format(test_results))
        if test_passed:
            f.write("Workflow name was found to be {}\n"
                    .format(workflow_name))
        else:
            f.write("Workflow name was not found to be {}\n"
                    .format(workflow_name))
    return filename


def generate_vep_summary(filename,
                         job_id,
                         config_matched,
                         clinvar_line,
                         clinvar_version,
                         vep_config_name):
    with open(filename, "w") as f:
        if config_matched and clinvar_line != "":
            test_results = "Pass"
        else:
            test_results = "Fail"
        f.write("Overall testing result: {}\n\n".format(test_results))
        f.write("Job ID: {}\n\n".format(job_id))
        f.write("Name of new vep config: {}\n".format(vep_config_name))
        if config_matched:
            f.write("Pass: The config file \"{}\" was used as an input\n"
                    .format(vep_config_name))
        else:
            f.write("Fail: The config file \"{}\" was not used as an input\n"
                    .format(vep_config_name))
        f.write("\n")
        f.write("New clinvar version: {}\n"
                .format(clinvar_version))
        if clinvar_line != "":
            f.write("Pass: Clinvar version {} was present in the logs\n"
                    .format(clinvar_version))
            f.write("Line containing correct clinvar version:\n")
            f.write(clinvar_line + "\n")
        else:
            f.write("Fail: Clinvar version {} was not present in the logs\n"
                    .format(clinvar_version))

    return filename


def search_for_regex(log_file, regex):
    """returns all lines containing regex in text file

    Args:
        log_file (str): path to log file
        regex (str): regex to search for

    Returns:
        list (str): all lines in file containing regex
    """
    regex = re.compile(regex)
    results = []
    with open(log_file) as f:
        for line in f:
            result = regex.search(line)
            if result:
                results.append(line)
    return results
