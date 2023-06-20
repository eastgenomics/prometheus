"""
Handles announcing updates to team
"""

def announce_clinvar_update(clinvar_date, month):
    # TODO: learn how to use slack API
    update_message = """
    The new version of the ClinVar annotation resource file clinvar_{}.vcf.gz ({}) has been deployed into 001_reference
    """.format(clinvar_date, month)
    print(update_message)
    return