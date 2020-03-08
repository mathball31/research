from aig_minterm_functions import *
from rlrh import *
import sys
import os
from pathlib import Path
import argparse
import subprocess
import re
from itertools import chain, combinations

parser = argparse.ArgumentParser()
parser.add_argument('input_file_name', help='.aag/aig representing input circuit')

args = parser.parse_args()

input_file_name, input_file_ext = os.path.splitext(args.input_file_name)
input_file = open(args.input_file_name, "r")

input_lines = input_file.readlines()
header = [int(string) for string in input_lines[0].split()[1:] ]
init_max_index(header[0])
num_inputs = header[1]
num_latches = header[2]
num_outputs = header[3]
num_ands = header[4]
num_lines = num_inputs + num_latches + num_outputs + num_ands

inputs = []
for idx in range(num_inputs//2):
    inputs.append("a(" + str(idx) + ")")
    inputs.append("b(" + str(idx) + ")")


def invert_term(term):
    return "(1-" + term + ")"

def concat(left, right):
    if left == "":
        return right
    return "(" + left + ")*(" + right + ")"


def powerset(input_list):
    return list(chain.from_iterable(combinations(input_list,r) for r in range(1, len(input_list) + 1)))

def generate_all_minterms(inputs):
    pow_set = powerset(inputs)

    minterms = []
    for terms in pow_set:
        num_terms = len(terms)
        for count in range(2**num_terms):
            minterm = ""
            for idx, term in enumerate(terms):
                if count ^ (1 << idx) == 0:
                    minterm = concat(minterm, term)
                else:
                    minterm = concat(minterm, invert_term(term))
            minterms.append(minterm)
    return minterms



