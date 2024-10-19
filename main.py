import re  # import library for regex
import networkx as nx # import networkx for graph data structure
from collections import deque # library needed for queue
from enum import Enum # enumeration to define the possible gate types
from tabulate import tabulate # print the output with a good format
from colorama import Fore, Style, init # print the output with colors
from itertools import chain # to iterate over dictionary


# init colorama
init(autoreset=True)


# Define the gate types enumeration, any gate in bench files has to be declared in this class
class GateType(Enum):
    AND = "and"
    OR = "or"
    NOT = "not"
    NAND = "nand"
    NOR = "nor"
    XOR = "xor"
    XNOR = "xnor"
    BUFF = "buff"
    UNKNOWN = "unknown" # has to be the last one in the list, ALWAYS

# Create a regex pattern from GateType excluding UNKNOWN
gate_types = [gate.value for gate in GateType if gate != GateType.UNKNOWN]
string_r = '|'.join(gate_types)
gate_type_pattern = re.compile(string_r, re.IGNORECASE)

# matching patterns for detecting inputs, outputs, and gates using regex
input_output_pattern = r'^(input|output)\((.+)\)$'
input_pattern = r'^input\(.+\)$'
output_pattern = r'^output\(.+\)$'
gate_pattern = r'^\s*([^\s=]+)\s*=\s*([^\s(]+)\s*\(([^)]*)\)\s*$'


# compute the regex for gate type automatically based on the GateType class definition
gate_type_patter = "r'"
for gate in GateType:
    if gate == GateType.UNKNOWN:
        # removing last '|' and add '
        gate_type_patter = gate_type_patter[:-1]
        gate_type_patter += '\''
    else:
        # adding all the gate types to the regex pattern
        gate_type_patter += gate.name.lower() + '|'


gate_type_patter = re.compile(gate_type_patter, re.IGNORECASE)


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
            gate type (str), input node names (list). It the given line doesn't describe a gate, None is returned instead
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


def get_node_level(levelization_dict, input_nodes):
    """
    Function that given the input nodes of the current gate, checks all the levels and return the level
    as the max{level of input nodes} + 1. If the level is unknown -1 is used
    :param levelization_dict: dictionary that maps the node and its level
    :param input_nodes: list with input nodes
    :return: -1 if at least one input level is unknown, max{level of input nodes} + 1 as level of the current node
    """
    # list that contains the levels for all the fanin nodes
    lvls = []
    # run over input nodes
    for input_node in input_nodes:
        # check if input node is in the levelization dictionary
        if input_node in levelization_dict:
            # add level
            lvls.append(levelization_dict[input_node])
        else:
            # append -1 if the input node is not in the levelization dictionary
            lvls.append(-1)

    if len(lvls) == 0 or min(lvls) < 0:
        # at least one level is unknown
        return -1
    else:
        # return the greatest level among the input nodes + 1
        return max(lvls) + 1


def levelization(graph_circuit, list_input_node, levelization_dict):
    """
    Function that given a graph that models a circuit and the input list, computes the levelization over the circuit.
    :param graph_circuit: graph that models the circuit
    :param list_input_node: input nodes of the circuit
    :param levelization_dict: dictionary that maps the node and its level
    :return: Updated levelization_dict
    """
    # Initialize all nodes to -1 (meaning unprocessed)
    for node in graph_circuit.nodes():
        levelization_dict[node] = -1

    # Set the levels of input nodes to 0
    for node in list_input_node:
        levelization_dict[node] = 0

    # Initialize a queue with the input nodes
    queue = deque(list_input_node)

    # BFS-like process using the queue
    while queue:
        current_node = queue.popleft()  # Get the next node from the queue

        # Iterate over all the successors (outgoing edges) of the current node
        for successor in graph_circuit.successors(current_node):
            # Check the levels of all predecessors of the successor
            predecessor_levels = [levelization_dict[pred] for pred in graph_circuit.predecessors(successor)]

            # Ensure all predecessors have been assigned a level (-1 indicates unprocessed)
            if all(level != -1 for level in predecessor_levels):
                # The level of the successor is the maximum level of its predecessors + 1
                new_level = max(predecessor_levels) + 1

                # If the successor's level has not been set or can be updated
                if levelization_dict[successor] == -1 or new_level > levelization_dict[successor]:
                    # Update the level of the successor
                    levelization_dict[successor] = new_level
                    # Add the successor to the queue for further processing
                    queue.append(successor)

    return levelization_dict


