"""
get an new unused variable name
---returns---
new_var: int, the new variable
"""
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
minterm_product: string, the gate representing the entire AND tree
"""
def build_product(minterm):
    gate_expressions = []
    while len(minterm) > 1:
        left = minterm.pop()
        if len(minterm) == 0:
            break
        right = minterm.pop()
        (net_name, gate_expression) = make_and(left, right)
        minterm.append(net_name)
        gate_expressions.append(gate_expressions)


	minterm_product = gate_expressions[-1]
    return gate_expressions, minterm_product

"""
TODO
. get final result from `build_product`
. get old output
. build xor gate from above
. return new gates and final variable name

minterm_product: string, the gate representing the entire AND tree
---returns---
xor_gates: List[string], the list of additional lines to add to the AAG
new_output: string, the (possibly inverted) gate that replaces the old output
"""
def build_xor(minterm_product):
	print("not implemented")
	

