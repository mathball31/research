"""
This script is designed to take an arithmetic circuit in blif format, 
and output an approximate circuit with some minterms changed
"""
import sys
import argparse
from blif_to_sing_functions import *



parser = argparse.ArgumentParser()
parser.add_argument('input_file_name', help='.blif representing input circuit')
parser.add_argument('output_file_name', help='.blif representing modified circuit')
#TODO handle multiple nets
parser.add_argument('output_net', help='output net which will change with minterm change')
#TODO handle multiple minterms
parser.add_argument('minterms', nargs='+', help='minterms to change (space separated)')

args = parser.parse_args()

input_file = open(args.input_file_name, "r")
output_file = open(args.output_file_name, "w")


#parse input file to get primary inputs and outputs
(gates, primary_inputs, primary_outputs) = blif_to_gates(input_file)

input_file.close()
input_file = open(args.input_file_name, "r")

for minterm in args.minterms:
    minterm_tokens = minterm.split('*')
    #check inputs
    for token in minterm_tokens:
        if token.replace('~', '', 1) not in primary_inputs:
            print("WARNING: minterm contains terms not in primary_inputs! This probably won't work")

if args.output_net not in primary_outputs:
    print("WARNING: output_net not in primary outputs! This probably won't work")

def make_gate_string(gate, Y, A, B):
    return ".gate " + gate + " A=" + A + " B=" + B  + " Y=" + Y + "\n"

input_inversions = []
def handle_offset(term):
    term = term.replace('~', '', 1)
    if term not in input_inversions:
        input_inversions.append(term)
        output_file.write(".gate INVX1 A=" + term + " Y=" + term + "inv\n")
    return term + "inv"
    
def write_minterm_change(output_file, gates, output_net, minterms):
    full_terms = []
    output_file.write("#begin error\n")
    for minterm in minterms:
        #AND all terms in minterm together
        terms = minterm.split('*')
        while len(terms) > 1:
            A = terms.pop(0)
            if A.startswith('~'):
                A = handle_offset(A)

            B = terms.pop(0)
            if B.startswith('~'):
                B = handle_offset(B)

            #get new output name
            write_minterm_change.error_num += 1
            Y = "error" + str(write_minterm_change.error_num)
            while Y in gates:
                write_minterm_change.error_num += 1
                Y = "error" + str(write_minterm_change.error_num)

            terms.append(Y)
            output_file.write(make_gate_string("AND2X1", Y, A, B))

        full_terms.extend(terms) #should only be one term

    #OR all minterms together
    while len(full_terms) > 1:
        A = full_terms.pop(0)
        B = full_terms.pop(0)
        #get new output name
        write_minterm_change.error_num += 1
        Y = "error" + str(write_minterm_change.error_num)
        while Y in gates:
            write_minterm_change.error_num += 1
            Y = "error" + str(write_minterm_change.error_num)
        full_terms.append(Y)
        output_file.write(make_gate_string("OR2X1", Y, A, B))

    #XOR output with SOP expression
    output_file.write(make_gate_string("XOR2X1", output_net, output_net + "_old", terms[0]))
    output_file.write("#end error\n")

write_minterm_change.error_num = -1



line = input_file.readline()
while line != "":
    if line.startswith(".gate") and args.output_net in line:
        line = line.replace("=" + args.output_net, "=" + args.output_net + "_old")
        write_minterm_change(output_file, gates, args.output_net, args.minterms)

    output_file.write(line)
    line = input_file.readline()

input_file.close()
output_file.close()
