"""
Compares the output of VEP for development and production ClinVar vcfs
"""

import re
import types
import pandas
import json

output_location = "temp"


def compare_annotation(diff_twe, diff_tso, bin_folder):
    """generates csv reports from diff outputs for TWE and TSO500

    Args:
        diff_twe (str): path to diff output file for TWE
        diff_tso (str): path to diff output file for TSO500

    Returns:
        added_output: str
            path to .csv summarising added variants
        deleted_output: str
            path to .csv summarising deleted variants
        changed_output: str
            path to .csv summarising changed variants
    """
    # get variant annotation changes for TWE
    added_twe, deleted_twe, changed_twe, detailed_twe = parse_diff(
        diff_twe, bin_folder)
    # add "assay" column with "TWE" for added, deleted, and changed
    added_twe["assay"] = "TWE"
    deleted_twe["assay"] = "TWE"
    changed_twe["assay"] = "TWE"
    detailed_twe["assay"] = "TWE"

    # get variant annotation changes for TSO500
    added_tso, deleted_tso, changed_tso, detailed_tso = parse_diff(
        diff_tso, bin_folder)
    # add "assay" column with "TSO500" for added, deleted, and changed
    added_tso["assay"] = "TSO500"
    deleted_tso["assay"] = "TSO500"
    changed_tso["assay"] = "TSO500"
    detailed_tso["assay"] = "TSO500"

    # combine both tables on all columns for added, deleted, and changed
    added = pandas.concat([added_twe, added_tso])
    deleted = pandas.concat([deleted_twe, deleted_tso])
    changed = pandas.concat([changed_twe, changed_tso])
    detailed = pandas.concat([detailed_twe, detailed_tso])
    # filter added to show only "Added" "Count TWE" and "Count TSO500" columns
    added = added[['added', 'assay']].value_counts()
    added = added.reset_index(name='assay counts')
    added = pandas.pivot_table(added, index='added',
                               columns='assay', values='assay counts')
    added = added.fillna(0).astype(int)
    # filter deleted to show only "Deleted" "Count TWE" "Count TSO500" columns
    deleted = deleted[['deleted', 'assay']].value_counts()
    deleted = deleted.reset_index(name='assay counts')
    deleted = pandas.pivot_table(deleted, index='deleted',
                                 columns='assay', values='assay counts')
    deleted = deleted.fillna(0).astype(int)
    # filter changed to show only "Changed from" "Changed to"
    # "Count TWE" "Count TSO500" columns
    changed = changed[['changed from', 'changed to', 'assay']].value_counts()
    changed = changed.reset_index(name='assay counts')
    changed = pandas.pivot_table(changed, index=['changed from', 'changed to'],
                                 columns='assay', values='assay counts')
    changed = changed.fillna(0).astype(int)

    added_output = f"{output_location}/added_variants.csv"
    added.to_csv(added_output, index=True)
    deleted_output = f"{output_location}/deleted_variants.csv"
    deleted.to_csv(deleted_output, index=True)
    changed_output = f"{output_location}/changed_variants.csv"
    changed.to_csv(changed_output, index=True)
    detailed_out = f"{output_location}/detailed_changed_variants.csv"
    detailed.to_csv(detailed_out, index=False)

    return added_output, deleted_output, changed_output, detailed_out