def get_output_gate(inputs, gate_type):
    """
    Function that given a list of input values and the gate type, returns the output
    :param inputs: list of boolean values, representing the input vector of the current gate
    :param gate_type: type of gate defined in GateType class
    :return: boolean value of the output
    """
    # AND gate
    if gate_type == GateType.AND:
        return all(inputs)

    # OR gate
    elif gate_type == GateType.OR:
        return any(inputs)

    # NOT gate (expects a single input)
    elif gate_type == GateType.NOT:
        if len(inputs) != 1:
            raise ValueError("NOT gate expects exactly one input")
        return not inputs[0]

    # NAND gate (AND followed by NOT)
    elif gate_type == GateType.NAND:
        return not all(inputs)

    # NOR gate (OR followed by NOT)
    elif gate_type == GateType.NOR:
        return not any(inputs)

    # XOR gate (True if exactly one input is True)
    elif gate_type == GateType.XOR:
        return inputs.count(True) % 2 == 1

    # XNOR gate (True if an even number of True inputs)
    elif gate_type == GateType.XNOR:
        return inputs.count(True) % 2 == 0

    # BUFF gate (expects a single input, returns it as-is)
    elif gate_type == GateType.BUFF:
        if len(inputs) != 1:
            raise ValueError("BUFF gate expects exactly one input")
        return inputs[0]

    else:
        raise ValueError(f"Unsupported gate type: {gate_type}")


def circuit_parsing(file_name, ret_fault_list=False, ret_levelization_dict=False):
    """
    circuit_parsing is a function in charge of, given a text file that describes a circuit benchmark, modelling the
    circuit with a graph. The directed graph models the input, output and internal nodes with the node set, while
    the wires are modeled with the edges. Inputs are modeled with nodes too, even though they are note gates.
    The node type, that can be either INPUT, OUTPUT, or the gate type, can be get back using the symbol table associated
    to the graph itself.
    :param file_name: name of the file that describes the circuit benchmark
    :param ret_fault_list: flag for computing the full fault list while modelling the circuit as a graph
    :param ret_levelization_dict: flag for computing the levelization of the circuit
    :return: the function returns the graph that models the circuit, the associated symbol table, two lists
             (one for the input and one for the output nodes), the full fault list if the flag ret_fault_list is True
             (None otherwise), and the levelization dictionary if the flag ret_levelization_dict is True (None otherwise)
    """

    # lists for input and output nodes
    list_input_node = []
    list_output_node = []
    # dictionary for the full fault list
    fault_dict = {}
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
                if input not in fault_dict:
                    fault_dict[input] = set()
                fault_dict[input].add(input + "-0")
                fault_dict[input].add(input + "-1")

        # check if it is an output
        elif bool(re.match(output_pattern, line, re.IGNORECASE)):
            output = get_output(line)  # get the output node name
            # adding the node if not inserted yet
            list_output_node.append(output) if output not in list_output_node else None

            # if return fault mode is active
            if ret_fault_list:
                # add faults to fault list
                if output not in fault_dict:
                    fault_dict[output] = set()
                fault_dict[output].add(output + "-OUT-0")
                fault_dict[output].add(output + "-OUT-1")

        # check if it is not empty, or it is a comment
        elif line.strip() and line[0] != '#':
            # get the gate information
            output_node, gate_type, list_inputs = get_gate(line)

            # if return fault mode is active
            if ret_fault_list:
                # add faults to fault list
                if output_node not in fault_dict:
                    fault_dict[output_node] = set()
                fault_dict[output_node].add(output_node + "-0")
                fault_dict[output_node].add(output_node + "-1")

            # update gate type
            symbol_table_nodes[output_node] = gate_type

            # add nodes to graph
            # run over both input and output nodes
            nodes = list_inputs
            nodes.append(output_node)
            for node in nodes:
                # check if node has been already added to the graph
                if node not in graph_circuit.nodes:
                    # add node
                    graph_circuit.add_node(node)
                    # update symbol table with a new node
                    #if node not in list_input_node:
                        #print(gate_type)
                        #symbol_table_nodes[node] = 'GATE'# gate[1]

                    # add node to levelization dictionary
                    if ret_levelization_dict and node not in levelization_dict:
                        # level -1 for those nodes for which the level is unknown
                        levelization_dict[node] = -1

            # add edges to graph
            for input_node in list_inputs:
                # if edge does not exist, create a new directed edge, ingoing into the output node (check auto-loop)
                if not graph_circuit.has_edge(input_node, output_node) and input_node != output_node:
                    graph_circuit.add_edge(input_node, output_node)

                # if return fault mode is active
                if ret_fault_list:
                    # add faults to fault list considering only input of the gate
                    for node_f in list_inputs:
                        if node_f != output_node and node_f + "-" + output_node + "-0" not in list(chain.from_iterable(fault_dict.values())):
                            if node_f not in fault_dict:
                                fault_dict[node_f] = set()
                            fault_dict[output_node].add(output_node + "-" + node_f + "-0")
                            fault_dict[output_node].add(output_node + "-" + node_f + "-1")

    f.close()  # close the file

    # check if a there are straight connections between inputs and outputs
    for input_node in list_input_node:
        if not graph_circuit.has_node(input_node):
            # if the input is not in the graph, means that it has to be added ad both an input
            graph_circuit.add_node(input_node)

    # if levelization flag is active, propagate the input level over the graph
    if ret_levelization_dict:
        # propagate the level of the input over the graph
        levelization(graph_circuit, list_input_node, levelization_dict)

    if ret_fault_list and ret_levelization_dict:
        return graph_circuit, symbol_table_nodes, list_input_node, list_output_node, fault_dict, levelization_dict
    elif ret_fault_list and not ret_levelization_dict:
        return graph_circuit, symbol_table_nodes, list_input_node, list_output_node, fault_dict, None
    elif not ret_fault_list and ret_levelization_dict:
        return graph_circuit, symbol_table_nodes, list_input_node, list_output_node, None, levelization_dict
    else:
        return graph_circuit, symbol_table_nodes, list_input_node, list_output_node, None, None


