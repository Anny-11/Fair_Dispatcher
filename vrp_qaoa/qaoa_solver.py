"""
=============================================================
QAOA Solver for VRP  –  using OpenQAOA library
=============================================================

Uses the OpenQAOA library (openqaoa-core + openqaoa-qiskit)
to run the QAOA optimizer on the QUBO problem.

QAOA Circuit:
  - Problem unitary  : e^{-iγ C}   (encodes QUBO cost)
  - Mixer unitary    : e^{-iβ B}   (standard X mixer)
  - Layers (p)       : 2  (tunable)
  - Backend          : qiskit.statevector_simulator  (exact, no noise)

For p=2, N=5 VRP:
  Parameters: 2*p = 4  (γ1,β1,γ2,β2)
  Shots      : 1024
"""

from openqaoa import QAOA
from openqaoa.backends import create_device
from openqaoa.problems import QUBO
import numpy as np


def solve_vrp_with_qaoa(Q: dict, n_vars: int, p: int = 2, shots: int = 1024):
    """
    Solve the VRP QUBO using QAOA via OpenQAOA.

    Parameters
    ----------
    Q       : QUBO dict {(i,j): coeff}
    n_vars  : number of binary variables (= number of qubits)
    p       : number of QAOA layers (depth)
    shots   : number of measurement shots

    Returns
    -------
    result  : OpenQAOA result object with optimal angles + bitstrings
    """
    print(f"\n{'='*55}")
    print(f"  QAOA SOLVER  |  qubits={n_vars}  p={p}  shots={shots}")
    print(f"{'='*55}")

    # ── Step 1: Build OpenQAOA QUBO problem object
    # Convert our sparse dict to the linear_terms + quadratic_terms format
    linear_terms = {}
    quadratic_terms = {}

    for (i, j), coeff in Q.items():
        if i == j:
            linear_terms[i] = linear_terms.get(i, 0.0) + coeff
        else:
            key = (min(i, j), max(i, j))
            quadratic_terms[key] = quadratic_terms.get(key, 0.0) + coeff

    qubo_problem = QUBO(
        n=n_vars,
        terms=list(quadratic_terms.keys()) + [(k,) for k in linear_terms],
        weights=list(quadratic_terms.values()) + list(linear_terms.values()),
    )

    print(f"  QUBO: {n_vars} vars, {len(quadratic_terms)} quadratic, "
          f"{len(linear_terms)} linear terms")

    # ── Step 2: Create QAOA instance
    qaoa = QAOA()

    # ── Step 3: Set classical optimizer
    qaoa.set_classical_optimizer(
        method="cobyla",
        maxiter=200,
        tol=1e-5,
    )

    # ── Step 4: Set circuit properties (p layers, standard X mixer)
    qaoa.set_circuit_properties(
        p=p,
        param_type="standard",
        init_type="ramp",
        mixer_hamiltonian="x",
    )

    # ── Step 5: Choose backend – local statevector simulator (no hardware needed)
    device = create_device(location="local", name="qiskit.statevector_simulator")
    qaoa.set_device(device)

    # ── Step 6: Compile the QAOA circuit onto the problem
    qaoa.compile(qubo_problem)
    print(f"  Circuit compiled successfully.")
    print(f"  Optimizable parameters : {2 * p}  (γ and β for each layer)")

    # ── Step 7: Run the optimization
    print(f"\n  Running COBYLA optimizer (max 200 iterations)...")
    qaoa.optimize()

    result = qaoa.result
    print(f"\n  ✅ Optimization complete!")
    print(f"  Best energy found : {result.optimized['cost']:.6f}")
    print(f"  Optimal angles    : {result.optimized['angles']}")

    return result


def decode_result(result, var_map: dict, distance_matrix: np.ndarray):
    """
    Decode the QAOA bitstring result into actual vehicle routes.

    Parameters
    ----------
    result          : OpenQAOA result object
    var_map         : dict (node_from, node_to) -> qubit_index
    distance_matrix : NxN distance array

    Returns
    -------
    best_route      : list of edges [(i,j), ...] in the solution
    total_distance  : float, total route distance
    """
    print(f"\n{'='*55}")
    print(f"  DECODING RESULT")
    print(f"{'='*55}")

    # Get the most-sampled bitstring
    best_bitstring = result.most_probable_states["solutions_bitstrings"][0]
    print(f"  Best bitstring : {best_bitstring}")

    # Reverse var_map: qubit_index -> (from_node, to_node)
    idx_to_edge = {v: k for k, v in var_map.items()}

    # Extract active edges
    active_edges = []
    for qubit_idx, bit in enumerate(best_bitstring):
        if bit == "1" and qubit_idx in idx_to_edge:
            edge = idx_to_edge[qubit_idx]
            active_edges.append(edge)

    print(f"  Active edges   : {active_edges}")

    # Calculate total distance for active edges
    total_dist = sum(distance_matrix[i][j] for i, j in active_edges)
    print(f"  Total distance : {total_dist:.2f} km")

    return active_edges, total_dist


def print_route(active_edges, locations: dict, total_dist: float):
    """Pretty-print the decoded route."""
    print(f"\n{'='*55}")
    print(f"  OPTIMAL ROUTE FOUND BY QAOA")
    print(f"{'='*55}")
    if not active_edges:
        print("  ⚠  No valid route decoded from bitstring.")
        return

    for i, j in active_edges:
        from_name = locations[i]["name"]
        to_name   = locations[j]["name"]
        print(f"  {from_name}  →  {to_name}")

    print(f"\n  Total Travel Distance : {total_dist:.2f} km")
    print(f"{'='*55}")