def parse_diff(diff_filename, bin_folder):
    """parses file of diff output to dataframes

    Args:
        diff_filename (str): path to diff file

    Raises:
        FileNotFoundError: diff file not found

    Returns:
        added_df: pandas.DataFrame
            path to .csv summarising added variants
        deleted_df: pandas.DataFrame
            path to .csv summarising deleted variants
        changed_df: pandas.DataFrame
            path to .csv summarising changed variants
    """
    # read in file from filename passed in
    try:
        diff = open(diff_filename, "r")
    except (FileNotFoundError, IOError):
        raise FileNotFoundError(f"Error: the diff file {diff_filename}"
                                + " could not be found!")

    consts = types.SimpleNamespace()
    consts.SCAN_MODE = 0
    consts.ADDED_MODE = 1
    consts.DELETED_MODE = 2
    consts.CHANGED_MODE_DEL = 3
    consts.CHANGED_MODE_ADD = 4

    parse_mode = consts.SCAN_MODE

    change_regex = r"[0-9]+c[0-9]+"
    add_regex = r"[0-9]+a[0-9]+"
    delete_regex = r"[0-9]+d[0-9]+"

    added_regex = r"^> (.*)$"
    deleted_regex = r"^< (.*)$"

    added_list = []
    deleted_list = []
    changed_list_from = []
    changed_list_to = []

    # tracks multiple lines added, removed, or changed in diff output
    added_line_counter = 0
    deleted_line_counter = 0

    for line in diff:
        match parse_mode:
            case consts.SCAN_MODE:
                # search for new difference annotation
                if re.search(change_regex, line):
                    parse_mode = consts.CHANGED_MODE_DEL
                    added_line_counter = parse_line_count(line)
                    deleted_line_counter = parse_line_count(line)
                elif re.search(add_regex, line):
                    parse_mode = consts.ADDED_MODE
                    added_line_counter = parse_line_count(line)
                elif re.search(delete_regex, line):
                    parse_mode = consts.DELETED_MODE
                    deleted_line_counter = parse_line_count(line)
            case consts.ADDED_MODE:
                # search for added line
                result = re.search(added_regex, line)
                if result:
                    added_list.append(result.group(0))
                    added_line_counter -= 1
                if added_line_counter <= 0:
                    parse_mode = consts.SCAN_MODE
            case consts.DELETED_MODE:
                # search for deleted line
                result = re.search(deleted_regex, line)
                if result:
                    deleted_list.append(result.group(0))
                    deleted_line_counter -= 1
                if deleted_line_counter <= 0:
                    parse_mode = consts.SCAN_MODE
            case consts.CHANGED_MODE_DEL:
                # search for changed line (old)
                result = re.search(deleted_regex, line)
                if result:
                    changed_list_from.append(result.group(0))
                    deleted_line_counter -= 1
                if deleted_line_counter <= 0:
                    parse_mode = consts.CHANGED_MODE_ADD
            case consts.CHANGED_MODE_ADD:
                # search for changed line (new)
                result = re.search(added_regex, line)
                if result:
                    changed_list_to.append(result.group(0))
                    added_line_counter -= 1
                if added_line_counter <= 0:
                    parse_mode = consts.SCAN_MODE

    added_split = split_variant_info(added_list)
    deleted_split = split_variant_info(deleted_list)
    changed_from_split = split_variant_info(changed_list_from)
    changed_to_split = split_variant_info(changed_list_to)

    # if name == "" or " " in changed_from, add changed_to entry to added
    # and delete entry in changed_from and changed_to
    # if name == "" or " " in changed_to, add changed_from entry to deleted
    # and delete entry in changed_from and changed_to
    delete_indices = []
    for i in range(0, len(changed_from_split)):
        from_name = changed_from_split[i][2]
        to_name = changed_to_split[i][2]
        if from_name == "" or from_name == " ":
            delete_indices.append(i)
            added_split.append(changed_to_split[i])
        elif to_name == "" or to_name == " ":
            delete_indices.append(i)
            deleted_split.append(changed_from_split[i])

    for index in sorted(delete_indices, reverse=True):
        del changed_from_split[index]
        del changed_to_split[index]

    added_df, deleted_df, changed_df, detailed_df = make_dataframes(
        added_split, deleted_split, changed_from_split, changed_to_split,
        bin_folder
    )

    return added_df, deleted_df, changed_df, detailed_df


def parse_line_count(line):
    """checks if the number of commas is valid when parsing a difference

    Args:
        line (str): line containing difference description

    Raises:
        Exception: odd number of commas found in line

    Returns:
        int: number of differences found based on number of commas
    """
    num_commas = line.count(",")
    if num_commas % 2 == 0:
        return num_commas/2 + 1
    else:
        raise Exception("Invalid (odd) number of commas found"
                        " when parsing diff file")


def split_variant_info(raw_list):
    """splits diff string into columns

    Args:
        raw_list (list): list of diff strings

    Returns:
        list: list of values in format mutation, clinvar ID, category, info
    """
    filtered_list = []
    for item in raw_list:
        # format: mutation, clinvar ID, category, info
        # ignore first element as this is ">" or "<"
        filtered_list.append(item.split(' ')[1:])

    return filtered_list


