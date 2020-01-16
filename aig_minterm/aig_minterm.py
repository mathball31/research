"""
This will be the minterm_change but for aig instead of blif
"""
#TODO

from blif_to_sing_functions import *
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

input_lines = input_file.readlines()
header = input_lines[0].split()
max_idx = header[1]
num_inputs = head[2]
num_latches = head[3]
num_outputs = head[4]
num_ands = head[5]


and_count = 0
minterm = args.minterm
new_gates = []
"""
TODO
x build minterm as and gate tree
x Find highest AND gate index
. rename output
	- this is actually super easy. Just replace the line of the output with
	the new one
. XOR minterm with old output to get new output
"""

"""
TODO
main loop
. copy existing file until output we want.
. Replace output with new output variable
. Add new AND gates at the end
"""

start_of_outputs = num_inputs + num_latches
outputs = input_lines[start_of_outputs:start_of_outputs + num_outputs]

if args.output_idx//2 not in outputs:
	print("output_idx is not an existing output")
	exit()
