"""
Deploys files from 003 project to 001 project
"""

from dxpy.bindings.dxfile_functions import open_dxfile
from dxpy.bindings.dxproject import DXProject
from dxpy import upload_local_file
from dxpy.bindings.dxworkflow import DXWorkflow

from .utils import check_proj_folder_exists


def deploy_config_to_production(
    reference_project_id, dev_project_id, config_id, deploy_folder
) -> None:
    """move config file to 001 reference project

    Args:
        reference_project_id (str): DNAnexus ID of 001 reference project
        dev_project_id (str): DNAnexus ID of 003 development project
        config_id (str): DNAnexus ID of config file to upload
        deploy_folder (str): DNAnexus project folder to upload to

    Raises:
        Exception: project folder does not exist
    """
    if not check_proj_folder_exists(reference_project_id, deploy_folder):
        raise Exception(
            f"Folder {deploy_folder} does not exist"
            + f" in project {reference_project_id}"
        )

    with open_dxfile(dxid=config_id, project=dev_project_id) as file:
        file.clone(project=reference_project_id, folder=deploy_folder)
        file.close()


def deploy_workflow_to_production(
    reference_project_id, dev_project_id, workflow_id, deploy_folder
) -> None:
    """move workflow file to 001 reference project

    Args:
        reference_project_id (str): DNAnexus ID of 001 reference project
        dev_project_id (str): DNAnexus ID of 003 development project
        config_id (str): DNAnexus ID of workflow file to upload
        deploy_folder (str): DNAnexus project folder to upload to

    Raises:
        Exception: project folder does not exist
    """
    if not check_proj_folder_exists(reference_project_id, deploy_folder):
        raise Exception(f"Folder {deploy_folder} does not exist"
                        + f" in project {reference_project_id}")
    workflow = DXWorkflow(dxid=workflow_id, project=dev_project_id)
    workflow.clone(project=reference_project_id, folder=deploy_folder)


def deploy_clinvar_to_production(
    reference_project_id, dev_project_id, vcf_file_id, tbi_file_id,
    deploy_folder
) -> None:
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
    if not check_proj_folder_exists(reference_project_id, deploy_folder):
        raise Exception(
            f"Folder {deploy_folder} does not exist"
            + f" in project {reference_project_id}"
        )

    for file_id in [vcf_file_id, tbi_file_id]:
        with open_dxfile(dxid=file_id, project=dev_project_id) as file:
            file.clone(project=reference_project_id, folder=deploy_folder)
            file.close()


def deploy_testing_to_development(
    dev_project_id, clinvar_version, added_csv, deleted_csv, changed_csv,
    detailed_csv, job_report
) -> None:
    """uploads all files output from testing to subfolder of 003 dev project

    Args:
        dev_project_id (str): DNAnexus ID of 003 development project
        clinvar_version (str): current version of ClinVar file
        added_csv (str): path to added csv
        deleted_csv (str): path to deleted csv
        changed_csv (str): path to changed csv
        detailed_csv (str): path to detailed csv
        job_report (str): path to job report txt file

    Returns:
        added_id: str
            DNAnexus file ID for added csv
        deleted_id: str
            DNAnexus file ID for deleted csv
        changed_id: str
            DNAnexus file ID for changed csv
        detailed_id: str
            DNAnexus file ID for detailed csv
        job_report_id: str
            DNAnexus file ID for txt file containing job IDs
    """
    subfolder = (
        f"ClinVar_version_{clinvar_version}"
        + "_annotation_resource_update"
    )
    folder_path = f"/{subfolder}/Evidence"

    # make new subfolder for documenting evidence
    dev_project = DXProject(dev_project_id)
    dev_project.new_folder(folder_path, parents=True)

    for csv_filename in [
        added_csv, deleted_csv, changed_csv, detailed_csv, job_report
    ]:
        upload_local_file(
            filename=csv_filename, project=dev_project_id, folder=folder_path
        )
