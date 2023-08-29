from .context import compare_annotation as ca
import unittest

import pandas
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
        """

        with open("test_diff.txt", "w") as f:
            f.write(parse_text)
            f.write("\n")

        (added_df,
         deleted_df,
         changed_df) = ca.parse_diff("test_diff.txt")

        # check output type is correct
        assert ((type(added_df) == pandas.DataFrame)
                and (type(deleted_df) == pandas.DataFrame)
                and (type(changed_df) == pandas.DataFrame))

        # check contents are correct
        assert len(added_df) == 1
        assert len(deleted_df) == 4
        assert len(changed_df) == 4

        os.remove("test_diff.txt")

    def test_get_full_category_name(self):
        name = "Benign"
        info = "."
        assert ca.get_full_category_name(name, info) == "benign"

        name = "2134793ryh02735607"
        with self.assertRaises(Exception):
            ca.get_full_category_name(name, info)

        conflict = "conflicting interpretations of pathogenicity"
        conflict_other = ("conflicting interpretations of "
                          + "pathogenicity and other")
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflict, info)
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflict_other, info)

    def test_split_variant_info(self):
        input = ["< 1:10689814:G:C 2125983 Uncertain_significance .",
                 "< 1:247587997:G:A 1985408 Benign ."]
        output = ca.split_variant_info(input)
        assert len(output) == 2
        assert output[0][0] == "1:10689814:G:C"
        assert output[0][1] == "2125983"
        assert output[0][2] == "Uncertain_significance"
        assert output[0][3] == "."


if __name__ == "__main__":
    unittest.main()
