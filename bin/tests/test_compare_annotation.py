from .context import compare_annotation as ca
import unittest

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_regex(self):
        assert ca.get_full_category_name("Benign", ".") == "benign"
        assert (ca.get_full_category_name("Benign/Likely_benign", ".")
                == "benign/likely benign")
        assert ca.get_full_category_name("not_provided", ".") == "not provided"
        assert ca.get_full_category_name("Pathogenic", ".") == "pathogenic"
        assert (ca.get_full_category_name("Uncertain_significance", ".")
                == "uncertain significance")
        assert (ca.get_full_category_name("Pathogenic/Likely_pathogenic", ".")
                == "pathogenic/likely pathogenic")
        assert ca.get_full_category_name("risk_factor", ".") == "risk factor"

        # complex cases
        conflicting = "Conflicting_interpretations_of_pathogenicity"
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflicting, ".")
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflicting, ".")


if __name__ == "__main__":
    unittest.main()