def make_dataframes(added_list, deleted_list, changed_list_from,
                    changed_list_to, bin_folder):
    """generates dataframes from lists of variants

    Args:
        added_list (list): list of added variants
        deleted_list (list): list of deleted variants
        changed_list_from (list): list of old changed variants
        changed_list_to (list): list of new changed variants

    Returns:
        added_df: pandas.DataFrame
            columns: added
        deleted_df: pandas.DataFrame
            columns: deleted
        changed_df: pandas.DataFrame
            columns: changed_from, changed_to
        detailed_df: pandas.DataFrame
            columns: changed from, changed to, clinvar ID, benign prod,
                     benign dev, likely benign prod, likely benign dev,
                     uncertain prod, uncertain dev, likely pathogenic prod,
                     likely pathogenic dev, pathogenic prod, pathogenic dev
    """
    added_df = pandas.DataFrame(data=added_list,
                                columns=["mutation", "clinvar ID",
                                         "category", "info"])
    added_df["added"] = get_categories(
        added_df, bin_folder
    )
    added_df = added_df[["added"]]

    deleted_df = pandas.DataFrame(
        data=deleted_list, columns=[
            "mutation", "clinvar ID", "category", "info"
        ]
    )
    deleted_df["deleted"] = get_categories(
        deleted_df, bin_folder
    )
    deleted_df = deleted_df[["deleted"]]

    changed_from_df = pandas.DataFrame(
        data=changed_list_from, columns=[
            "mutation", "clinvar ID", "category", "info"
        ]
    )
    changed_from_df["changed from"] = get_categories(
        changed_from_df, bin_folder
    )
    changed_to_df = pandas.DataFrame(
        data=changed_list_to, columns=[
            "mutation", "clinvar ID", "category", "info"
        ]
    )
    changed_from_df["changed to"] = get_categories(
        changed_to_df, bin_folder)
    changed_df = changed_from_df[["changed from", "changed to"]]

    # generate variant evidence report
    # get all changed variants
    det_df = changed_from_df[[
        "changed from", "changed to", "clinvar ID"
    ]]
    # add info columns
    det_df["from info"] = changed_from_df["info"]
    det_df["to info"] = changed_to_df["info"]
    # filter to only changes with from and to having evidence
    det_df.drop(
        det_df[
            (det_df["from info"] == ".") | (det_df["to info"] == ".")
        ].index, inplace=True
    )
    # get list of counts per evidence type (5) for from and to
    # format: benign, likely benign, uncertain,
    #         likely pathogenic, pathogenic
    if len(det_df) == 0:
        return added_df, deleted_df, changed_df, det_df
    evidence_list = []
    for index, row in det_df.iterrows():
        from_evidence = get_evidence_counts(row["from info"])
        to_evidence = get_evidence_counts(row["to info"])
        # length 7 + length 7 = vector of length 14
        all_evidence = from_evidence + to_evidence
        evidence_list.append(all_evidence)

    # TODO: handle case for only evidence count changing (e.g., (1) to (2))
    ev_df = pandas.DataFrame(
        data=evidence_list,
        columns=[
            "benign_prod", "likely_benign_prod", "uncertain_prod",
            "likely_pathogenic_prod", "pathogenic_prod",
            "path_low_penetrance_prod", "unknown_prod",
            "benign_dev", "likely_benign_dev", "uncertain_dev",
            "likely_pathogenic_dev", "pathogenic_dev",
            "path_low_penetrance_dev", "unknown_dev"
        ]
    )

    det_df[[
        "benign_prod", "benign_dev",
        "likely_benign_prod", "likely_benign_dev",
        "uncertain_prod", "uncertain_dev",
        "likely_pathogenic_prod", "likely_pathogenic_dev",
        "pathogenic_prod", "pathogenic_dev",
        "path_low_penetrance_prod", "path_low_penetrance_dev",
        "unknown_prod", "unknown_dev"
    ]] = ev_df[[
        "benign_prod", "benign_dev",
        "likely_benign_prod", "likely_benign_dev",
        "uncertain_prod", "uncertain_dev",
        "likely_pathogenic_prod", "likely_pathogenic_dev",
        "pathogenic_prod", "pathogenic_dev",
        "path_low_penetrance_prod", "path_low_penetrance_dev",
        "unknown_prod", "unknown_dev"
    ]]
    det_df.drop(columns=["from info", "to info"], inplace=True)

    return added_df, deleted_df, changed_df, det_df


