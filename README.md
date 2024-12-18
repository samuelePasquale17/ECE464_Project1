# Multi-Fault Simulation

## Overview
This project implements a multi-fault simulation system for test benches using a **directed graph model**. The program supports modeling circuits, generating fault lists, and simulating both fault-free and faulty circuits with improved execution times.

---

## Key Features

### Circuit Modeling
- **Functionality**: The function `circuit_parsing(...)` models a given test bench as a **directed graph**:
  - Nodes represent **inputs**, **outputs**, or **intermediate gates**.
  - Directed edges represent the **connections** (wires) between nodes.
- **Node Classification**:
  - **Inputs**: Nodes with only outgoing edges.
  - **Outputs**: Nodes with only incoming edges.
  - **Intermediate Nodes**: Nodes with both incoming and outgoing edges.

### Fault List Generation
- **Runtime Generation**: The **full fault list** is generated during graph creation to minimize redundant operations.
- **Optimized Data Structure**: A dictionary maps each node to its associated set of faults, enabling:
  - Fast access to a node's fault list.
  - Efficient retrieval of the entire fault list.

### Circuit Simulation
- **Levelization**:
  - Uses a **Breadth-First Search (BFS)** algorithm to assign levels to nodes, starting from inputs (level 0) and progressing to outputs.
  - The result is stored in a dictionary mapping nodes to their levels.
- **Simulation Process**:
  - Input values are assigned to input nodes.
  - Nodes are evaluated level by level, with output values computed based on previous levels.

### Fault Simulation
- **Fault Handling**:
  - During simulation, the program checks for faults at each node.
  - If a fault is detected, the node's value is set to the stuck-at value instead of the computed value.
- **Fault Detection**:
  - Compares the output of the fault-free circuit with the faulty circuit.
  - Any differences indicate a detectable fault.

---

## Implementation Highlights
- **Graph Theory Optimization**:
  - Exploits graph-based algorithms to reduce execution time.
  - Circuit modeling and fault listing are performed during the first file read to avoid redundant processing.
- **Execution Time**:
  - Full fault list generation: ~10 seconds for the largest test bench (`c7552.bench`).
  - Circuit simulation (test vectors: all 0's and all 1's): <11 seconds.
  - Fault simulation (e.g., `node1-SA-0`): A few seconds.

---

## Tools Used
- **Python**: Implementation of graph-based algorithms and simulation.
- **Directed Graphs**: Core data structure for efficient modeling and analysis.

---

## Results
The system demonstrates high efficiency and accuracy in fault simulation:
1. Generates fault lists and simulates large circuits in minimal time.
2. Detects faults effectively by comparing outputs of fault-free and faulty circuits.

---

## Conclusion
This project leverages graph-based techniques to achieve efficient multi-fault simulation. By integrating fault list generation, levelization, and fault detection into a cohesive workflow, the system minimizes execution time while ensuring accurate results for large-scale test benches.
