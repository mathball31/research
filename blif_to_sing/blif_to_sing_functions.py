import re

"""
checks if gate is an AND gate of on AND gate and XOR gate with the same inputs
"""
def is_AND_AND_XOR(gate, gate_dict):
    input0 = gate_dict[gate.inputs[0]]
    input1 = gate_dict[gate.inputs[1]]

    #check that gates have same inputs
    same_inputs = set(input0.inputs) == set(input1.inputs)
    if not same_inputs:
        return False

    #check that one input gate is XOR
    one_XOR = (input0.gate.startswith("XOR") and input1.gate.startswith("XOR"))
    if not one_XOR:
        return False

    #check that one input gate is AND
    one_AND = (input0.gate.startswith("AND") and input1.gate.startswith("AND"))
    if not one_AND:
        return False

    return True

"""
gets all pairs of AND and XOR gates with the same inputs
"""
def get_AND_XOR_pairs(gates):
    ands = filter(lambda gate: gates[gate].gate.startswith("AND"), gates)
    xors = filter(lambda gate: gates[gate].gate.startswith("XOR"), gates)

    pairs = []
    for and_gate in ands:
        for xor_gate in filter(lambda gate: set(gates[gate].inputs) == set(gates[and_gate].inputs), xors):
            pairs.append((and_gate, xor_gate))

    return pairs

    


def gate_to_poly(gate, gate_dict = None):
    gate_to_poly.poly_num += 1
    if gate.gate.startswith("AND"):
        #check for (a AND b) AND (a XOR b)
        if isinstance(gate_dict, dict) and is_AND_AND_XOR(gate, gate_dict):
            # replace with zero
            print("Found AND_AND_XOR: %d" % (gate_to_poly.poly_num))
            return "poly f%d = -%s + 0;\n" % (gate_to_poly.poly_num, gate.output)
        return "poly f%d = -%s + %s*%s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0], gate.inputs[1])

    if gate.gate == "NOTA AND B":
        return "poly f%d = -%s + (1 - %s)*%s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0], gate.inputs[1])

    if gate.gate == "NOTA NAND B":
        return "poly f%d = -%s + 1 - (1 - %s)*%s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0], gate.inputs[1])

    if gate.gate == "NAND":
        return "poly f%d = -%s + 1 - %s*%s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0], gate.inputs[1])

    if gate.gate.startswith("OR"):
        return "poly f%d = -%s + %s + %s - %s*%s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0], gate.inputs[1], gate.inputs[0], gate.inputs[1])

    if gate.gate.startswith("XOR"):
        return "poly f%d = -%s + %s + %s - 2*%s*%s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0], gate.inputs[1], gate.inputs[0], gate.inputs[1])

    if gate.gate == "XNOR":
        return "poly f%d = -%s + 1 - %s - %s + 2*%s*%s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0], gate.inputs[1], gate.inputs[0], gate.inputs[1])

    if gate.gate == "INPUT":
        #don't increment on primary inputs
        gate_to_poly.poly_num -= 1
        return "poly f%s = %s^2 - %s;\n" % (gate.output, gate.output, gate.output)
    if gate.gate.startswith("INV"):
        return "poly f%d = -%s + 1 - %s;\n" % (gate_to_poly.poly_num, gate.output, gate.inputs[0])
    return str(gate) + "\n"

gate_to_poly.poly_num = -1


"""
input: '\n' seperated string of strings representing truth table
output: string with name of gate
"""
def blif_name_to_gate(truth_table):
    entries = truth_table.split("\n");
    if truth_table == "11 1\n":
        return "AND"
    if truth_table == "00 0\n":
        return "NAND"
    if truth_table == "01 1\n":
        return "NOTA AND B"
    if truth_table == "01 0\n":
        return "NOTA NAND B"
    if "01 1" in truth_table and "10 1" in truth_table:
        if "11 1" in truth_table:
            return "OR"
        else:
            return "XOR"
    if "00 1" in truth_table and "11 1" in truth_table:
        return "XNOR"
    

    print("gate")
    print(truth_table)
    return ""

"""
get all the nodes with node as an input
"""
def get_output_edges(node, graph):
    return filter(lambda edge: node in graph[edge].inputs, graph)