def simulation(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization, tv, fault_enable=False, fault_value=None):
    """
    Function that given the circuit, its levelization, and an input vector, simulates the circuit behavior and returns
    the output boolean values
    :param graph_circuit: circuit modeled as a directed graph
    :param list_input_node: list of input nodes
    :param list_output_node: list of output nodes
    :param symbol_table_nodes: symbol table nodes, representing the graph
    :param dict_levelization: dictionary that has all the nodes as keys and their levels as values
    :param tv: input test vector
    :param fault_enable: flag that if active makes the simulation sensible to fault value
    :param fault_value: string representing the fault that has to be considered over the simulation
    :return: dictionary that has output pins as keys and their boolean values associated accordingly
    """
    # dictionary that keeps track of the boolean values for each node
    boolean_values = {}

    # run over the inputs
    for i in range(len(list_input_node)):
        # assign boolean values based on the test vector
        boolean_values[list_input_node[i]] = bool(int(tv[i]))

    # check if is needed to set a fault
    if fault_enable:
        # check if fault at the input, output or at the output of a gate
        if len(fault_value.split("-")) == 2 or ( len(fault_value.split("-")) == 3 and fault_value.split("-")[1] == "OUT"):
            # add the fault value
            if fault_value.split("-")[len(fault_value.split("-")) - 1] == "1":
                boolean_values[fault_value.split("-")[0]] = True
            else:
                boolean_values[fault_value.split("-")[0]] = False


    # run over one level at a time
    for i in range(1, max(dict_levelization.values()) + 1):
        # compute for each node of the level the boolean value
        for node in list(filter(lambda key: dict_levelization[key] == i, dict_levelization)):
            # get the gate type
            gate_type = get_gate_type(symbol_table_nodes[node])
            # compute the boolean value
            # check if fault enabled
            if fault_enable:
                # check if a fault occurs at the inputs
                if node == fault_value.split("-")[0] and len(fault_value.split("-")) == 3 and fault_value.split("-")[1] != "OUT":
                    # get the input values
                    inputs = []
                    for input_node in graph_circuit.predecessors(node):
                        # check if it is the faulty input
                        if input_node == fault_value.split("-")[1]:
                            if fault_value.split("-")[len(fault_value.split("-")) - 1] == "1":
                                inputs.append(True)
                            else:
                                inputs.append(False)
                        else:
                            # not the faulty input
                            inputs.append(boolean_values[input_node])

                    # compute the boolean value with the faulty input value
                    out_val = get_output_gate(inputs, gate_type)


                else:
                    # get the input values
                    inputs = []
                    for input_node in graph_circuit.predecessors(node):
                        inputs.append(boolean_values[input_node])
                    # compute the boolean value
                    out_val = get_output_gate(inputs, gate_type)

            else:
                # get the input values
                inputs = []
                for input_node in graph_circuit.predecessors(node):
                    inputs.append(boolean_values[input_node])
                # compute the boolean value
                out_val = get_output_gate(inputs, gate_type)

            # check if fault is enabled
            if fault_enable:
                # check if the output has already computed, if yes means that it is a faulty node
                if node not in boolean_values:
                    # no fault at this point
                    boolean_values[node] = out_val
            else:
                # no fault enabled
                boolean_values[node] = out_val


    # return the output
    out = {}
    for output_node in list_output_node:
        # save output pin and its boolean value in the dictionary
        out[output_node] = str(int(boolean_values[output_node]))

    return out


