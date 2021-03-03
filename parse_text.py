# %%
import os
import re
import csv
import string
import fnmatch

"""
Notes:

This script will read in a file (in_file), and for each line of the file will
    parcellate by speaker then determine the number of words for each speaker
    sentence.

Parcellation is accomplished given that each sentence has the format
    " ... foo bar. SPEAKER: lorem ipsum blah".
    Parcellation steps:
        1) Determine ":" locations
        2) Text Todd about (1)
        3) Derive speaker from between "." and ":"
        4) Derive sentence from preceding final "."
        NOTE - sentence always lags by one speaker.

The parcellated line will be written to out_dir/Line?.csv for review.

A running total will keep track of words in each line and in total. These will
    be written to out_dir/Total_words.csv

TODO:
    1) Hardcode -> regex
    2) Resolve missing ":" issue
    2) Update for CLI?
    3) Update to process all files in directory.
"""


# %%
# set orientings vars, make output location
parent_dir = os.getcwd()
data_dir = os.path.join(parent_dir, "txt_files")
data_list = os.listdir(data_dir)

problem_list = ["SPCA", "HIV", "AIDS"]


# for in_file in data_list:
txt_file = data_list[0]
in_file = os.path.join(data_dir, txt_file)

out_dir = os.path.join(parent_dir, "csv_files", txt_file.split(".")[0])
if not os.path.exists(out_dir):
    os.mkdir(out_dir)


# %%
# read in txt file as dictionary
text_lines = {}
with open(in_file, "r", encoding="utf-8") as text_file:
    for c, line in enumerate(text_file):
        text_lines[c] = line

# %%
# start counter for whole file
running_total = 0

# iterate through lines of file
for key in text_lines:

    # clean oddities
    line_clean = text_lines[key].replace("voice-over", "")
    line_clean = line_clean.replace(" : ", ": ")
    line_clean = line_clean.replace("@ @", ".")

    # make symbols consistent
    replace_dict = {
        "?": ".",
        "!": ".",
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

    # find all positions of capital strings
    #   regex match ".Mrs FOO BAR :"
    speaker_list = re.findall(
        r"(\b(?:[.]?\s*[A-Z]+[A-Z]+)\b(?:\s+(?:[A-Z]+[A-Z]+\s*[:]?)\b)*)", line_clean,
    )
    speaker_list = [x.strip(" ") for x in speaker_list]
    speaker_list = [x for x in speaker_list if x not in problem_list]

    # iterate through all speakers, without re-searching
    #   same start of line
    h_start = 0
    for c, spkr in enumerate(speaker_list):

        # find speaker location and following space
        h_loc = line_clean.find(spkr, h_start)
        h_space = line_clean.find(" ", h_loc)

        # test if character 2 places after space
        #   is upper (FIRST LAST vs LAST Word), walk
        #   until success
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
                    line_clean = line_clean[:h_space] + ":" + line_clean[h_space:]
                elif "," not in line_clean[h_end:h_col]:
                    line_clean = line_clean[:h_space] + ":" + line_clean[h_space:]

        h_start = h_end

    # determine location of colons, split line by colon
    loc_colons = [i.start() for i in re.finditer(":", line_clean)]
    line_parts = [line_clean[i:j] for i, j in zip(loc_colons, loc_colons[1:] + [None])]

    # initialize empty dict, add first key. line_dict will have format
    #   line_dict[key]: [values] = line_dict[speaker]: [word_count, sentence]
    line_dict = {}
    speaker_name = f"0. {line_clean.split(':')[0].split('.')[-1]}"
    line_dict[speaker_name] = []

    # start line counter
    line_total_dict = {}
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
        line_dict[speaker_name] = [num_words, parts_sentence]
        print(f"{speaker_name}: {num_words}, {parts_sentence}")
        print("")

        # get, add new dict key if we are in bounds
        if ind_count < (len(line_parts) - 1):
            speaker_name = f"{ind_count + 1}. {line_parts[ind_count].split('.')[-1]}"
            line_dict[speaker_name] = []

    # write line total to dict
    line_total_dict[key] = line_total

    # write out parcellated line to out_dir/Line*.csv
    outFile = os.path.join(out_dir, f"Line{key}.csv")
    with open(outFile, "w") as csv_file:
        writer = csv.writer(csv_file)
        for key, value in line_dict.items():
            writer.writerow([key, value])

# get file total
line_total_dict["Final"] = running_total
print(running_total)

# write out parcellated line to out_dir/Line*.csv
outFile = os.path.join(out_dir, "Total_Words.csv")
with open(outFile, "w") as csv_file:
    writer = csv.writer(csv_file)
    for key, value in line_total_dict.items():
        writer.writerow([key, value])
