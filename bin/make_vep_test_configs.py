"""
Generates vep config files for development and production ClinVar vcfs
"""

import dxpy
import shutil

import utils


def generate_config_files(dev_version, dev_annotation_file_id,
                          dev_index_file_id, dev_proj_id, ref_proj_id):
    """generates vep config files for dev and prod ClinVar files

    Args:
        dev_version (str): version of dev vcf file
        dev_annotation_file_id (str): DNAnexus file ID for dev vcf file
        dev_index_file_id (str): DNAnexus file ID for dev tbi file
        dev_proj_id (str): DNAnexus project ID for 003 dev project
        ref_proj_id (str): DNAnexus project ID for 001 reference project

    Returns:
        dev_id: str
            DNAnexus file ID for dev vep config file
        prod_id: str
            DNAnexus file ID for prod vep config file
    """
    # make prod testing file from template
    (prod_version, prod_annotation_file_id,
        prod_index_file_id) = utils.get_prod_version(ref_proj_id,
                                                     "/annotation/b37/clinvar",
                                                     "b37")
    prod_filename = ("Clinvar_annotation_vep_config_prod_"
                     + "{}.json".format(prod_version))
    prod_output_path = "temp/{}".format(prod_filename)
    path_to_prod = make_config_file(prod_output_path, prod_annotation_file_id,
                                    prod_index_file_id)

    # make dev testing file from template
    dev_filename = ("Clinvar_annotation_vep_config_dev_"
                    + "{}.json".format(dev_version))
    dev_output_path = "temp/{}".format(dev_filename)
    path_to_dev = make_config_file(dev_output_path, dev_annotation_file_id,
                                   dev_index_file_id)

    # upload prod and dev files to DNAnexus via dxpy
    subfolder = ("ClinVar_version_{}".format(dev_version)
                 + "_annotation_resource_update")
    folder_path = "/{}/Testing".format(subfolder)

    dev_file = dxpy.upload_local_file(filename=path_to_dev,
                                      project=dev_proj_id,
                                      folder=folder_path)
    prod_file = dxpy.upload_local_file(filename=path_to_prod,
                                       project=dev_proj_id,
                                       folder=folder_path)

    dev_id = dev_file.get_id()
    prod_id = prod_file.get_id()

    return dev_id, prod_id


def make_config_file(filename, annotation_file_id, index_file_id):
    """makes vep config file from template

    Args:
        filename (str): name of vep config file to be output
        annotation_file_id (str): DNAnexus file ID of vcf file
        index_file_id (str): DNAnexus file ID of vcf index file

    Returns:
        str: path to config file created
    """
    # copy template file and rename
    shutil.copy("resources/template_VEP_Config.json", filename)

    # replace CLINVAR_VCF_FILE_ID and CLINVAR_VCF_TBI_FILE_ID and save
    with open(filename, 'r') as file:
        file_data = file.read()
    file_data = file_data.replace("CLINVAR_VCF_FILE_ID", annotation_file_id)
    file_data = file_data.replace("CLINVAR_VCF_TBI_FILE_ID", index_file_id)
    with open(filename, 'w') as file:
        file.write(file_data)

    return filename