def get_gate_type(node_type):
    """
    Function that give a string that represents a gate, returns the corresponding gate type
    :param node_type: string
    :return: GateType
    """
    # Regex to search for gate types
    if gate_type_pattern.search(node_type):
        gate_str = gate_type_pattern.search(node_type).group().lower()  # Convert the match to lowercase
        # Return the corresponding gate type from the enumeration
        return GateType[gate_str.upper()]  # Use the uppercase key to access the enum
    else:
        return GateType.UNKNOWN  # If no match, return UNKNOWN


def print_faults(dict_fault_list, bench_name):
    """
    Function that, given a dictionary that contains for each node a list of all its possible faults, prints the full
    fault list
    :param dict_fault_list: dictionary that describes all the faults
    :param bench_name: name of the bench file
    :return:
    """
    print(bench_name + " benchmark has " + str(len(list(chain.from_iterable(dict_fault_list.values())))) + " faults")
    for node in dict_fault_list:
        print("Node " + node + " faults:")
        for fault in sorted(dict_fault_list[node], key=lambda x: (len(x), x)):
            print("    > " + fault)


def print_simulation_result(res, list_input_node, tv):
    """
    Function that, given a dictionary containing the result of a simulation, prints its content.
    :param res: dictionary with simulation results
    :param list_input_node: list of the input nodes
    :param tv: input test vector
    :return: None
    """
    print("-- INPUT --")
    datain = [[Fore.GREEN + str(node) + Style.RESET_ALL for node in list_input_node],
              [Fore.GREEN + str(value) + Style.RESET_ALL for value in tv]]
    print(tabulate(datain, tablefmt="grid"))

    print("-- OUTPUT --")
    dataout = [[Fore.RED + str(key) + Style.RESET_ALL for key in res.keys()],
               [Fore.RED + str(value) + Style.RESET_ALL for value in res.values()]]
    print(tabulate(dataout, tablefmt="grid"))


def menu_get_TV(input_list):
    """
    This function asks for a value (0 or 1) for each input node in the input list and returns a string representing the test vector (TV).

    :param input_list: List of input nodes
    :return: A string representing the test vector (TV) with the input_list order
    """
    tv = ""
    print("Enter the test vector (TV): ")
    for input_node in input_list:
        while True:
            val = input(f"{input_node}: ").strip()
            if val in {"0", "1"}:
                tv += val
                break
            else:
                print("Invalid input. Please enter 0 or 1.")
    return tv


