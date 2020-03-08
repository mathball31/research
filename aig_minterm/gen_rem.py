from aag import *
from aig_minterm_functions import *
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
aag = AAG(input_lines)

inputs = []
for idx in range(aag.num_inputs//2):
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
            print("count: " + str(count))
            for idx, term in enumerate(terms):
                if count & (1 << idx) == 0:
                    minterm = concat(minterm, term)
                else:
                    minterm = concat(minterm, invert_term(term))
            minterms.append(minterm)
            print(minterm)
    return minterms

generate_all_minterms(inputs)
