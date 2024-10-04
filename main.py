import re  # import library for regex


# matching patterns for detecting inputs, outputs, and gates using regex
input_output_pattern = r'^(input|output)\((.+)\)$'
input_pattern = r'^input\(.+\)$'
output_pattern = r'^output\(.+\)$'
gate_pattern = r'^\s*([^\s=]+)\s*=\s*([^\s(]+)\s*\(([^)]*)\)\s*$'


def get_gate(line):
    """
    get_gate is a function in charge of, given a string that describes a gate, extracting some information
    about the output pin name, the gate type and the input pin names that feed the gate.

    :param line: String that should have the following format: out_pin_name = GATE_TYPE(input_pin_name1, ...)
    :return get_gate returns three information about the gate with the following order: output pin name (str),
            gete type (str), input pin names (list). It the given line doesn't describe a gate, None is returned instead
    """

    # Regex match verification
    match = re.search(gate_pattern, line)

    # Check if match occurs
    if match:
        output_pin = match.group(1)  # getting the output pin name
        gate_name = match.group(2)  # getting the gate name
        list_inputs = match.group(3)  # getting the inputs string
        list_inputs = [element.strip() for element in list_inputs.split(',')] # generation of a list with all the inputs
        fanin = len(list_inputs)  # number of inputs
        if fanin > 1:
            gate_type = str(fanin) + "-input " + gate_name.upper()  # update the gate type with the number of inputs
        else:
            gate_type = gate_name.upper() # no changes

        # return the gate information
        return output_pin, gate_type, list_inputs
    else:
        # if NO match occurs
        return None, None, None


def get_input(line):
    """
    get_input is a function in charge of, given a line (str) as input, checking if it describes an either an input or an
    output, and return the pin name
    :param line: string with the following format: INPUT(pin_name) or OUTPUT(pin_name)
    :return: get_input returns the pin name if a match is found, None otherwise
    """

    # check if it is an INPUT or an OUTPUT (not Case Sensitive)
    match = re.search(input_output_pattern, line, re.IGNORECASE)

    # check is match occurs
    if match:
        return match.group(2)  # return the pin name
    else:
        return None  # None if no match


def get_output(line):
    """
    get_output is a wrapper that simply calls get_input. This is needed just for user interface purposes. In fact the
    user can call that function to get the output pin without know what's happening behind the scene. As we know the
    pattern for both inputs and outputs is almost the same, except for the word itself (either input or output)
    :param line:
    :return:
    """

    return get_input(line)  # return the output pin name


def circuit_parsing(file_name, list_input_node, list_output_node, list_gates):
    """
    circuit_parsing is a function in charge of, given a text file that describes a circuit benchmark, parsing the
    circuit, extracting some information
    :param file_name: name of the file that describes the circuit benchmark
    :param list_input_node: list with all the input nodes
    :param list_output_node: list with all the output nodes
    :param list_gates: list with all the gates, with their main characteristics (output pin, gate type, input pins)
    :return:
    """

    f = open(file_name, "r")  # open the file

    for line in f.readlines():  # read each line

        # check if it is an input
        if bool(re.match(input_pattern, line, re.IGNORECASE)):
            input = get_input(line)  # get the input pin name
            # adding the pin if not inserted yet
            list_input_node.append(input) if input not in list_input_node else None
        # check if it is an output
        elif bool(re.match(output_pattern, line, re.IGNORECASE)):
            output = get_output(line)  # get the output pin name
            # adding the pin if not inserted yet
            list_output_node.append(output) if output not in list_output_node else None
        # check if it not empty or it is a comment
        elif line.strip() and line[0] != '#':
            # get the gate
            gate = get_gate(line)
            list_gates.append(gate) if gate not in list_gates else None


    f.close()  # close the file


def circuit_levelization(list_input_node, list_output_node, list_gates, dict_lev_node):
    # add all the input nodes
    for input in list_input_node:
        # check if the input node has already been added as key in the dictionary
        if input not in dict_lev_node:
            # add input node as key and initialize lvl to 0
            dict_lev_node[input] = 0

    # add all the output nodes
    for output in list_output_node:
        # check if the output node has already been added as key in the dictionary
        if output not in dict_lev_node:
            # add output node as key and initialize lvl to inf (-1 value)
            dict_lev_node[output] = -1

    # add all the remaining internal nodes
    for gate in list_gates:
        # get the output node
        node = gate[0]
        # check if the node has already been added as key in the dictionary
        if node not in dict_lev_node:
            # add node as key and initializa lvl to inf (-1 value)
            dict_lev_node[node] = -1

    # flag for loop detection
    loopDetect = False
    # flag to detect when all nodes get a lvl
    end = False
    # counter of the number of output pins with a level assigned
    cntOutLvl = 0
    # levelization
    while not loopDetect and not end:
        # check if loops occur
        lvlUpdated = 0
        # scan all gates
        for gate in list_gates:
            # check if all inputs get a lvl
            flagInput = True
            # input levels
            lvls = []
            for input in gate[2]:
                # check if input has a lvl
                if dict_lev_node[input] == -1:
                    # lvl is still inf
                    flagInput = False
                else:
                    # save temporary the level
                    lvls.append(dict_lev_node[input])

            # check input flag, if true all inputs have a lvl
            if flagInput:
                # check if the node is an output node and has not a lvl yet
                if gate[0] in list_output_node and dict_lev_node[gate[0]] == -1:
                    cntOutLvl += 1

                # assign the level to the output
                dict_lev_node[gate[0]] = max(lvls) + 1
                # increment counter of nodes that get a lvl on the ongoing gate loop
                lvlUpdated += 1

            # check if all outputs get a level (terminal condition)
            if cntOutLvl >= len(list_output_node):
                # all outputs get a level
                end = True
                # exit gate for loop
                break

        # check if any node has been updated with a lvl
        if lvlUpdated == 0:
            # no updates, loop detected (terminal condition)
            loopDetect = True

    # check if loop has been detected
    if loopDetect:
        # print error message
        print("Loop detected!")
        # erase the dictionary
        dict_lev_node.clear()

    # return if the levelization is correct or not valid due to a loop
    return not loopDetect


def main():
    # file_name = "benchmark1.txt"
    # file_name = "benchmark2.txt"
    # file_name = "benchmark3.txt"
    file_name = "hw1.bench"
    # file_name = "c17.bench"
    list_input_node = []
    list_output_node = []
    list_gates = []
    dict_lev_node = {}

    # parsing the circuit
    circuit_parsing(file_name, list_input_node, list_output_node, list_gates)

    # levelization of the circuit
    ret = circuit_levelization(list_input_node, list_output_node, list_gates, dict_lev_node)

    # print levelization result
    if ret:
        for lvl in sorted((set(dict_lev_node.values()))):
            print("=== Level ", lvl, " ===")
            for node in dict_lev_node.keys():
                if dict_lev_node[node] == lvl:
                    print(node, end=' ')
            print()


main()