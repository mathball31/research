#TODO
"""
x take multiplier aag, 
    x change a gate to `x 0 0`
        x run through aigtoaig to get .aig (this fixes some weird issues)
        x run through aigmultopoly to get .sing
        x modify spec to match approx
        x run through Singular to get remainder
        x repeat above but with `x 1 1`
    x repeat above with other gates
    . repeat with different approximate spec

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
        return None

    #TODO change sing spec
    sing_file = open(sing_name, "r")
    approx_sing_file = open(approx_sing_name, "w")
    sing_lines = sing_file.readlines()
    #TODO assert that this works
    slices_idx = sing_lines.index("ideal slices =\n")
    last_line_of_spec = sing_lines[slices_idx -1]
    new_last_line = last_line_of_spec.replace(';', ' +')
    for idx, line in enumerate(sing_lines):
        if idx == slices_idx - 1:
            approx_sing_file.write(new_last_line)
            approx_sing_file.write("  " + args.remainder + ";\n")
        else:
            approx_sing_file.write(line)

    approx_sing_file.write("exit;")
    sing_file.close()
    approx_sing_file.close()
    
    #run Singular
    singular = ["Singular", approx_sing_name, "-q"]
    process = subprocess.run(singular, capture_output = True, text=True)
    remainder = process.stdout
    return remainder

    


# pick gate
with cd(temp_dir_str):
    #TODO
    for gate in gates:
        """ TODO
        x change to x 0 0
            x convert to aig
            x convert to sing
            x change sing spec
            . run singular
        . change to x 1 1
            . repeat above
        """
        rL = remainder(gate, 0)
        rH = remainder(gate, 1)
        print("Gate: " + gate.strip())
        print("rL: " + str(rL).strip())
        print("rH: " + str(rH).strip())

