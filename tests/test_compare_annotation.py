from bin.annotation import compare_annotation as ca
import unittest
import pandas
from unittest.mock import Mock, patch, mock_open


class testCompareAnnotation(unittest.TestCase):
    REGEX_DICT = {
            "difference_regex": {
                "affects": "Affects",
                "benign": "Benign",
                "established risk allele": "Established_risk_allele",
                "likely benign": "Likely_benign",
                "likely pathogenic": "Likely_pathogenic",
                "likely risk allele": "Likely_risk_allele",
                "pathogenic": "Pathogenic",
                "uncertain risk allele": "Uncertain_risk_allele",
                "uncertain significance": "Uncertain_significance",
                "association": "association",
                "association not found": "association_not_found",
                "confers sensitivity": "confers_sensitivity",
                "conflicting data from submitters": "conflicting_data_from_submitters",
                "drug response": "drug_response",
                "not provided": "not_provided",
                "other": "other",
                "protective": "protective",
                "risk factor": "risk_factor",
                "conflicting interpretations of pathogenicity": "Conflicting_interpretations_of_pathogenicity",
                "conflicting interpretations of pathogenicity and other": "Conflicting_interpretations_of_pathogenicity&other",
                "conflicting interpretations of pathogenicity and other and risk factor": "Conflicting_interpretations_of_pathogenicity&other&risk_factor",
                "conflicting interpretations of pathogenicity and risk factor": "Conflicting_interpretations_of_pathogenicity&risk_factor"
            },
            "evidence_regex": {
                "benign": "Benign",
                "likely benign": "Likely_benign",
                "uncertain significance": "Uncertain_significance",
                "likely pathogenic": "Likely_pathogenic",
                "pathogenic": "Pathogenic",
                "pathogenic and low penetrance": "Pathogenic&_low_penetrance"
            }
        }

    def test_regex_benign(self):
        """test if benign category can be identified from regex
        """

        assert ca.get_full_category_name(
            "Benign", ".", self.REGEX_DICT
        ) == "benign"

    def test_regex_likely_benign(self):
        """test if likely benign category can be identified from regex
        """
        assert (
            ca.get_full_category_name(
                "Benign/Likely_benign", ".", self.REGEX_DICT
            ) == "benign/likely benign"
        )

    def test_regex_not_provided(self):
        """test if not provided category can be identified from regex
        """
        assert (
            ca.get_full_category_name(
                "not_provided", ".", self.REGEX_DICT
            ) == "not provided"
        )

    def test_regex_pathogenic(self):
        """test if pathogenic category can be identified from regex
        """
        assert (
            ca.get_full_category_name(
                "Pathogenic", ".", self.REGEX_DICT
            ) == "pathogenic"
        )

    def test_regex_uncertain(self):
        """test if uncertain category can be identified from regex
        """
        assert (
            ca.get_full_category_name(
                "Uncertain_significance", ".", self.REGEX_DICT
            ) == "uncertain significance"
        )

    def test_regex_likely_pathogenic(self):
        """test if likely pathogenic category can be identified from regex
        """
        assert (
            ca.get_full_category_name(
                "Pathogenic/Likely_pathogenic", ".", self.REGEX_DICT
                ) == "pathogenic/likely pathogenic"
        )

    def test_regex_risk_factor(self):
        """test if risk factor category can be identified from regex
        """
        assert (
            ca.get_full_category_name(
                "risk_factor", ".", self.REGEX_DICT
                ) == "risk factor"
        )

    def test_regex_conflicting(self):
        """test if conflicting category can be identified from regex
        """
        conflicting = "Conflicting_interpretations_of_pathogenicity"
        info = "Likely_pathogenic(1)&Uncertain_significance(1)"
        assert (
            ca.get_full_category_name(conflicting, info, self.REGEX_DICT)
            == "conflicting interpretations of pathogenicity uncertain significance&likely pathogenic"
        )

    def test_regex_conflicting_invalid(self):
        """test that get_full_categoty_name fails when conflicting category
        does not contain information in info column
        """
        conflicting = "Conflicting_interpretations_of_pathogenicity"
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflicting, ".", self.REGEX_DICT)

    def test_regex_conflicting_other(self):
        """test if conflicting other category can be identified from regex
        """
        info = "Likely_pathogenic(1)&Uncertain_significance(1)"
        conflict_other = "Conflicting_interpretations_of_pathogenicity&other"
        assert (
            ca.get_full_category_name(conflict_other, info, self.REGEX_DICT)
            == "conflicting interpretations of pathogenicity uncertain significance&likely pathogenic"
        )

    def test_regex_conflicting_other_invalid(self):
        """test that get_full_categoty_name fails when conflicting other
        category does not contain information in info column
        """
        conflict_other = ("Conflicting_interpretations_of_pathogenicity&other")
        with self.assertRaises(Exception):
            ca.get_full_category_name(conflict_other, ".", self.REGEX_DICT)

    def test_parse_line_count_no_commas(self):
        """test if line count can be found for 0 commas
        """
        no_commas = "223c223"
        assert ca.parse_line_count(no_commas) == 1

    def test_parse_line_count_one_comma(self):
        """test if line count can be found for 1 comma
        """
        one_comma = "21,22c21,22"
        assert ca.parse_line_count(one_comma) == 2

    def test_parse_line_count_five_commas(self):
        """test if line count can be found for 5 commas
        """
        five_commas = "2,3,4,5,6,7c2,3,4,5,6,7"
        assert ca.parse_line_count(five_commas) == 6

    def test_parse_line_count_invalid(self):
        """test if parse line count raises exception with invalid input
        """
        invalid = "4,5,6c4,5"
        with self.assertRaises(Exception):
            ca.parse_line_count(invalid)

    def test_parse_diff(self):
        """test if diff output can be parsed to dataframes of correct size
        """
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
        with patch("json.load", Mock(return_value=self.REGEX_DICT)):
            with patch("builtins.open", mock_open(read_data=parse_text)):
                (
                    added_df,
                    deleted_df,
                    changed_df,
                    detailed_df
                ) = ca.parse_diff("test_diff.txt", "")

        # check output type is correct
        assert (
            isinstance(added_df, pandas.DataFrame)
            and isinstance(deleted_df, pandas.DataFrame)
            and isinstance(changed_df, pandas.DataFrame)
            and isinstance(detailed_df, pandas.DataFrame)
        )

        # check contents are correct
        assert (
            len(added_df) == 1
            and len(deleted_df) == 4
            and len(changed_df) == 5
            and len(detailed_df) == 3
        )

    def test_split_variant_info(self):
        """test that variant info string can be split into columns
        by split_variant_info
        """
        input = [
            "< 1:10689814:G:C 2125983 Uncertain_significance .",
            "< 1:247587997:G:A 1985408 Benign ."
        ]
        output = ca.split_variant_info(input)
        assert (
            len(output) == 2
            and output[0][0] == "1:10689814:G:C"
            and output[0][1] == "2125983"
            and output[0][2] == "Uncertain_significance"
            and output[0][3] == "."
        )

    def test_get_evidence_counts_low(self):
        """test if get_evidence_counts can obtain counts from a string of
        low evidence counts
        """
        input = (
            "Benign(1)&Likely_benign(1)&Uncertain_significance(2)"
            + "&Likely_pathogenic(3)&Pathogenic(4)"
        )
        assert ca.get_evidence_counts(input) == [1, 1, 2, 3, 4, 0, 0]

    def test_get_evidence_counts_high(self):
        """test if get_evidence_counts can obtain counts from a string of
        high evidence counts
        """
        input = "Benign(111)&Likely_pathogenic(31)&Pathogenic(46)"
        assert ca.get_evidence_counts(input) == [111, 0, 0, 31, 46, 0, 0]

    @patch("builtins.open", mock_open(read_data="data"))
    def test_make_dataframes(self):
        """test if make_dataframes can generate dataframes from input lists
        """
        added_list = []
        deleted_list = []
        changed_list_from = [[
            "mutation", "1234",
            "Conflicting_interpretations_of_pathogenicity",
            "Benign(1)&Likely_pathogenic(3)&Pathogenic(4)"
        ]]
        changed_list_to = [[
            "mutation", "1234",
            "Conflicting_interpretations_of_pathogenicity",
            "Benign(1)&Likely_benign(1)&Pathogenic(4)"
        ]]
        bin_folder = ""
        with patch("json.load", Mock(return_value=self.REGEX_DICT)):
            (
                added_df,
                deleted_df,
                changed_df,
                detailed_df
            ) = ca.make_dataframes(
                added_list, deleted_list, changed_list_from, changed_list_to,
                bin_folder
            )

        # check output type is correct
        assert (
            isinstance(added_df, pandas.DataFrame)
            and isinstance(deleted_df, pandas.DataFrame)
            and isinstance(changed_df, pandas.DataFrame)
            and isinstance(detailed_df, pandas.DataFrame)
        )


if __name__ == "__main__":
    unittest.main()
