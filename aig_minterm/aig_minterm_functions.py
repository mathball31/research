
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

        

from contextlib import contextmanager
import os

@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
