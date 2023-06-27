"""
Runs prometheus
This program is to be run on a DNAnexus node once a week as new clinvar updates come in
"""

import getClinvarFiles
import makeVepTestConfigs as vep
import vepTesting
import confluenceHandler
import jiraHandler
import deployer
import announcer

def run_prometheus():
    # Step 1 - Fetch latest ClinVar files and add to new 003 project
    print("Fetching latest ClinVar annotation resource files")
    recent_vcf_file, recent_tbi_file, earliest_time, clinvar_version = getClinvarFiles.get_ftp_files()
    print("Downloading the clinvar annotation resource files {1} and {2} from {3}".format(recent_vcf_file,
    recent_tbi_file, earliest_time))
    project_id, clinvar_vcf_id, clinvar_tbi_id = getClinvarFiles.retrieve_clinvar_files(recent_vcf_file, recent_tbi_file, clinvar_version)

    # Step 2 - Make dev and prod VEP config files from template and store local paths
    print("Creating development and production config files from template")
    vep_config_dev, vep_config_prod = vep.generate_config_files(clinvar_version, clinvar_vcf_id, clinvar_tbi_id, project_id)

    # Step 3 - Run vep for dev and prod configs, find differences, get evidence of changes
    print("Running vep for development and production configs")
    (annotation_comparison, twe_diff, tso_diff, dev_twe_job, dev_tso_job, prod_twe_job,
    prod_tso_job) = vepTesting.perform_vep_testing(project_id, vep_config_dev, vep_config_prod)

    # Step 4 - generate confluence page and jira ticket
    print("Documenting testing on Confluence")
    confluence_link = confluenceHandler.generate_page(annotation_comparison,
    twe_diff, tso_diff, dev_twe_job, dev_tso_job, prod_twe_job, prod_tso_job)
    print("Generating Jira ticket")
    jira_link = jiraHandler.generate_ticket(confluence_link)
    confluenceHandler.add_jira_link(confluence_link, jira_link)

    # Step 5 - deploy clinvar file to 001
    print("Deploying clinvar files to 001 reference project")
    deployer.deploy_clinvar_to_production(recent_vcf_file, recent_tbi_file)

    # Step 6 - announce update to team
    announcer.announce_clinvar_update(recent_vcf_file, earliest_time, jira_link)

if __name__ == "__main__":
    run_prometheus()
