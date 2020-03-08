from aag import *
from approx_mult_functions import *
import sys
import os
from pathlib import Path
import argparse
import subprocess
import re
from itertools import chain, combinations
from random import randrange, choice

parser = argparse.ArgumentParser()
parser.add_argument('input_file_name', help='.aag/aig representing input circuit')
parser.add_argument('num_remainders', type=int, help='number of remainders to generate')

args = parser.parse_args()

aag = AAG(args.input_file_name)

inputs = []
for idx in range(aag.num_inputs//2):
    inputs.append("a(" + str(idx) + ")")
    inputs.append("b(" + str(idx) + ")")


def invert_term(term):
    return "(1-" + term + ")"

def concat(left, right):
    if left == "":
        return right
    return left + " * " + right


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
                if count & (1 << idx) == 0:
                    minterm = concat(minterm, term)
                else:
                    minterm = concat(minterm, invert_term(term))
            minterms.append(minterm)
    return minterms

powers_of_2 = []
for idx in range(aag.num_outputs):
    powers_of_2.append("number(2)^" + str(idx))
def generate_all_remainders(inputs):
    powers_of_2 = []
    for idx in range(aag.num_outputs):
        powers_of_2.append("number(2)^" + str(idx))
    minterms = generate_all_minterms(inputs)
    remainders = []
    for term in minterms:
        for power in powers_of_2:
            remainders.append(concat(power, term))
    return remainders

"""
NOTE: total_num = num_outputs * (2^num_inputs-1)
"""
def generate_random_remainders(inputs, num):
    count = 0
    #itrs is a safety valve, and will ensure this doesn't run forever
    itrs = 0
    remainders = set()
    while count < num and itrs < 2*num:
        #pick a random output
        remainder = choice(powers_of_2)
        test_sum = 0
        for term in inputs:
            #pick if a term is ommited, included, or inverted
            test = randrange(3)
            test_sum += test
            if test == 1:
                remainder = concat(remainder, term)
            elif test == 2:
                remainder = concat(remainder, invert_term(term))
        #ensure that remainder is new and contains inputs
        if remainder not in remainders and test_sum != 0:
            count += 1
            remainders.add(remainder)
        itrs += 1
    return list(remainders)


remainders = []
max_num = aag.num_outputs * (3** aag.num_inputs - 1)
if args.num_remainders > max_num:
    print("you requested more remainders than can exist for this circuit. generating all " 
            + str(max_num) + " remainders")
if args.num_remainders >= max_num:
    remainders = generate_all_remainders(inputs)
else:
    remainders = generate_random_remainders(inputs, args.num_remainders)

"""
for rem in remainders:
    print(rem)
print(len(remainders))
"""

temp_dir_str = aag.file_name + '_remainders'
temp_dir = Path(temp_dir_str)
temp_dir.mkdir(exist_ok = True)
with cd(temp_dir_str):
    for count, term in enumerate(remainders):
        if count % 1 == 0:
            print("term " + str(count) + ": " + term)
        gate_residue = reduce_rlrh(aag, term)
