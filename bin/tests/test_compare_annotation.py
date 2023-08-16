from bin.compare_annotation import get_full_category_name as get_fc

import os
os.chdir("..")


def test_get_full_category_name():
    # all simple cases
    assert get_fc("Benign", ".") == "benign"
    assert get_fc("Benign/Likely_benign", ".") == "benign/likely benign"
    assert get_fc("not_provided", ".") == "not provided"
    assert get_fc("Pathogenic", ".") == "pathogenic"
    assert get_fc("Uncertain_significance", ".") == "uncertain significance"
    assert (get_fc("Pathogenic/Likely_pathogenic", ".")
            == "pathogenic/likely pathogenic")
    assert get_fc("risk_factor", ".") == "risk factor"

    # complex cases
    assert (get_fc("Conflicting_interpretations_of_pathogenicity", ".")
            != "conflicting interpretations of pathogenicity")
    assert (get_fc("Conflicting_interpretations_of_pathogenicity&other", ".")
            != "conflicting interpretations of pathogenicity and other")


if __name__ == "__main__":
    test_get_full_category_name()
