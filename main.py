import re  # import library for regex
import networkx as nx # import networkx for graph data structure


# matching patterns for detecting inputs, outputs, and gates using regex
input_output_pattern = r'^(input|output)\((.+)\)$'
input_pattern = r'^input\(.+\)$'
output_pattern = r'^output\(.+\)$'
gate_pattern = r'^\s*([^\s=]+)\s*=\s*([^\s(]+)\s*\(([^)]*)\)\s*$'


def get_input(line):
    """
    get_input is a function in charge of, given a line (str) as input, checking if it describes an either an input or an
    output, and return the node name
    :param line: string with the following format: INPUT(node_name) or OUTPUT(node_name)
    :return: get_input returns the node name if a match is found, None otherwise
    """
    # check if it is an INPUT or an OUTPUT (not Case Sensitive)
    match = re.search(input_output_pattern, line, re.IGNORECASE)

    # check is match occurs
    if match:
        return match.group(2)  # return the node name
    else:
        return None  # None if no match


def get_output(line):
    """
    get_output is a wrapper that simply calls get_input. This is needed just for user interface purposes. In fact the
    user can call that function to get the output node without know what's happening behind the scene. As we know the
    pattern for both inputs and outputs is almost the same, except for the word itself (either input or output)
    :param line:
    :return:
    """
    return get_input(line)  # return the output node name


def get_gate(line):
    """
    get_gate is a function in charge of, given a string that describes a gate, extracting some information
    about the output node name, the gate type and the input node names that feed the gate.

    :param line: String that should have the following format: out_node_name = GATE_TYPE(input_node_name1, ...)
    :return get_gate returns three information about the gate with the following order: output node name (str),
            gete type (str), input node names (list). It the given line doesn't describe a gate, None is returned instead
    """
    # Regex match verification
    match = re.search(gate_pattern, line)

    # Check if match occurs
    if match:
        output_node = match.group(1)  # getting the output node name
        gate_name = match.group(2)  # getting the gate name
        list_inputs = match.group(3)  # getting the inputs string
        list_inputs = [element.strip() for element in list_inputs.split(',')] # generation of a list with all the inputs
        fanin = len(list_inputs)  # number of inputs
        if fanin > 1:
            gate_type = str(fanin) + "-input " + gate_name.upper()  # update the gate type with the number of inputs
        else:
            gate_type = gate_name.upper() # no changes

        # return the gate information
        return output_node, gate_type, list_inputs
    else:
        # if NO match occurs
        return None, None, None


