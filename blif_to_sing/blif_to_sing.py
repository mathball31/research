"""
This script is designed to produce a Singular file (.sing) ready to perform a verification test
on a given circuit and specification.

The test circuit must be a .blif file
    NOTE: currently it must be mapped. a non-mapped .blif won't crash the script,
    but the results are likely (almost certaintly) incorrect.
    TODO: fix this^^

The specification can be a circuit (.blif, same restrictions as above) or a polynomial.

The output file should be a .sing.

To perform the verification, run Singular (https://www.singular.uni-kl.de/) then run the command:
    <"output_file_name.sing";

If the result is zero, the circuit matches the spec. Otherwise there is a bug.

usage:
    python blif_to_sing.py TEST_FILE_NAME.blif SING_FILE_NAME.sing [--spec_file_name SPEC_FILE_NAME]
        [--spec_poly SPEC_POLY]

    NOTE: --spec_file_name OR --spec_poly MUST be given. 
    If both are given, the script will use the file, NOT the polynomial

Options:
    -p SPEC_POLY
    --spec_poly SPEC_POLY
        The specification polynomial
        the poly should not contain any equals signs
        E.G. the polynomial "Z=A*B" should be passed in as "Z-A*B" or "\-Z+A*B".
        note that leading '-'s must be escaped

    -f SPEC_FILE_NAME
    --spec_file_name SPEC_FILE_NAME
        The name of the .blif file representing the specification or "Golden Model" circuit.
        NOTE: this is currently unimplemented
        TODO: implement verification against a circuit

"""

import sys
import argparse
import copy
import itertools
from blif_to_sing_functions import *

parser = argparse.ArgumentParser()
parser.add_argument('test_file_name', help='.blif representing circuit to be verified')
parser.add_argument('sing_file_name', help='.sing script that will perform verification')
parser.add_argument('--spec_file_name', '-f', default=False, 
        help='.blif representing specification circuit')
parser.add_argument( '--spec_poly', '-p', default=False, help='specification polynomial')

args = parser.parse_args()

if args.spec_file_name and args.spec_poly:
    print("WARNING: spec_poly and spec_file defined. spec_file will be used")
if not args.spec_file_name and not args.spec_poly:
    parser.print_help()
    raise argparse.ArgumentTypeError("no spec defined")

if args.spec_poly and "=" in args.spec_poly:
    print("WARNING: spec_poly contains '='. This will result in invalid syntax in the Singular file")
    print("HINT: subtract the left side of the equation over to the right")

test_file = open(args.test_file_name, "r")
sing_file = open(args.sing_file_name, "w")
if args.spec_file_name:
    spec_file = open(args.spec_file_name, "r")



#parse test file
(test_gates, test_primary_inputs, test_primary_outputs) = blif_to_gates(test_file)

#add primary inputs to gate list
for in_gate in test_primary_inputs:
    test_gates[in_gate] = Gate(in_gate, [], "INPUT")

#derive order for test circuit
order = khan_topo_sort(test_gates, test_primary_inputs, test_primary_outputs)

#maybe parse spec file
if args.spec_file_name:
    (spec_gates, spec_primary_inputs, spec_primary_outputs) = blif_to_gates(spec_file)

    #add primary inputs to gate list
    for in_gate in spec_primary_inputs:
        spec_gates[in_gate] = Gate(in_gate, [], "INPUT")

    spec_order = khan_topo_sort(spec_gates, spec_primary_inputs, spec_primary_outputs)


#derive order string
#TODO integrate spec file if present
order_string = ""
for gate in order:
    order_string += ", " +  gate.output
sing_file.write("ring r = 0, (Z, A, B" + order_string + "), lp;\n\n")

#derive output polynomial
output_poly = "poly fZ = -Z"
k = 1;
for term in test_primary_outputs:
    output_poly += " + %d*%s" % (k, term)
    k *= 2

#derive polynomial for input A
in_A_poly = "poly fA = -A"
k = 1;
for term in filter(lambda term: term.startswith('a'), test_primary_inputs):
    in_A_poly += " + %d*%s" % (k, term)
    k *= 2

#derive polynomial for input B
in_B_poly = "poly fB = -B"
k = 1;
for term in filter(lambda term: term.startswith('b'), test_primary_inputs):
    in_B_poly += " + %d*%s" % (k, term)
    k *= 2

sing_file.write(output_poly + ";\n")
sing_file.write(in_A_poly + ";\n")
sing_file.write(in_B_poly + ";\n")

#write polys
for gate in order:
    sing_file.write("// " + gate.gate + "\n" + gate_to_poly(gate))

#derive ideal J
ideal_string = ""
for poly_num in range(0, gate_to_poly.poly_num + 1):
    ideal_string += "f%d, " % (poly_num)

sing_file.write("ideal J = (fZ, fA, fB, " + ideal_string[0:-2] + ");\n")

#derive ideal J0
ideal0_string = ""
for gate in test_primary_inputs:
    ideal0_string += "f%s, " % (gate)

sing_file.write("ideal J0 = (" + ideal0_string[0:-2] + ");\n")


#write spec_poly
if args.spec_file_name:
    print("not implemented")

if args.spec_poly:
    sing_file.write("poly f_spec =" + args.spec_poly + ";\nreduce(f_spec, J + J0);\n")

test_file.close()
sing_file.close()
if args.spec_file_name:
    spec_file.close()
