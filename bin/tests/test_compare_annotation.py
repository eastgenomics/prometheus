from bin.compare_annotation import get_full_category_name

import os
os.chdir("..")

def test_get_full_category_name():
    # all simple cases
    assert get_full_category_name("Benign", ".") == "benign"
    assert get_full_category_name("Benign/Likely_benign", ".") == "benign/likely benign"
    assert get_full_category_name("not_provided", ".") == "not provided"
    assert get_full_category_name("Pathogenic", ".") == "pathogenic"
    assert get_full_category_name("Uncertain_significance", ".") == "uncertain significance"
    assert get_full_category_name("Pathogenic/Likely_pathogenic", ".") == "pathogenic/likely pathogenic"
    assert get_full_category_name("risk_factor", ".") == "risk factor"

    # complex cases
    assert get_full_category_name("Conflicting_interpretations_of_pathogenicity", ".") != "conflicting interpretations of pathogenicity"
    assert get_full_category_name("Conflicting_interpretations_of_pathogenicity&other", ".") != "conflicting interpretations of pathogenicity and other"

if __name__ == "__main__":
    test_get_full_category_name()
    