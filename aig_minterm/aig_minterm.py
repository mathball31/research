"""
This will be the minterm_change but for aig instead of blif
"""
#TODO

import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input_file_name', help='.aag/aig representing input circuit')
parser.add_argument('output_file_name', help='.aag/aig representing modified circuit')
#TODO handle multiple nets
parser.add_argument('output_idx', type=int, help='index of output which will change with minterm change')
#TODO handle multiple minterms
parser.add_argument('minterm', nargs='+', type=int, help='minterm to change (space separated)')

args = parser.parse_args()

input_file = open(args.input_file_name, "r")
output_file = open(args.output_file_name, "w")

header = input_file.readline().split()
max_idx = header[1]
num_inputs = head[2]
num_latches = head[3]
num_outputs = head[4]
num_ands = head[5]


if args.output_idx//2 > num_outputs:
    print("output_idx is greater than number of outputs")
    exit()

and_count = 0
minterm = args.minterm
new_gates = []
"""
TODO
\ build minterm as and gate tree
. Find highest AND gate index
. rename output
. XOR minterm with old output to get new output
"""

#TODO find max_idx
int max_idx = -1
"""
get an new unused variable name
---returns---
new_var: int, the new variable
"""
#TODO figure if any doubling needs to happen here
def get_var():
    max_idx += 1
    return max_idx
    

"""
left, right: int, the potentially inverted net idx
returns: (net_name, gate_expression):
    net_name: int, the new net idx
    gate_expression: string, the resulting AAG line
"""
def make_and(left, right):
    var_idx = get_var()
    return (var_idx, str(var_idx) + " " + str(left) + " " + str(right))

"""
minterm: List[int], all minterms that should be ANDed together
---returns---
gate_expressions: List[string], the list of additional lines to add to the AAG
"""
def build_product(minterm):
    gate_expressions = []
    while len(minterm) > 1:
        left = minterm.pop()
        if len(minterm) == 0:
            break
        right = minterm.pop()
        #TODO implement make_and
        (net_name, gate_expression) = make_and(left, right)
        minterm.append(net_name)
        gate_expressions.append(gate_expressions)


    return gate_expressions



