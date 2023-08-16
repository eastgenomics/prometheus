"""
Deploys most recent clinvar annotation resource files to 001
"""

from dxpy.bindings.dxfile_functions import open_dxfile
from dxpy.bindings.dxproject import DXProject
from dxpy import upload_local_file


def deploy_clinvar_to_production(reference_project_id, dev_project_id,
                                 vcf_file_id, tbi_file_id, deploy_folder):
    # move vcf file and vcf.tbi file to 001 reference project
    vcf_file = open_dxfile(dxid=vcf_file_id, project=dev_project_id)
    vcf_file.clone(project=reference_project_id, folder=deploy_folder)

    tbi_file = open_dxfile(dxid=tbi_file_id, project=dev_project_id)
    tbi_file.clone(project=reference_project_id, folder=deploy_folder)


def deploy_testing_to_development(dev_project_id, clinvar_version, added_csv,
                                  deleted_csv, changed_csv, job_report):
    # upload .csv files generated earlier to subfolder of 003 project
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
