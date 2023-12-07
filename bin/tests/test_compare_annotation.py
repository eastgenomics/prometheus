from .context import compare_annotation as ca
import unittest

import pandas
import json
import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_regex(self):
        with open(ca.regex_config_location, "r") as file:
            regex_dict = json.load(file)

        assert ca.get_full_category_name("Benign", ".", regex_dict) == "benign"
        assert (ca.get_full_category_name("Benign/Likely_benign", ".",
                                          regex_dict)
                == "benign/likely benign")
        assert (ca.get_full_category_name("not_provided", ".", regex_dict)
               == "not provided")
        assert (ca.get_full_category_name("Pathogenic", ".", regex_dict)
               == "pathogenic")
        assert (ca.get_full_category_name("Uncertain_significance", ".",
                                          regex_dict)
                == "uncertain significance")
        assert (ca.get_full_category_name("Pathogenic/Likely_pathogenic", ".",
                                          regex_dict)
                == "pathogenic/likely pathogenic")
        assert (ca.get_full_category_name("risk_factor", ".", regex_dict)
               == "risk factor")

        # complex cases
        conflicting = "Conflicting_interpretations_of_pathogenicity"
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflicting, ".", regex_dict)
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflicting, ".", regex_dict)

    def test_parse_line_count(self):
        no_commas = "223c223"
        one_comma = "21,22c21,22"
        five_commas = "2,3,4,5,6,7c2,3,4,5,6,7"
        invalid = "4,5,6c4,5"
        assert ca.parse_line_count(no_commas) == 1
        assert ca.parse_line_count(one_comma) == 2
        assert ca.parse_line_count(five_commas) == 6

        with self.assertRaises(Exception):
            ca.parse_line_count(invalid)

    def test_parse_diff(self):
        parse_text = """18d17
< 1:10689814:G:C 2125983 Uncertain_significance .
23c22
< 1:11854476:T:G 3521 Conflicting_interpretations_of_pathogenicity&other Likely_pathogenic(1)&Uncertain_significance(1)&Benign(5)&Likely_benign(1)
---
> 1:11854476:T:G 3521 Conflicting_interpretations_of_pathogenicity&other Likely_pathogenic(1)&Uncertain_significance(2)&Benign(5)
158c157
< 1:100346327:G:T 382454 Conflicting_interpretations_of_pathogenicity Uncertain_significance(2)&Benign(1)&Likely_benign(4)
---
> 1:100346327:G:T 382454 Conflicting_interpretations_of_pathogenicity Uncertain_significance(2)&Benign(1)&Likely_benign(3)
190d188
< 1:151006539:C:A 2112788 Benign .
249d246
< 1:186946912:G:A 2113058 Benign .
293d289
< 1:204379617:T:C 2113113 Benign .
309,310c305,306
< 1:215914826:T:C 48378 Benign/Likely_benign .
< 1:215916563:G:A 48377 Benign/Likely_benign .
---
> 1:215914826:T:C 48378 Benign .
> 1:215916563:G:A 48377 Benign .
370a365
> 1:247587997:G:A 1985408 Uncertain_significance .
23c22
< 1:11854476:T:G 3521 Conflicting_interpretations_of_pathogenicity Benign(500)&Likely_benign(1)
---
> 1:11854476:T:G 3521 Conflicting_interpretations_of_pathogenicity Likely_pathogenic(1)&Uncertain_significance(2)&Benign(5)
        """

        with open("test_diff.txt", "w") as f:
            f.write(parse_text)
            f.write("\n")

        (added_df,
         deleted_df,
         changed_df,
         detailed_df) = ca.parse_diff("test_diff.txt")

        # check output type is correct
        assert ((type(added_df) is pandas.DataFrame)
                and (type(deleted_df) is pandas.DataFrame)
                and (type(changed_df) is pandas.DataFrame)
                and (type(changed_df) is pandas.DataFrame))

        # check contents are correct
        assert len(added_df) == 1
        assert len(deleted_df) == 4
        assert len(changed_df) == 5

        os.remove("test_diff.txt")

    def test_get_full_category_name(self):
        with open(ca.regex_config_location, "r") as file:
            regex_dict = json.load(file)
        name = "Benign"
        info = "."
        assert ca.get_full_category_name(name, info, regex_dict) == "benign"

        name = "2134793ryh02735607"
        with self.assertRaises(Exception):
            ca.get_full_category_name(name, info, regex_dict)

        conflict = "conflicting interpretations of pathogenicity"
        conflict_other = ("conflicting interpretations of "
                          + "pathogenicity and other")
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflict, info, regex_dict)
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflict_other, info, regex_dict)

    def test_split_variant_info(self):
        input = ["< 1:10689814:G:C 2125983 Uncertain_significance .",
                 "< 1:247587997:G:A 1985408 Benign ."]
        output = ca.split_variant_info(input)
        assert len(output) == 2
        assert output[0][0] == "1:10689814:G:C"
        assert output[0][1] == "2125983"
        assert output[0][2] == "Uncertain_significance"
        assert output[0][3] == "."

    def test_get_evidence_counts(self):
        input = ("Benign(1)&Likely_benign(1)&Uncertain_significance(2)"
                 + "&Likely_pathogenic(3)&Pathogenic(4)")
        assert ca.get_evidence_counts(input) == [1, 1, 2, 3, 4, 0]

        input = "Benign(1)&Likely_pathogenic(31)&Pathogenic(46)"
        assert ca.get_evidence_counts(input) == [1, 0, 0, 31, 46, 0]


if __name__ == "__main__":
    unittest.main()
