"""
Contains utility functions used in multiple modules
"""

import time

import dxpy
from dxpy.bindings.dxproject import DXProject


def check_jobs_finished(job_id_list, timer, max_wait_time):
    """checks if jobs have finished or until max time has elapsed

    Args:
        job_id_list (str): DNAnexus job IDs to check if completed
        timer (int): interval to check in (minutes)
        max_wait_time (int): max wait time
    """
    job_list = []

    # check that all jobs exist
    for job_id in job_id_list:
        try:
            job_list.append(dxpy.bindings.dxjob.DXJob(job_id))
        except dxpy.exceptions.DXError:
            raise IOError("DNAnexus job {} not found".format(job_id))

    time_elapsed = 0

    # check for job to complete until max wait time is reached
    while time_elapsed < max_wait_time:
        jobs_completed = 0
        for job in job_list:
            # check if job is done
            job_state = job.describe()["state"]
            if job_state == "done":
                jobs_completed += 1
            else:
                break

        if jobs_completed >= len(job_list):
            break
        else:
            # wait for [timer] minutes
            time.sleep(timer*60)
            time_elapsed += timer


def check_project_exists(project_id):
    """checks if a DNAnexus project exists from project ID

    Args:
        project_id (str): DNAnexus project ID

    Returns:
        bool: does the specified project exist
    """
    try:
        DXProject(project_id)
        return True
    except dxpy.exceptions.DXError:
        return False


def check_proj_folder_exists(project_id, folder_path):
    """checks if a DNAnexus folder exists in a given project

    Args:
        project_id (str): DNAnexus project ID
        folder_path (str): path to DNAnexus folder

    Raises:
        Exception: project not found

    Returns:
        bool: does folder exist in project
    """
    if not check_project_exists(project_id):
        raise Exception("Project {} does not exist".format(project_id))

    try:
        dxpy.api.project_list_folder(
            project_id,
            input_params={"folder": folder_path, "only": "folders"},
            always_retry=True
        )
        return True
    except dxpy.exceptions.ResourceNotFound:
        return False
