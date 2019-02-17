
def gate_to_poly(gate):
    gate_to_poly.poly_num += 1
    if gate.gate.startswith("AND"):
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
sorts a circuit into RTTO
inputs:
    graph - dictionary of Gates. 
        key: output net of gate 
        value: Gate(output, inputs, gate)
    inputs - list of primary input nets of circuit
    outputs - list of primary output nets of circuit
"""
def khan_topo_sort(graph, inputs, outputs):
    """
    get all the nodes with node as an input
    """
    def get_edges(node):
        return filter(lambda edge: node in graph[edge].inputs, graph)

    in_degree = {}

    queue = []
    for node in graph:
        edges = get_edges(node)
        in_degree[node] = len(edges)

    queue = filter(lambda node: len(get_edges(node)) == 0, graph)


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
        self.output = output_net
        self.inputs = input_nets
        self.gate = gate

    def __repr__(self):
        if self.gate == "INPUT":
            return "<%s = INPUT>" % (self.output)
        return "<%s = %s %s %s>" % (self.output, self.inputs[0], self.gate, self.inputs[1])

"""
blif_to_gates
takes in a .blif file and parses it into a dictionary of Gates
file - a .blif representing a circuit

returns:
    gates: a dictionary mapping an output net to a Gate
    primary_inputs: list of Gates representing primary inputs to the circuit
    primary_outputs: list of Gates representing primary outputs to the circuit
"""
def blif_to_gates(blif_file):
    gates = {}
    primary_inputs = []
    primary_outputs = []

    """
    run through test blif_file, generating graph, and gate_list
    """
    line = blif_file.readline()
    while line != "":
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


        line = blif_file.readline()
    return (gates, primary_inputs, primary_outputs)