def get_evidence_counts(info):
    """gets the evidence count per category for a given variant

    Args:
        info (str): string of info column of a given variant

    Raises:
        RuntimeError: info has invalid format
        RuntimeError: info has invalid categories

    Returns:
        list: list of ints in format benign l_benign uncertain l_path path
    """
    return_list = [0, 0, 0, 0, 0, 0, 0]
    # handles case in which "&" is in the middle of string
    # e.g., Pathogenic&_low_penetrance(1)
    regex = r"[a-zA-Z_]+&*[a-zA-Z_]*\([0-9]+\)"
    match_regex = r"(^[A-Z].+)\(([0-9]+)\)"
    split = re.findall(regex, info)
    if len(split) < 1:
        raise RuntimeError(
            f"Info field \"{info}\" does not contain any valid entries"
        )

    cat_benign = "Benign"
    cat_lbenign = "Likely_benign"
    cat_uncertain = "Uncertain_significance"
    cat_lpathogenic = "Likely_pathogenic"
    cat_pathogenic = "Pathogenic"
    cat_lpenetrance = "Pathogenic&_low_penetrance"
    # format is now Name(n)
    for entry in split:
        match = re.search(match_regex, entry)
        if not match:
            raise RuntimeError(
                f"Info field \"{info}\" entry \"{entry}\" has invalid format"
            )
        category = match.group(1)
        try:
            count = int(match.group(2))
        except Exception:
            raise RuntimeError(
                f"Info field \"{info}\"has invalid categories"
                + f". The category {category} has an invalid"
                + " evidence count"
            )
        if category == cat_benign:
            return_list[0] = count
        elif category == cat_lbenign:
            return_list[1] = count
        elif category == cat_uncertain:
            return_list[2] = count
        elif category == cat_lpathogenic:
            return_list[3] = count
        elif category == cat_pathogenic:
            return_list[4] = count
        elif category == cat_lpenetrance:
            return_list[5] = count
        else:
            # record in "unknown" category instead of failing
            return_list[6] = count
    return return_list


def get_categories(dataframe_extract, bin_folder):
    """get full category name from category and info columns for all entries

    Args:
        dataframe_extract (pandas.DataFrame): contains category and info cols

    Returns:
        list: list of updated category names
    """
    updated_categories = []
    location = f"{bin_folder}/resources/annotation_regex.json"
    with open(location, "r") as file:
        regex_dict = json.load(file)
    for index, row in dataframe_extract.iterrows():
        base_name = row["category"]
        info = row["info"]
        full_name = get_full_category_name(base_name, info, regex_dict)
        updated_categories.append(full_name)

    return updated_categories


def get_full_category_name(base_name, info, regex_dict):
    """get full category name from category and info columns for single entry

    Args:
        base_name (str): from category column
        info (str): from info column

    Raises:
        Exception: Invalid input format in 'info' field

    Returns:
        str: full category name
    """
    difference_regex = regex_dict["difference_regex"]
    evidence_regex = regex_dict["evidence_regex"]

    conflict = "conflicting interpretations of pathogenicity"
    conflict_other = "conflicting interpretations of pathogenicity and other"
    conflict_risk = (
        "conflicting interpretations of pathogenicity and risk factor"
    )
    conflict_other_risk = (
        "conflicting interpretations of pathogenicity and other"
        + " and risk factor"
    )

    unknown_key = "unknown"

    name_split = base_name.split("/")
    # loop through name split to parse all name components
    # then add together to single name
    full_names = []
    for name in name_split:
        # validate that category is contained in difference regex
        name_match = False

        for key in difference_regex:
            if re.match(difference_regex[key], name):
                # value entered is valid
                name_match = True
                if (key != conflict
                        and key != conflict_other
                        and key != conflict_risk
                        and key != conflict_other_risk):
                    # add simple category to list of names
                    full_names.append(key)
                else:
                    # check info
                    if info == ".":
                        raise Exception("Invalid input format in 'info' field")
                    else:
                        # try to parse info
                        split_info = info.split("&")
                        # remove numbers in brackets
                        new_info = []
                        for my_str in split_info:
                            match = (re.match(r"(.+)\([0-9]+\)", my_str)
                                     .groups()[0])
                            if match:
                                new_info.append(match)
                            else:
                                raise Exception(
                                    "Invalid input format in 'info' field"
                                )

                        # we now have a vec (new_info) containing all evidence
                        # categories for this variant
                        # order this list of categories so the order is uniform
                        # for all variants
                        match_found = False
                        output_string = name + " "
                        for regex_category in evidence_regex:
                            for evidence in new_info:
                                if re.match(evidence_regex[regex_category],
                                            evidence):
                                    # add category and &
                                    output_string += regex_category + "&"
                                    match_found = True
                                    continue
                        if not match_found:
                            raise Exception("Invalid input in 'info' field")
                        # remove final &
                        output_string = output_string[:-1]
                        return output_string
        if not name_match:
            # if name does not match records, record as unknown
            # instead of failing
            full_names.append(unknown_key)
    # if name is simple, return
    # else, build composite name
    if len(full_names) < 2:
        return full_names[0]
    else:
        full_name = full_names[0]
        for i in range(1, len(full_names)):
            full_name += f"/{full_names[i]}"
        return full_name
