from pathlib import Path
import subprocess
from contextlib import contextmanager
import os
import re
import csv
import shutil


#TODO make these be flags
verbose = False
ignore_errors = True
delete_temp_dirs = True
def msg(string):
    if verbose:
        print(string)
def error(string):
    if not ignore_errors:
        print(string)
"""
left, right: int, the potentially inverted net idx
returns: (net_name, gate_expression):
    net_name: int, the new net idx
    gate_expression: string, the resulting AAG line
"""
def make_and(aag, left, right):
    var = aag.get_var_idx() * 2
    return (var, str(var) + " " + str(left) + " " + str(right))

"""
minterm: List[int], all minterms that should be ANDed together
---returns---
gate_expressions: List[string], the list of additional lines to add to the AAG
minterm_product: string, the gate representing the entire AND tree
"""
def build_product(aag, minterm):
    gate_expressions = []
    while len(minterm) > 1:
        left = minterm.pop()
        if len(minterm) == 0:
            break
        right = minterm.pop()
        (net_name, gate_expression) = make_and(aag, left, right)
        minterm.append(net_name)
        gate_expressions.append(gate_expression)

        minterm_product = gate_expressions[-1]
    return gate_expressions, minterm_product

"""
minterm_product: string, the gate representing the entire AND tree
old_output: string, the output that will be XORed with the minterm_product
---returns---
xor_gates: List[string], the list of additional lines to add to the AAG
new_output: string, the (possibly inverted) gate that replaces the old output
"""
def build_xor(aag, minterm_product, old_output):
    x = int(minterm_product.split()[0])
    y = int(old_output)
    a1 = aag.get_var_idx() * 2
    a1_gate = str(a1) + " " + str(x+1) + " " + str(y)
    a2 = aag.get_var_idx() * 2
    a2_gate = str(a2) + " " + str(x) + " " + str(y+1)
    a3 = aag.get_var_idx() * 2
    a3_gate = str(a3) + " " + str(a1+1) + " " + str(a2+1)
    return ([a1_gate, a2_gate, a3_gate], str(a3 + 1))


"""
change directories to newdir. Do future file interactions from that directory for rest of indent block
optionally delete the new directory after work is finished.
"""
@contextmanager
def cd(newdir, delete_temp_dir=delete_temp_dirs):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        if delete_temp_dir:
            shutil.rmtree(newdir)

"""
aag: aag to run tests against
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
def rlrh(aag, gate, remainder, bit):
    gate_out = gate.split()[0]
    new_gate = gate_out + " " + str(bit) + " " + str(bit) + "\n"
    new_name = aag.file_name + "g" + gate_out + '_' + str(bit)
    aag_name = new_name + ".aag"
    aig_name = new_name + ".aig"
    sing_name = new_name + ".sing"
    approx_sing_name = new_name + "_approx.sing"
    stuck_aag = open(aag_name, "w")
    #change gate to x 0 0
    for line in aag.lines:
        if line == gate:
            stuck_aag.write(new_gate)
        else:
            stuck_aag.write(line)
    stuck_aag.close()

    #convert to aig
    aigtoaig = ["aigtoaig", aag_name, aig_name]
    subprocess.run(aigtoaig)

    #convert to sing
    aigmultopoly = ["aigmultopoly", aig_name, sing_name, "--non-incremental", "--singular", "-b"]
    process = subprocess.run(aigmultopoly, capture_output = True, text=True)
    if process.stderr.strip() != "":
        #TODO be smarter about this
        error("There was an error during aigmultopoly on gate " + new_gate.strip() +
                " with remainder: " + remainder)
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
            approx_sing_file.write("  " + remainder + ";\n")
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

    
"""
convert a remainder written singular style to something easier to work with
"""
def clean_remainder(remainder):
    cleaned_remainder = re.sub('[\(\) ]', '', remainder)
    cleaned_remainder = re.sub('1-', '-', cleaned_remainder)
    cleaned_remainder = re.sub('\*', '.', cleaned_remainder)
    cleaned_remainder = cleaned_remainder.replace("number", "")
    return cleaned_remainder



# pick gate
#TODO save files between each remiander/between batches, instead of just at the end
"""
perform a rectificiton check to find single fix rectifiable nets.
The test attempts to modify aag to match aag+remainder
"""
def reduce_rlrh(aag, remainder):
    cleaned_remainder = clean_remainder(remainder)

    msg( cleaned_remainder)
    temp_dir_str = aag.file_name + '_' + cleaned_remainder
    temp_dir = Path(temp_dir_str)
    #TODO write in rectifiables each time before turning this on
    """
    if temp_dir.is_dir():
        print("duplicate remainder skipped")
        return []
        """
    temp_dir.mkdir(exist_ok = True)
    gate_residues = {}
    rectifiables = []
    with cd(temp_dir_str):
        for gate in aag.gates:
            (rL, J0L, ringL) = rlrh(aag, gate, remainder, 0)
            (rH, J0H, ringH) = rlrh(aag, gate, remainder, 1)
            if J0L != J0H:
                error("Error: rL and rH have different J0")
            if ringL != ringH:
                error("Error: rL and rH have different ring")
            if rL == None or rH == None:
                continue

            msg("Gate: " + gate.strip())
            msg("rL: " + str(rL).strip())
            msg("rH: " + str(rH).strip())
            #create singular file to reduce rL*rH by J0
            gate_out = gate.split()[0]
            sing_file_name = aag.file_name + "g" + gate_out + "_rLrH.sing"
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
            if residue.strip() == "0":
                print("0 remainder for remainder: " + cleaned_remainder + ", \agate: " + gate.strip())
                rectifiables.append((cleaned_remainder, gate.strip()))
            msg("residue: " + residue)
            gate_residues[gate.strip()] = residue.strip()

        #TODO maybe do this incrementally instead of at the end.
        csv_file_name = aag.file_name + "_r_" + cleaned_remainder + ".csv"
        with open(csv_file_name, 'w') as f:
            w = csv.writer(f)
            w.writerows(gate_residues.items())
    return rectifiables