def menu_get_fault(dict_fault):
    """
    This function allows the user to select a fault node from the provided dictionary and then choose a specific fault
    from the list of faults associated with that node. The faults are displayed in order of increasing length and then
    alphabetically. It returns the selected fault as a string.

    :param dict_fault: Dictionary where keys are fault nodes and values are lists of faults
    :return: A string representing the selected fault
    """
    # Display available fault nodes to the user
    print("Available fault nodes:")
    node_list = list(dict_fault.keys())
    for idx, node in enumerate(node_list, start=1):
        print(f"{idx}. {node}")

    # Ask the user to select a node
    node_choice = input("Select a node by number: ").strip()
    while not node_choice.isdigit() or not (1 <= int(node_choice) <= len(node_list)):
        print("Invalid selection. Please choose a valid node number.")
        node_choice = input("Select a node by number: ").strip()

    selected_node = node_list[int(node_choice) - 1]

    # Sort faults by length and then alphabetically
    fault_list = sorted(dict_fault[selected_node], key=lambda x: (len(x), x))

    # Display sorted faults within the selected node
    print(f"Available faults for {selected_node}:")
    for idx, fault in enumerate(fault_list, start=1):
        print(f"{idx}. {fault}")

    # Ask the user to select a specific fault
    fault_choice = input("Select a fault by number: ").strip()
    while not fault_choice.isdigit() or not (1 <= int(fault_choice) <= len(fault_list)):
        print("Invalid selection. Please choose a valid fault number.")
        fault_choice = input("Select a fault by number: ").strip()

    return fault_list[int(fault_choice) - 1]


def fault_sim_menu(input_list, dict_fault):
    """
    Function that prints the menu for the fault simulation and gets the user choice
    :param input_list: list of input nodes
    :param dict_fault: faults of the circuit
    :return:    the choice (1: Any TV any fault, 2: Any TV full fault list),
                the test vector with bits with input_list order, fault selected
    """
    # Ask the user to choose an option
    print("Please choose one of the following options:")
    print("1. Any TV any fault")
    print("2. Any TV full fault list")

    while True:
        # get the user choice
        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            # ask for the TV
            tv = menu_get_TV(input_list)
            fault = menu_get_fault(dict_fault)
            return 1, tv, fault

        elif choice == "2":
            # If the user selects the second option, ask for TV only
            tv = menu_get_TV(input_list)
            return 2, tv, None

        # error
        else:
            print("Invalid input. Please enter 1 or 2.")


def res_cmp(res_no_fault, res_fault):
    """
    Function that given two simulation results, returns if they are different
    :param res_no_fault: result for good circuit
    :param res_fault: result for bad circuit
    :return: True if they differ
    """
    detect = False
    for node in res_no_fault:
        if res_no_fault[node] != res_fault[node]:
            return True

    return detect


def simulation_fault(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization, tv, fault, file_name):
    """
    Function that given a circuit, runs the simulation with a given fault
    :param graph_circuit: model of the circuit
    :param list_input_node: list of input nodes
    :param list_output_node: list of output nodes
    :param symbol_table_nodes: symbol table of the graph that models the circuit
    :param dict_levelization: levelization of the circuit
    :param tv: test vector
    :param fault: fault
    :param file_name: name of the bench file
    :return: if the fault was detected or not and the outcome of the good and bad simulation respectively
    """
    # run simulation without fault
    res_no_fault = simulation(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization,
                              tv)
    # run simulation with fault
    res_fault = simulation(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization, tv,
                           fault_enable=True, fault_value=fault)
    # check if fault detected
    detect = res_cmp(res_no_fault, res_fault)
    # return if it has been detected or not, and the simulation results
    return detect, res_no_fault, res_fault


