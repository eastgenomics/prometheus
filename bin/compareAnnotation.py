import re
import types
import pandas
import json

regex_config_location = "resources/annotation_regex.json"

def compare_annotation(diff_twe, diff_tso):
    # TODO: write algorithm to document and describe all differences
    # get variant annotation changes for TWE
    added_twe, deleted_twe, changed_twe = parse_diff(diff_twe)
    # add "assay" column with "TWE" for added, deleted, and changed
    # TODO: implement here
    
    # get variant annotation changes for TSO500
    added_tso, deleted_tso, changed_tso = parse_diff(diff_tso)

    # combine both tables on all columns for added, deleted, and changed
    added = pandas.concat([added_twe, added_tso])
    deleted = pandas.concat([deleted_twe, deleted_tso])
    changed = pandas.concat([changed_twe, changed_tso])
    # filter added to show only "Added" "Count TWE" and "Count TSO500" columns
    # filter deleted to show only "Deleted" "Count TWE" and "Count TSO500" columns
    # filter changed to show only "Changed from" "Changed to" "Count TWE" and "Count TSO500" columns
    
    comparison_spreadsheet = "annotation_comparison.csv"
    return comparison_spreadsheet

def parse_diff(diff):
    """
    Returns list of deleted variants (list of strings), 
    added variants (list of strings), 
    changed variants (list of tuples in format: string, string) for old variant, new variant
    """
    consts = types.SimpleNamespace()
    consts.SCAN_MODE = 0
    consts.ADDED_MODE = 1
    consts.DELETED_MODE = 2
    consts.CHANGED_MODE_DEL = 3
    consts.CHANGED_MODE_ADD = 4

    parse_mode = consts.SCAN_MODE

    change_regex = r"^[0-9]+c[0-9]$"
    added_regex = r"^[0-9]+a[0-9]$"
    deleted_regex = r"^[0-9]+d[0-9]$"

    added_regex = r"^> (.*)$"
    deleted_regex = r"^< (.*)$"

    added_list = []
    deleted_list = []
    changed_list = []

    changed_del_temp = ""

    for line in diff:
        match parse_mode:
            case consts.SCAN_MODE:
                # search for new difference annotation
                if re.search(change_regex, line):
                    parse_mode = consts.CHANGED_MODE_DEL
                elif re.search(added_regex, line):
                    parse_mode = consts.ADDED_MODE
                elif re.search(deleted_regex, line):
                    parse_mode = consts.DELETED_MODE
            case consts.ADDED_MODE:
                # search for added line
                result = re.search(added_regex, line)
                if result:
                    added_list.append(result)
                    parse_mode = consts.SCAN_MODE
            case consts.DELETED_MODE:
                # search for deleted line
                result = re.search(deleted_regex, line)
                if result:
                    deleted_list.append(result)
                    parse_mode = consts.SCAN_MODE
            case consts.CHANGED_MODE_DEL:
                # search for changed line (old)
                result = re.search(deleted_regex, line)
                if result:
                    changed_del_temp = result
                    parse_mode = consts.CHANGED_MODE_ADD
            case consts.CHANGED_MODE_ADD:
                # search for changed line (new)
                result = re.search(added_regex, line)
                if result:
                    changed_list.append((changed_del_temp, result))
                    parse_mode = consts.SCAN_MODE

    # TODO: add code for processing this info

    return added_list, deleted_list, changed_list

def split_variant_info(raw_list) -> list(str):
    filtered_list = []
    for item in raw_list:
        # format: mutation, locus, category, info
        filtered_list.append(item.split(' '))

def make_tables(added_list, deleted_list, changed_list):
    added_table = pandas.DataFrame(data=added_list, columns=["mutation", "locus", "category", "info"])
    # output format: variant category, count TWE, count TSO500
    # in the case of conflicting evidence, category is based on "category" and "info" columns
    # list of full category names from category and input columns
    added_categories = get_categories(added_table)
    

def get_categories(dataframe_extract):
    # get full category name from category and info columns for all entries
    updated_categories = []
    for row in dataframe_extract:
        base_name = row.category
        info = row.info
        full_name = get_full_category_name(base_name, info)
        updated_categories.append(full_name)

def get_full_category_name(base_name, info):
    # get full category name from category and info columns for single entry
    with open(regex_config_location, "r") as file:
        regex_dict = json.load(file)

    difference_regex = regex_dict[difference_regex]
    evidence_regex = regex_dict[evidence_regex]

    # validate that category is contained in difference regex
    for key in difference_regex:
        if re.match(difference_regex[key], base_name):
            # value entered is valid
            if (key != "conflicting interpretations of pathogenicity" and
            key != "conflicting interpretations of pathogenicity and other"):
                # return simple category, as this does not require modification
                return key
            else:
                # check info
                if info == ".":
                    # throw exception, invalid input
                    print("invalid input")
                else:
                    # try to parse info
                    # split info by &
                    split_info = info.split("&")
                    # remove numbers in brackets
                    # TODO: extract numbers for final report table
                    # TODO: check if format of split string is valid (matches r"(*)\([0-9]\)")
                    new_info = []
                    for my_str in split_info:
                        match = re.match(r"(*)\([0-9]\)", my_str)
                        if match:
                            new_info.append(match)
                        else:
                            # throw exception
                            print("invalid input format in 'info' field")

                    # we now have a vec (new_info) containing all evidence categories for this variant
                    # the next step is to order this list of categories so the order is uniform for all variants

                    output_string = base_name + " "
                    for regex in evidence_regex:
                        for evidence in new_info:
                            if re.match(evidence_regex[regex], evidence):
                                # add category and &
                                output_string += regex + "&"

                    output_string = output_string[:-1]
                    return output_string