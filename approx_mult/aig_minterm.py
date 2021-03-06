"""
This is like minterm_change but for aig instead of blif

"""

from approx_mult_functions import *
from aag import *
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input_file_name', help='.aag/aig representing input circuit')
parser.add_argument('output_file_name', help='.aag/aig representing modified circuit')
parser.add_argument('output_idx', type=int, help='index of output which will change with minterm change')
#TODO handle multiple minterms
parser.add_argument('minterm', nargs='+', type=int, help='minterm to change (space separated)')

args = parser.parse_args()

aag = AAG(args.input_file_name)
output_file = open(args.output_file_name, "w")


and_count = 0
minterm = args.minterm
new_gates = []

print(aag.outputs)

if args.output_idx not in aag.outputs:
	print("output_idx is not an existing output")
	exit()

# this seems to be working, now we just need to build the xor
product_gates, minterm_product = build_product(aag, minterm)

xor_gates, new_output = build_xor(aag, minterm_product, args.output_idx)

num_new_ands = len(product_gates) + len(xor_gates)
num_ands = aag.num_ands + num_new_ands

#write output file
header_string = "aag " + str(aag.max_idx) + " " +  str(aag.num_inputs) + " " + str(aag.num_latches) + " " + str(aag.num_outputs) + " " + str(aag.num_ands) + "\n"
output_file.write(header_string)
for line in aag.lines[1:aag.num_lines + 1]:
    if line == str(args.output_idx) + '\n':
        new_output_str = new_output + '\n'
        output_file.write(new_output_str)
    else:
        output_file.write(line)

# write new lines
for line in product_gates:
    output_file.write(line + "\n")
for line in xor_gates:
    output_file.write(line + "\n")

# write comments etc
for line in aag.lines[aag.num_lines + 1:]:
    output_file.write(line)

# write my info
#TODO get date
#TODO link to website
signiture = "This file has been edited by aig_minterm\n"
output_file.write(signiture)