"""
sorts a circuit into RTTO
inputs:
    graph - dictionary of Gates. 
        key: output net of gate 
        value: Gate(output, inputs, gate)
    inputs - list of primary input nets of circuit
    outputs - list of primary output nets of circuit
"""
def khan_topo_sort(graph, inputs, outputs):

    in_degree = {}

    queue = []
    for node in graph:
        edges = get_output_edges(node, graph)
        in_degree[node] = len(edges)

    queue = filter(lambda node: len(get_output_edges(node, graph)) == 0, graph)


    cnt = 0
    order = []
    
    while queue:
        node = queue.pop()
        order.append(graph[node])
        
        edges = graph[node].inputs
        for edge in edges:
            in_degree[edge] -= 1
            if in_degree[edge] == 0:
                queue.append(edge)


        cnt += 1

    if cnt != len(graph):
        print("Cycle in graph")

    order.reverse()

    #pull out primary outputs and sort
    output_gates = filter(lambda node: node.output in outputs, order)
    order = filter(lambda node: node.output not in outputs, order)
    #rejoin and reverse
    output_gates.sort(key = lambda node: node.output, reverse = True)
    order += output_gates
    order.reverse()
    #pull out primary inputs and sort
    input_gates = filter(lambda node: node.output in inputs, order)
    input_gates.sort(key = lambda node: node.output)
    order = filter(lambda node: node.output not in inputs, order)
    #rejoin
    order += input_gates
    return order

    
"""
sorts a circuit into RTTO
inputs:
    graph - dictionary of Gates. 
        key: output net of gate 
        value: Gate(output_net, input_nets, gate)
    inputs - list of primary input nets of circuit
    outputs - list of primary output nets of circuit
"""
def dfs_topo_sort(graph, inputs, outputs):
    order = []
    color = {node: "white" for node in graph}
    found_cycle = [False]
    for node in graph:
        if color[node] == "white":
            dfs_visit(graph, node, color, order, found_cycle)
        if found_cycle[0]:
            break

    if found_cycle[0]:
        order = []

    #pull out primary outputs and sort
    output_gates = filter(lambda node: node.output in outputs, order)
    order = filter(lambda node: node.output not in outputs, order)
    #rejoin and reverse
    output_gates.sort(key = lambda node: node.output, reverse = True)
    order += output_gates
    order.reverse()
    #pull out primary inputs and sort
    input_gates = filter(lambda node: node.output in inputs, order)
    input_gates.sort(key = lambda node: node.output)
    order = filter(lambda node: node.output not in inputs, order)
    #rejoin
    order += input_gates
    return order

"""
recursive helper for dfs_topo_sort
"""
def dfs_visit(graph, node, color, order, found_cycle):
    if found_cycle[0]:
        return
    
    color[node] = "grey"

    for in_node in graph[node].inputs:
        if color[in_node] == "grey":
            found_cycle[0] == True
            return
        if color[in_node] == "white":
            dfs_visit(graph, in_node, color, order, found_cycle)

    color[node] = "black"
    order.append(graph[node])
    return

class Gate:
    def __init__(self, output_net, input_nets, gate):
        self.output = output_net # string
        self.inputs = input_nets # list of strings
        self.gate = gate # string

    def __repr__(self):
        if self.gate == "INPUT":
            return "<%s = INPUT>" % (self.output)
        if len(self.inputs) == 1:
            return "<%s = %s %s>" % (self.output, self.inputs[0], self.gate)
        return "<%s = %s %s %s>" % (self.output, self.inputs[0], self.gate, self.inputs[1])


