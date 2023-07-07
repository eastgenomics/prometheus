"""
Deploys most recent clinvar annotation resource files to 001
"""

import dxpy

def deploy_clinvar_to_production(reference_project_id, vcf_file_id, tbi_file_id):
    # move vcf file and vcf.tbi file to 001 reference project
    ref_folder = "annotation/b37/clinvar"

    vcf_file = dxpy.bindings.DXObject(dxid=vcf_file_id)
    vcf_file.clone(project=reference_project_id, folder=ref_folder)

    tbi_file = dxpy.bindings.DXObject(dxid=tbi_file_id)
    tbi_file.clone(project=reference_project_id, folder=ref_folder)

def deploy_testing_to_development(dev_project_id, clinvar_version, added_csv, deleted_csv, changed_csv, job_report):
    # upload .csv files generated earlier to subfolder of 003 project
    subfolder = "ClinVar_version_{}_annotation_resource_update".format(clinvar_version)
    folder_path = "{}/Evidence".format(subfolder)

    added_id = dxpy.upload_local_file(filename=added_csv, project=dev_project_id, folder=folder_path)
    deleted_id = dxpy.upload_local_file(filename=deleted_csv, project=dev_project_id, folder=folder_path)
    changed_id = dxpy.upload_local_file(filename=changed_csv, project=dev_project_id, folder=folder_path)
    job_report_id = dxpy.upload_local_file(filename=job_report, project=dev_project_id, folder=folder_path)

    return added_id, deleted_id, changed_id, job_report_id