def init_menu(file_names):
    """
    This function displays a menu to the user with three options:
    1. Fault listing
    2. Circuit simulation
    3. Fault simulation

    After the user selects an option, it asks the user to choose a benchmark from the provided list.
    The selected benchmark's name is stored in a variable called file_name, and the function allows
    space for additional code to be executed based on the user's selection.

    :param file_names: List of available benchmark file names
    :return: None
    """
    # Display the main menu options
    print("Please choose one of the following options:")
    print("1. Fault listing")
    print("2. Circuit simulation")
    print("3. Fault simulation")

    # Get the user's choice
    choice = input("Enter 1, 2, or 3: ").strip()
    while choice not in {"1", "2", "3"}:
        print("Invalid selection. Please choose 1, 2, or 3.")
        choice = input("Enter 1, 2, or 3: ").strip()

    # Display the list of available benchmarks
    print("\nAvailable benchmarks:")
    for idx, name in enumerate(file_names, start=1):
        print(f"{idx}. {name}")

    # Get the user's benchmark selection
    benchmark_choice = input("Select a benchmark by number: ").strip()
    while not benchmark_choice.isdigit() or not (1 <= int(benchmark_choice) <= len(file_names)):
        print("Invalid selection. Please choose a valid benchmark number.")
        benchmark_choice = input("Select a benchmark by number: ").strip()

    # Store the selected benchmark in file_name
    file_name = file_names[int(benchmark_choice) - 1]

    # Placeholder for additional code based on the user's main menu selection
    if choice == "1":
        # Fault list selection
        # parsing the circuit
        graph_circuit, symbol_table_nodes, list_input_node, list_output_node, fault_dict, dict_levelization = circuit_parsing(file_name, True, False)

        # print the number of faults and the full fault list
        print_faults(fault_dict, file_name)

    elif choice == "2":
        # Circuit simulation selection
        # parsing the circuit
        graph_circuit, symbol_table_nodes, list_input_node, list_output_node, fault_dict, dict_levelization = circuit_parsing(file_name, True, True)

        # test vector
        print("=" * 40)
        print(file_name + " simulation")
        tv = "0" * len(list_input_node)
        # run the simulation
        res0 = simulation(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization, tv)
        print_simulation_result(res0, list_input_node, tv)

        tv = "1" * len(list_input_node)
        # run the simulation
        res1 = simulation(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization, tv)
        print_simulation_result(res1, list_input_node, tv)


    elif choice == "3":
        # Fault simulation selection
        # parsing the circuit
        graph_circuit, symbol_table_nodes, list_input_node, list_output_node, fault_dict, dict_levelization = circuit_parsing(file_name, True, True)

        # print the menu and get the user choice for the fault simulation
        choice, tv, fault = fault_sim_menu(list_input_node, fault_dict)
        if choice == 1:
            # Any TV any fault
            # run simulation
            detect, res_no_fault, res_fault = simulation_fault(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization, tv, fault, file_name)
            # print result of fault simulation
            if detect:
                print("In " + file_name + " " + fault + " is detected by TV(" + " ".join(list_input_node) + ") = " + tv)
                print("Output without fault: ")
                print_simulation_result(res_no_fault, list_input_node, tv)
                print("Output with fault: ")
                print_simulation_result(res_fault, list_input_node, tv)
            else:
                print("In " + file_name + " " + fault + " is NOT detected by TV(" + " ".join(
                    list_input_node) + ") = " + tv)
                print("Output without fault: ")
                print_simulation_result(res_no_fault, list_input_node, tv)
                print("Output with fault: ")
                print_simulation_result(res_fault, list_input_node, tv)

        else:
            # Any TV full fault list

            # list of string containing the messages of the result
            res_out = [[], []]  # detected and not detected respectively
            # cnt of total faults
            fault_cnt = 0
            # cnt of detected faults
            det_cnt = 0
            # iterate over all possible faults
            for key in fault_dict:
                for fault in fault_dict[key]:
                    # run simulation
                    detect, res_no_fault, res_fault = simulation_fault(graph_circuit, list_input_node, list_output_node, symbol_table_nodes, dict_levelization, tv, fault, file_name)
                    fault_cnt += 1
                    if detect:
                        # fault detected
                        res_out[0].append("    > " + fault + " fault is detected")
                        # increment number of detected faults
                        det_cnt += 1
                    else:
                        # fault not detected
                        res_out[1].append("    > " + fault + " fault is NOT detected")

            # print result
            print("In " + file_name + ", given the TV(" + " ".join(list_input_node) + ") = " + tv)
            print("# of detected faults: " + str(det_cnt))
            print(f"% of detected faults: {(det_cnt / fault_cnt) * 100:.2f}%")
            print("Detected faults: ")
            for res in res_out[0]:
                print(res)

            print("Not detected faults: ")
            for res in res_out[1]:
                print(res)


def main():
    # bench files
    file_names = ["c17.bench", "c432.bench", "c499.bench", "c880.bench", "c1355.bench", "c1908.bench", "c2670.bench", "c3540.bench", "c5315.bench", "c6288.bench", "c7552.bench", "hw1.bench"]
    # test bench files with known behavior
    file_names_test = ['./my_benches/BM01.bench', './my_benches/BM02.bench', './my_benches/BM03.bench']

    # starting point
    init_menu(file_names_test)


main()