def circuit_parsing(file_name, ret_fault_list=False, ret_levelization_dict=False):
    """
    circuit_parsing is a function in charge of, given a text file that describes a circuit benchmark, modelling the
    circuit with a graph. The directed graph models the input, output and internal nodes with the node set, while
    the wires are modeled with the edges. Inputs are modeled with nodes too, even though they are note gates.
    The node type, that can be either INPUT, OUTPUT, or the gate type, can be get back using the symbol table associated
    to the graph itself.
    :param file_name: name of the file that describes the circuit benchmark
    :param ret_fault_list: flag for computing the full fault list while modelling the circuit as a graph
    :return: the function returns the graph that models the circuit, the associated symbol table, two lists
             (one for the input and one for the output nodes), and the full fault list if the flag ret_fault_list is True
             (None otherwise)
    """

    # lists for input and output nodes
    list_input_node = []
    list_output_node = []
    # dictionary for the full fault list
    fault_list_dict = {}
    # dictionary for the levelization
    levelization_dict = {}
    # Directed Graph for circuit modelling
    graph_circuit = nx.DiGraph()
    # Symbol table to map each node and its type (can be either INPUT, OUTPUT, or the gate type)
    symbol_table_nodes = {}

    f = open(file_name, "r")  # open the file

    for line in f.readlines():  # read each line
        # check if it is an input
        if bool(re.match(input_pattern, line, re.IGNORECASE)):
            input = get_input(line)  # get the input node name
            # adding the node if not inserted yet
            list_input_node.append(input) if input not in list_input_node else None
            # update symbol table with INPUT type for the current node
            symbol_table_nodes[input] = 'INPUT'
            # if return fault mode is active
            if ret_fault_list:
                # add faults to fault list
                fault_list_dict[input] = [input + "-0", input + "-1"]

        # check if it is an output
        elif bool(re.match(output_pattern, line, re.IGNORECASE)):
            output = get_output(line)  # get the output node name
            # adding the node if not inserted yet
            list_output_node.append(output) if output not in list_output_node else None

            # if return fault mode is active
            if ret_fault_list:
                # add faults to fault list
                fault_list_dict[output + "-OUT"] = [output + "-OUT-0", output + "-OUT-1"]


        # check if it is not empty, or it is a comment
        elif line.strip() and line[0] != '#':
            # get the gate
            gate = get_gate(line)

            # if return fault mode is active
            if ret_fault_list:
                # add faults to fault list
                fault_list_dict[gate[0] + ":" + gate[1]] = []
                fault_list_dict[gate[0] + ":" + gate[1]].append(gate[0] + "-0")
                fault_list_dict[gate[0] + ":" + gate[1]].append(gate[0] + "-1")


            # add nodes to graph
            nodes = gate[2] # add input nodes
            nodes.append(gate[0]) # add output node
            # run over both input and output nodes
            for node in nodes:
                # check if node has been already added to the graph
                if node not in graph_circuit.nodes:
                    # add node
                    graph_circuit.add_node(node)
                    # check if node is already in the symbol table (check needed for input nodes)
                    if node not in symbol_table_nodes:
                        # update symbol table with a new node
                        symbol_table_nodes[node] = gate[1]

            # add edges to graph
            for input_node in gate[2][:-1]:
                # if edge does not exist, create a new directed edge, ingoing into the output node
                if not graph_circuit.has_edge(input_node, gate[0]): graph_circuit.add_edge(input_node, gate[0])

                # if return fault mode is active
                if ret_fault_list:
                    # add faults to fault list
                    fault_list_dict[gate[0] + ":" + gate[1]].append(gate[0] + "-" + input_node + "-0")
                    fault_list_dict[gate[0] + ":" + gate[1]].append(gate[0] + "-" + input_node + "-1")

    f.close()  # close the file

    # if return fault mode is active
    if ret_fault_list:
        # return dictionary with the full fault list
        return graph_circuit, symbol_table_nodes, list_input_node, list_output_node, fault_list_dict
    else:
        # full fault list not returned
        return graph_circuit, symbol_table_nodes, list_input_node, list_output_node, None


def print_faults(dict_fault_list):
    """
    Function that, given a dictionary that contains for each node a list of all its possible faults, prints the full
    fault list
    :param dict_fault_list: dictionary that describes the fault list
    :return:
    """
    # run over all the keys
    for key in dict_fault_list.keys():
        print(key + " faults:")
        # print all the faults
        for val in dict_fault_list[key]:
            print("    " + val)


def main():
    # bench files
    file_names = ["c17.bench", "c432.bench", "c499.bench", "c880.bench", "c1355.bench", "c1908.bench", "c2670.bench",
                  "c3540.bench", "c5315.bench", "c6288.bench", "c7552.bench", "hw1.bench"]

    # select one bench file
    file_name = "mio.bench" #file_names[len(file_names) - 1]

    # parsing the circuit, return full fault list enabled
    graph_circuit, symbol_table_nodes, list_input_node, list_output_node, dict_fault_list = circuit_parsing(file_name, True)

    # print the number of faults and the full fault list
    print(file_name + " #Faults = " + str(len([item for sublist in dict_fault_list.values() for item in sublist])))
    # print the full fault list
    print_faults(dict_fault_list)


    # levelization
    # add levelization flag to circuit_parsing
    #print(nx.shortest_path_length(graph_circuit, source='a', target='y'))

main()
