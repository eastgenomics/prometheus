from bin.compare_annotation import get_full_category_name as get_fc
import unittest

import os
os.chdir("..")


class testCase(unittest.TestCase):

    def test_regex(self):
        assert get_fc("Benign", ".") == "benign"
        assert get_fc("Benign/Likely_benign", ".") == "benign/likely benign"
        assert get_fc("not_provided", ".") == "not provided"
        assert get_fc("Pathogenic", ".") == "pathogenic"
        assert (get_fc("Uncertain_significance", ".")
                == "uncertain significance")
        assert (get_fc("Pathogenic/Likely_pathogenic", ".")
                == "pathogenic/likely pathogenic")
        assert get_fc("risk_factor", ".") == "risk factor"

        # complex cases
        with self.assertRaises(Exception):
            get_fc("Conflicting_interpretations_of_pathogenicity", ".")
        with self.assertRaises(Exception):
            Exception, get_fc("Conflicting_interpretations"
                              + "_of_pathogenicity&other", ".")


if __name__ == "__main__":
    unittest.main()
