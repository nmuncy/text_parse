"""
Notes:

    1) Finds input files in cwd/txt_files
        cwd = current working directory

    2) Iterates through each txt file

    3) Searches for items in search_list
        Appends output csv for each match with
        preceding, word, subsequent

    4) Writes parellated lines to cwd/json_files
        cwd/json_files organized by txt_file name string

    5) Writes word match, total to cwd/csv_files
        same organization as json_files

    6) Likely breaks on Step2, since no consistent
        capitalization, string, punctuation to parse
        speaker: statement

Usage:
    Jupyter-esque via iPyKernel

TODO:
    Convert uber parse_text to modular functions
        for each step
    Update for CLI (CLI > Jupyter)
    Resolve hacky-hacks
"""

# %%
import os
import re
import csv
import string
import json
import numpy as np
import pandas as pd
from datetime import datetime


# %%
search_list = ["victims", "pets", "irrevocable"]


# %%
def parse_text(in_file, search_list, json_dir, csv_dir):

    """
    Step 0: Start
    Read in file, start output matrix
    """

    # # For testing
    # parent_dir = os.path.abspath(os.path.dirname(__file__))
    # data_dir = os.path.join(parent_dir, "txt_files")
    # data_list = os.listdir(data_dir)
    # txt_file = data_list[0]
    # in_file = os.path.join(data_dir, txt_file)
    # json_dir = os.path.join(parent_dir, "json_files", txt_file.split(".")[0])
    # csv_dir = os.path.join(parent_dir, "csv_files", txt_file.split(".")[0])

    # read in txt file as dictionary
    text_lines = {}
    with open(in_file, "r", encoding="utf-8") as text_file:
        for c, line in enumerate(text_file):
            text_lines[c] = line

    # start counter for whole file
    running_total = 0
    line_total_dict = {}

    # start search matrix, add NAN in case no matches
    df_word_match = np.empty((0, 3), str)
    df_word_match = np.append(df_word_match, [["NAN", "NAN", "NAN"]], axis=0)

    """
    Step 1: Clean line
    Iterate through lines of file, clean up nonsense
    """

    # iterate through lines of file
    for key in text_lines:
        # key = 759

        # clean oddities
        line_clean = text_lines[key].replace("voice-over", "")
        line_clean = line_clean.replace(" : ", ": ")
        line_clean = line_clean.replace(" . ", ". ")
        line_clean = line_clean.replace(" , ", ", ")
        line_clean = line_clean.replace("@ @", ".")

        # make symbols consistent
        replace_dict = {
            "?": ".",
            "!": ".",
            "&": ".",
            "%": ".",
            "$": " ",
            "#": " ",
            "@": " ",
            '"': " ",
            "-": " ",
        }
        line_clean = line_clean.translate(str.maketrans(replace_dict))

        # clean titles - to be included in name
        line_clean = line_clean.replace("Dr.", ".Dr")
        line_clean = line_clean.replace("Mr.", ".Mr")
        line_clean = line_clean.replace("Mrs.", ".Mrs")
        line_clean = line_clean.replace("Ms.", ".Ms")
        line_clean = line_clean.replace("Prof.", ".Prof")

        """
        Step 2: Split by speaker
        Determine speaker list via regex, search line
            for speaker, split line at location of speaker
            into speaker: statement (called sentence)

        SPECIAL NOTE: used some hacky hacks to make
            this part work (boundary issues). Code issues
            likely to be found here.
        """

        # find all positions of capital strings
        #   regex match ".Mrs FOO BAR :"
        speaker_list = re.findall(
            r"(\b(?:[.]?\s*[A-Z]+[A-Z]+)\b(?:\s+(?:[A-Z]+[A-Z]+\s*[:]?)\b)*)",
            line_clean,
        )
        speaker_list = [x.strip(".") for x in speaker_list]
        speaker_list = [x.strip(" ") for x in speaker_list]

        # iterate through all speakers, without re-searching
        #   same start of line
        h_start = 0
        for c, spkr in enumerate(speaker_list):

            # find speaker location and following space
            h_loc = line_clean.find(spkr, h_start)
            h_space = line_clean.find(" ", h_loc)

            # hacky hack for boundary issues
            if h_loc > 0:

                # add period to location preceding h_loc
                h_per = h_loc - 1
                if h_loc < len(line_clean) - 20:
                    if "." not in line_clean[h_per]:
                        line_clean = line_clean[:h_per] + "." + line_clean[h_per:]
                        h_loc += 1
                        h_space += 1

                # patchy patch for boundary issues (last wordish capitalized)
                if h_loc < len(line_clean) - 20:

                    # test if character 2 places after space
                    #   is upper (FIRST LAST vs LAST Word), walk
                    #   until success.
                    h_test = line_clean[h_space + 2]
                    while h_test.isupper():
                        h_loc = h_space + 1
                        h_space = line_clean.find(" ", h_loc)
                        h_test = line_clean[h_space + 2]

                    # check for, add colon if needed
                    h_end = h_space + 1
                    if ":" not in line_clean[h_loc:h_end]:
                        h_col = line_clean.find(":", h_end)
                        if c + 1 < len(speaker_list):
                            h_nxt_spkr = line_clean.find(speaker_list[c + 1], h_start)
                            if h_nxt_spkr < h_col:
                                line_clean = (
                                    line_clean[:h_space] + ":" + line_clean[h_space:]
                                )
                            elif "," not in line_clean[h_end:h_col]:
                                line_clean = (
                                    line_clean[:h_space] + ":" + line_clean[h_space:]
                                )

                    h_start = h_end

        # determine location of colons, split line by colon
        loc_colons = [i.start() for i in re.finditer(":", line_clean)]
        line_parts = [
            line_clean[i:j] for i, j in zip(loc_colons, loc_colons[1:] + [None])
        ]

        """
        Step 3: Line dictionary
        Make, fill line dictionary with speaker: statement.
        Count words of line. Increase running counters
        Find search word, and preceding/subsequent words in line.
        """

        # initialize empty dict, add first key. line_dict will have format
        #   line_dict[key]: [values] = line_dict[speaker]: [word_count, sentence]
        line_dict = {}
        speaker_name = f"0. {line_clean.split(':')[0].split('.')[-1]}"
        line_dict[speaker_name] = []

        # start line counter
        line_total = 0

        # loop through line sections
        for ind_count, sentence in enumerate(line_parts):

            # determine sentence (after first ":", before final ".")
            parts_sentence = line_parts[ind_count].split(":")[1].rsplit(".", 1)[0]

            # remove punctuation for word count
            parts_no_punc = re.sub(r"[^\w\s]", "", parts_sentence)

            # count words 2 ways to deal with oddities, take larger
            h_num_words_a = len(re.findall(r"\w+", parts_no_punc))
            h_num_words_b = sum(
                [i.strip(string.punctuation).isalpha() for i in parts_sentence.split()]
            )
            num_words = max(h_num_words_a, h_num_words_b)

            # increase running counters
            running_total += num_words
            line_total += num_words

            # write number of words, sentence to dict
            #      at key location previously set

            sentence_list = parts_no_punc.split(" ")
            sentence_list = list(filter(None, sentence_list))
            for search_word in search_list:
                ind_word = [x for x, y in enumerate(sentence_list) if y == search_word]
                if ind_word:
                    for ind_pos in ind_word:
                        word_prec = (
                            sentence_list[ind_pos - 1]
                            if ind_pos - 1 >= 0
                            else "NAN Out of Bounds"
                        )
                        word_curr = sentence_list[ind_pos]
                        word_post = (
                            sentence_list[ind_pos + 1]
                            if ind_pos + 1 <= len(sentence_list) - 1
                            else "NAN Out of Bounds"
                        )

                        df_word_match = np.append(
                            df_word_match, [[word_prec, word_curr, word_post]], axis=0
                        )

            # append sent list with num_words
            #   add sent list to line_dict at
            #   key location previously set
            sentence_list.insert(0, num_words)
            line_dict[speaker_name] = sentence_list

            # get, add new dict key if we are in bounds
            if ind_count < (len(line_parts) - 1):
                speaker_name = (
                    f"{ind_count + 1}. {line_parts[ind_count].split('.')[-1]}"
                )
                line_dict[speaker_name] = []

        """
        Step 4: Write out
        """

        # write line total to dict
        line_total_dict[f"line-{key}"] = line_total

        # write out parcellated line to json_dir/Line*.json
        out_json = os.path.join(json_dir, f"Line{key}.json")
        with open(out_json, "w") as jf:
            json.dump(line_dict, jf)

    # get file total
    line_total_dict["Final"] = running_total

    # write out parcellated line to json_dir/Line*.csv
    out_words = os.path.join(csv_dir, "Total_Words.csv")
    with open(out_words, "w") as csv_file:
        writer = csv.writer(csv_file)
        for key, value in line_total_dict.items():
            writer.writerow([key, value])

    # Write out word search
    df_out = pd.DataFrame(
        data=df_word_match, columns=["Preceding", "Current", "Subsequent"]
    )
    time_now = datetime.now()
    time_stamp = f"{time_now.year}-{time_now.month}-{time_now.day}_{time_now.hour}.{time_now.minute}.{time_now.second}"
    out_search = os.path.join(csv_dir, f"Match_Words_{time_stamp}.csv")
    df_out.to_csv(out_search, index=False)


# %%
# set orientings vars, make output location
parent_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(parent_dir, "txt_files")
data_list = os.listdir(data_dir)

# %%
for txt_file in data_list:
    in_file = os.path.join(data_dir, txt_file)

    json_dir = os.path.join(parent_dir, "json_files", txt_file.split(".")[0])
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    csv_dir = os.path.join(parent_dir, "csv_files", txt_file.split(".")[0])
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    parse_text(in_file, search_list, json_dir, csv_dir)