"""
This sorts the circuit column wise doing merging and promotion of gates as necessary

inputs:
    graph - dictionary of Gates. 
        key: output net of gate 
        value: Gate(output_net, input_nets, gate)
    inputs - list of primary input nets of circuit
    outputs - list of primary output nets of circuit
        NOTE: assumes outputs sorted LSB->MSB
"""
def daniela_sort(graph, inputs, outputs):
    #get normal rtto sort
    pre_order = khan_topo_sort(graph, inputs, outputs)
    print("pre_order: " + str(pre_order))
    print(len(pre_order))

    

    #build input cones
    input_cones = [] #list[set[Gate]]
    for output in outputs:
        #cone = graph[output].inputs
        cone = [output]
        idx = 0
        #recursively iterate through inputs
        while idx < len(cone):
            cone.extend(graph[cone[idx]].inputs)
            idx += 1


        input_cones.append(set(cone))

    print(input_cones)
    print("\n\n\n")

    #build slices. Each slice is difference of cones
    slices = [None]*len(input_cones) #list[set[Gate]]
    slices[0] = input_cones[0]
    for idx, cone in enumerate(input_cones[1:], 1):
        slices[idx] = input_cones[idx] - input_cones[idx - 1]

    print(slices)

    #merge
    #TODO: check that this works
    idx = len(slices) - 1
    #I want to go backwards, but keep the indexes normal. idk a good pythonic way to do this.
    while idx >= 0:
        stack = list(slices[idx])
        while stack:
            gate = stack.pop(0)
            # If both gate inputs are in lower slices, move to lower slice.
            # Because we go backwards, this gate will be pushed down each iteration
            # until it can't go any lower
            if all(input_net in input_cones[idx - 1] for input_net in graph[gate].inputs):
                slices[idx].remove(gate)
                slices[idx - 1].add(gate)
                #check parent(s)
                stack.extend(get_output_edges(gate, graph))

        idx -= 1

    #promote
    #TODO

    order = []
    for ckt_slice in slices:
        #print(ckt_slice)
        slice_order = filter(lambda node: node.output in ckt_slice, pre_order)
        #print("post_slice sub_order: " + str(slice_order))
        order.extend(slice_order)


    #TODO make this a function and use it in other circuits
    #pull out primary outputs and sort
    output_gates = filter(lambda node: node.output in outputs, order)
    order = filter(lambda node: node.output not in outputs, order)
    #rejoin and reverse
    output_gates.sort(key = lambda node: node.output, reverse = True)
    order += output_gates
    order.reverse()
    #pull out primary inputs and sort
    input_gates = filter(lambda node: node.output in inputs, order)
    input_gates.sort(key = lambda node: node.output)
    order = filter(lambda node: node.output not in inputs, order)
    #rejoin
    order += input_gates
    print("final order: " + str(order))
    print(len(order))
    if set(order) != set(pre_order):
        print("WARNING: order is missing gates!!")
        print(set(pre_order) - set(order))
    return order
        


"""
badchars
    this is a regex expression containing the characters that might be in a blif, 
    but shouldn't be in the singular file
"""
badchars = r'[\[\]]'

"""
blif_to_gates
takes in a .blif file and parses it into a dictionary of Gates
file - a .blif representing a circuit

returns:
    gates: a dictionary mapping an output net to a Gate
    primary_inputs: list of Gates representing primary inputs to the circuit
    primary_outputs: list of Gates representing primary outputs to the circuit
"""
#TODO add constant declaration
def blif_to_gates(blif_file):
    gates = {}
    primary_inputs = []
    primary_outputs = []

    """
    run through test blif_file, generating graph, and gate_list
    """
    line = blif_file.readline()
    while line != "":
        extendLine = line.rstrip()[-1] == '\\'
        line = re.sub(badchars, '_', line)
        if extendLine:
            line = line.replace('\\', '')
        if line.startswith(".gate"):
            tokens = line.split();
            gate_inputs = []
            gate_output = ""
            for token in tokens:
                if token.startswith('Y='):
                    gate_output = token[2:]
                if token.startswith('A=') or token.startswith('B='):
                    gate_inputs.append(token[2:])
            gates[gate_output] = Gate(gate_output, gate_inputs, tokens[1])

        if line.startswith(".names"):
            gate_inputs = line.split()[1:-1]
            gate_output = line.split()[-1]

            line = source_blif_file.readline()
            truth_table = ""
            while not line.startswith("."):
                truth_table += line
                line = source_blif_file.readline()

            gates[gate_output] = Gate(gate_output, gate_inputs, blif_name_to_gate(truth_table))

            continue

        if line.startswith(".inputs"):
            primary_inputs.extend(line.split()[1:])
        if line.startswith(".outputs"):
            primary_outputs.extend(line.split()[1:])

        if extendLine:
            line = line.split()[0] + blif_file.readline()
        else: 
            line = blif_file.readline()
    return (gates, primary_inputs, primary_outputs)
