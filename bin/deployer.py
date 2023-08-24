"""
Deploys most recent clinvar annotation resource files to 001
"""

from dxpy.bindings.dxfile_functions import open_dxfile
from dxpy.bindings.dxproject import DXProject
from dxpy import upload_local_file

import utils


def deploy_clinvar_to_production(reference_project_id, dev_project_id,
                                 vcf_file_id, tbi_file_id, deploy_folder):
    """move vcf file and vcf.tbi file to 001 reference project

    Args:
        reference_project_id (str): DNAnexus ID of 001 reference project
        dev_project_id (str): DNAnexus ID of 003 development project
        vcf_file_id (str): DNAnexus ID of vcf file to upload
        tbi_file_id (str): DNAnexus ID of tbi file to upload
        deploy_folder (str): DNAnexus project folder to upload to

    Raises:
        Exception: project folder does not exist
    """
    if not utils.check_proj_folder_exists(reference_project_id, deploy_folder):
        raise Exception("Folder {} does not exist in project {}"
                        .format(deploy_folder, reference_project_id))

    with open_dxfile(dxid=vcf_file_id, project=dev_project_id) as vcf_file:
        vcf_file.clone(project=reference_project_id, folder=deploy_folder)
        vcf_file.close()

    with open_dxfile(dxid=tbi_file_id, project=dev_project_id) as tbi_file:
        tbi_file.clone(project=reference_project_id, folder=deploy_folder)
        vcf_file.close()


def deploy_testing_to_development(dev_project_id, clinvar_version, added_csv,
                                  deleted_csv, changed_csv, job_report):
    """uploads all files output from testing to subfolder of 003 dev project

    Args:
        dev_project_id (str): DNAnexus ID of 003 development project
        clinvar_version (str): current version of ClinVar file
        added_csv (str): path to added csv
        deleted_csv (str): path to deleted csv
        changed_csv (str): path to changed csv
        job_report (str): path to job report txt file

    Returns:
        added_id: str
            DNAnexus file ID for added csv
        deleted_id: str
            DNAnexus file ID for deleted csv
        changed_id: str
            DNAnexus file ID for changed csv
        job_report_id: str
            DNAnexus file ID for txt file containing job IDs
    """
    subfolder = "ClinVar_version_{}".format(clinvar_version)
    + "_annotation_resource_update"
    folder_path = "/{}/Evidence".format(subfolder)

    # make new subfolder for documenting evidence
    dev_project = DXProject(dev_project_id)
    dev_project.new_folder(folder_path, parents=True)

    added_id = upload_local_file(filename=added_csv,
                                 project=dev_project_id,
                                 folder=folder_path)
    deleted_id = upload_local_file(filename=deleted_csv,
                                   project=dev_project_id,
                                   folder=folder_path)
    changed_id = upload_local_file(filename=changed_csv,
                                   project=dev_project_id,
                                   folder=folder_path)
    job_report_id = upload_local_file(filename=job_report,
                                      project=dev_project_id,
                                      folder=folder_path)

    return added_id, deleted_id, changed_id, job_report_id
