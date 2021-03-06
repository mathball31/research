"""
This is the main file.

This generates remainders for a given circuit, then runs rectification checks of the circuit against the circuit
with the remainder.

"""
from aag import *
from approx_mult_functions import *
from pathlib import Path
import argparse
from itertools import chain, combinations
from random import randrange, choice, sample
import ast

parser = argparse.ArgumentParser()
parser.add_argument('input_file_name', help='.aag representing input circuit')
parser.add_argument('num_remainders', type=int, help='number of remainders to generate')
parser.add_argument('num_outputs', type=int, default = 1, help='number of outputs to affect')

args = parser.parse_args()

aag = AAG(args.input_file_name)

inputs = []
for idx in range(aag.num_inputs//2):
    inputs.append("a(" + str(idx) + ")")
    inputs.append("b(" + str(idx) + ")")


"""
invert an algebraic term
"""
def invert_term(term):
    return "(1-" + term + ")"

"""
multiply two algebraic terms
"""
def concat(left, right):
    if left == "":
        return right
    return left + " * " + right

"""
add two algebraic terms
"""
def add(left, right):
    if left == "":
        return right
    return left + " + " + right


"""
generate the powerset of a given list
"""
def powerset(input_list):
    return list(chain.from_iterable(combinations(input_list,r) for r in range(1, len(input_list) + 1)))

"""
generate all possible minterms for the given inputs
"""
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

"""
generate all possible one output remainders for the given inputs
"""
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
generate a random coefficient for an arithmetic circuit with the given number of outputs
"""
def create_coefficient(num_outputs):
    outputs = []
    if num_outputs < len(powers_of_2)/2:
        outputs = sample(powers_of_2[0:len(powers_of_2)//2], num_outputs)
    else:
        outputs = sample(powers_of_2, num_outputs)

    coefficient = ""
    for output in sorted(outputs):
        coefficient = add(coefficient, output)
    return "(" + coefficient + ")"


"""
Generate `num` random remainders for a given list of `inputs`.
These can have any number of outputs, determined by create_coefficient

Skips remainders that have been previously tried

NOTE: total_num = num_outputs * (2^num_inputs-1)
"""
def generate_random_remainders(inputs, num, num_outputs, tried_remainders):
    count = 0
    #itrs is a safety valve, and will ensure this doesn't run forever
    itrs = 0
    
    remainders = set()
    while count < num and itrs < 2*num:
        #pick a random output
        remainder = create_coefficient(num_outputs)
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
        if clean_remainder(remainder) not in tried_remainders and test_sum != 0:
            count += 1
            tried_remainders.add(clean_remainder(remainder))
            remainders.add(remainder)
        itrs += 1

    if itrs >= 2*num:
        print("max iteration reached")
        print("generating " + str(count) + " remainders")
    return list(remainders)


temp_dir_str = aag.file_name + '_' + str(args.num_outputs) + 'out_remainders'
temp_dir = Path(temp_dir_str)
temp_dir.mkdir(exist_ok = True)
with cd(temp_dir_str, False):

    remainders = []
    max_num = aag.num_outputs * (3** aag.num_inputs - 1)
    rectifiables = set()
    unrectifiables = set()
    try:
        with open("rectifiables.txt", "r") as f:
            rectifiables = set(f.readlines())
    except FileNotFoundError:
        pass
    try:
        with open("unrectifiables.txt", "r") as f:
            unrectifiables = set(f.readlines())
    except FileNotFoundError:
        pass
    tried_remainders = {ast.literal_eval(tup_string)[0] for tup_string in rectifiables}
    tried_remainders.update([string.strip() for string in unrectifiables])
    remainders = generate_random_remainders(inputs, args.num_remainders, args.num_outputs, tried_remainders)

    """
    for rem in remainders:
        print(rem)
    print(len(remainders))
    """


    for count, term in enumerate(remainders):
        #TODO let user pick how often to check in
        if count % 1 == 0:
            print("term " + str(count) + ": " + clean_remainder(term))
        rectifiable_gates = reduce_rlrh(aag, term)
        if len(rectifiable_gates) == 0:
            unrectifiables.add(clean_remainder(term))
        rectifiables.update([str(tup) for tup in rectifiable_gates])

    with open("rectifiables.txt", "w") as f:
        for line in sorted(rectifiables):
            f.write(line.strip() + "\n")
    with open("unrectifiables.txt", "w") as f:
        for line in sorted(unrectifiables):
            f.write(line.strip() + "\n")
    



