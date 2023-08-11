import dxpy
import time

def check_jobs_finished(job_id_list, timer, max_wait_time):
    # timer is in minutes (e.g., check if job is done every 2 minutes)
    # max wait time is in minutes (e.g., fail after waiting for > 20 minutes)
    # job_list is list of job IDs to be checked
    job_list = []

    for job_id in job_id_list:
        job_list.append(dxpy.bindings.dxjob.DXJob(job_id))

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