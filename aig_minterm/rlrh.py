"""
This script takes an aag file representing an exact multiplier circuit, and a single minterm 
remainder. The remainder should be the result of reducing an approximate multiplier against an exact
spec.

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
    . reduce rL*rH by J0
        x find J0

"""

from aig_minterm_functions import *
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
input_file = open(args.input_file_name, "r")

input_lines = input_file.readlines()
header = [int(string) for string in input_lines[0].split()[1:] ]
init_max_index(header[0])
num_inputs = header[1]
num_latches = header[2]
num_outputs = header[3]
num_ands = header[4]
num_lines = num_inputs + num_latches + num_outputs + num_ands

start_ands = num_inputs + num_latches + num_outputs + 1
gates = input_lines[start_ands: start_ands + num_ands]


cleaned_remainder = re.sub('[\(\) ]', '', args.remainder)
cleaned_remainder = re.sub('1-', '-', cleaned_remainder)
print( cleaned_remainder)
temp_dir_str = input_file_name + '_' + cleaned_remainder
temp_dir = Path(temp_dir_str)
temp_dir.mkdir(exist_ok = True)

"""
gate: string, the gate that should be set to bit
bit: int {0, 1}, value that gate should be set to
---returns---
remainder: the remainder from reducing approx_spec by the exact multiplier with gate stuck at bit
    (if bit == 0, this is rL, if bit == 1, this is rH)
---Side effects---
creates 4 files with the following mapping:
    name.aag -> nameg<gate>_<bit>.<aag, aig, sing>, nameg<gate_<bit>_approx.sing
    eg if gate = "10 12 5", bit = 0, and name = mult2, this function creates:
        mult2g10_0.aag
        mult2g10_0.aig
        mult2g10_0.sing
        mult2g10_0_approx.sing
Also runs aigtoaig, aigmultopoly, and Singular to generate these and get the remainder

"""
def remainder(gate, bit):
    gate_out = gate.split()[0]
    new_gate = gate_out + " " + str(bit) + " " + str(bit) + "\n"
    new_name = input_file_name + "g" + gate_out + '_' + str(bit)
    aag_name = new_name + ".aag"
    aig_name = new_name + ".aig"
    sing_name = new_name + ".sing"
    approx_sing_name = new_name + "_approx.sing"
    aag = open(aag_name, "w")
    #change gate to x 0 0
    for line in input_lines:
        if line == gate:
            aag.write(new_gate)
        else:
            aag.write(line)
    aag.close()

    #convert to aig
    aigtoaig = ["aigtoaig", aag_name, aig_name]
    subprocess.run(aigtoaig)
    #TODO optionally delete aag

    #convert to sing
    aigmultopoly = ["aigmultopoly", aig_name, sing_name, "--non-incremental", "--singular", "-b"]
    process = subprocess.run(aigmultopoly, capture_output = True, text=True)
    if process.stderr.strip() != "":
        #TODO be smarter about this
        print("There was an error during aigmultopoly on gate " + new_gate, end = '')
        return None, "", ""

    #modify spec
    sing_file = open(sing_name, "r")
    approx_sing_file = open(approx_sing_name, "w")
    sing_lines = sing_file.readlines()
    #TODO search more resiliantly
    slices_idx = sing_lines.index("ideal slices =\n")
    last_line_of_spec = sing_lines[slices_idx -1]
    new_last_line = last_line_of_spec.replace(';', ' +')
    for idx, line in enumerate(sing_lines):
        if idx == slices_idx - 1:
            approx_sing_file.write(new_last_line)
            approx_sing_file.write("  " + args.remainder + ";\n")
        else:
            approx_sing_file.write(line)
    #extract ring
    #TODO search more resiliantly
    ring_idx = sing_lines.index("ring R  = 0, (\n")
    ring = ""
    for line in sing_lines[ring_idx:]:
        ring += line
        if line.startswith(')'):
            break
    #extract ideal J0
    #TODO search more resiliantly
    J0_idx = sing_lines.index("ideal FI =\n")
    J0 = "ideal J0 =\n"
    for line in sing_lines[J0_idx+1:]:
        J0 += line
        if line.startswith(';'):
            break

    approx_sing_file.write("exit;")
    sing_file.close()
    approx_sing_file.close()
    
    #run Singular
    singular = ["Singular", approx_sing_name, "-q"]
    process = subprocess.run(singular, capture_output = True, text=True)
    remainder = process.stdout

    return remainder, J0, ring

    


# pick gate
with cd(temp_dir_str):
    #TODO
    for gate in gates:
        """ TODO
        x change to x 0 0
            x convert to aig
            x convert to sing
            x change sing spec
            x run singular
        x change to x 1 1
            x repeat above
        . store remainders
        x find J0
        . reduce rL*rH by J0
        """
        (rL, J0L, ringL) = remainder(gate, 0)
        (rH, J0H, ringH) = remainder(gate, 1)
        if J0L != J0H:
            print("Error: rL and rH have different J0")
        if ringL != ringH:
            print("Error: rL and rH have different ring")
        if rL == None or rH == None:
            continue

        print("Gate: " + gate.strip())
        print("rL: " + str(rL).strip())
        print("rH: " + str(rH).strip())
        #create singular file to reduce rL*rH by J0
        gate_out = gate.split()[0]
        sing_file_name = input_file_name + "g" + gate_out + "_rLrH.sing"
        sing_file = open(sing_file_name, "w")
        sing_file.write(ringL)
        sing_file.write("poly rL =\n" + rL + ";\n")
        sing_file.write("poly rH =\n" + rH + ";\n")
        sing_file.write(J0L)
        sing_file.write("reduce (rL * rH, J0);\n")
        sing_file.write("exit;")
        sing_file.close()

        #run Singular
        singular = ["Singular", sing_file_name, "-q", "--no-warn"]
        process = subprocess.run(singular, capture_output = True, text=True)
        residue = process.stdout
        print("residue: " + residue)


