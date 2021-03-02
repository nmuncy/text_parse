# %%
import os
import re
import csv
import string

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


# set orientings vars, make output location
work_dir = os.getcwd()
in_file = os.path.join(work_dir, "w_spok_1990.txt")
out_dir = os.path.join(work_dir, "csv_files")
if not os.path.exists(out_dir):
    os.mkdir(out_dir)

# read in txt file as dictionary
text_lines = {}
with open(in_file, "r", encoding="utf-8") as text_file:
    for c, line in enumerate(text_file):
        text_lines[c] = line

# start counter for whole file
running_total = 0

# iterate through lines of file
#   only tested on lines 0-2
for key in text_lines:
    # key = 2

    # initialize empty dict, add first key. line_dict will have format
    #   line_dict[key]: [values] = line_dict[speaker]: [word_count, sentence]
    line_dict = {}
    speaker_name = f"0-{text_lines[key].split(':')[0]}"
    line_dict[speaker_name] = []

    # clean line - hardcoded to just get working
    #   TODO regex this nonsense
    line_clean = text_lines[key]
    line_clean = line_clean.replace("?", ".")
    line_clean = line_clean.replace("!", ".")
    line_clean = line_clean.replace("@", "")
    line_clean = line_clean.replace(".ANNOUNCER", ".ANNOUNCER:")
    line_clean = line_clean.replace(".SHERR", ".SHERR:")
    line_clean = line_clean.replace(".WALTERS", ".WALTERS:")
    line_clean = line_clean.replace(".DOWNS", ".DOWNS:")
    line_clean = line_clean.replace(".STOSSEL", ".STOSSEL:")
    line_clean = line_clean.replace("Dr.", ".Dr")
    line_clean = line_clean.replace("Mr.", ".Mr")
    line_clean = line_clean.replace("Ms.", ".Ms")
    line_clean = line_clean.replace('"', "")
    line_clean = line_clean.replace("voice-over", "")

    # determine location of colons, split line by colon
    loc_colons = [i.start() for i in re.finditer(":", line_clean)]
    line_parts = [line_clean[i:j] for i, j in zip(loc_colons, loc_colons[1:] + [None])]

    # start line counter
    line_total_dict = {}
    line_total = 0

    # loop through line sections
    for ind_count, sentence in enumerate(line_parts):

        # set count variable to avoid overwriting dict key
        #   w/same speaker name
        h_count = ind_count + 1

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
        # print(f"{speaker_name}: {num_words}, {parts_sentence}")
        # print("")

        # get, add new dict key if we are in bounds
        if ind_count < (len(line_parts) - 1):
            speaker_name = f"{h_count}-{line_parts[ind_count].split('.')[-1]}"
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
