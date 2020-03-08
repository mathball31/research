"""
This script takes an aag file representing an exact multiplier circuit, and a single minterm 
remainder. The remainder should be the result of reducing an approximate multiplier against an exact
spec.

Most of the functionality is in the function reduce_rlrh() from aig_minterm_functions.py

For each and gate in the circuit, this creates a new aag with that gate set to 0 and set to 1.
It then (through a series of steps) generates rL and rH, made by running the two new aags against
the approximate spec.

All intermediate files will be created in a folder named after the input file and the remainder.
eg `python3 rlrh.py mult2.aag "a(0) * (1 - b(1))"` -> `mult2_a0*-b1/`

To run: 
    python3 rlrh.py multiplier.aag "<remainder>"
where:
    multipler.aag: path to exact multiplier aag file
    <remainder>: Singular style minterm
        e.g.: "a(0)*b(1)", "number(2)^3*a(3)*(1-a(2))*b(2)*(1-b(0))"
        use quotes to escape the '('s and ')'s

NOTE: This was devolped with python version 3.7.6. It will probably work for any 3.7.x, but will 
*NOT* work for an version less than 3.7.

TODO
x take multiplier aag, 
    x change a gate to `x 0 0`
        x run through aigtoaig to get .aig (this fixes some weird issues)
        x run through aigmultopoly to get .sing
        x modify spec to match approx
        x run through Singular to get remainder
        x repeat above but with `x 1 1`
    x repeat above with other gates
    . store remainders
    x reduce rL*rH by J0
        x find J0

"""

from approx_mult_functions import *
from aag import AAG
import sys
import os
from pathlib import Path
import argparse
import subprocess
import re


parser = argparse.ArgumentParser()
parser.add_argument('input_file_name', help='.aag/aig representing input circuit')
#parser.add_argument('output_idx', type=int, help='index of output which will change with minterm change')
#parser.add_argument('minterm', nargs='+', type=int, help='minterm to change (space separated)')

#TODO figure out how to accept remainder
parser.add_argument('remainder', type=str, 
        help='singular style remainder of approximate multiplier. eg number(2)^k * a(0) * (1-b(2))')

args = parser.parse_args()

input_file_name, input_file_ext = os.path.splitext(args.input_file_name)
#input_file = open(args.input_file_name, "r")

#input_lines = input_file.readlines()
aag = AAG(args.input_file_name)

reduce_rlrh(aag, args.remainder)
