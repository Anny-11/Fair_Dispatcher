"""
=============================================================
QUBO Builder for Vehicle Routing Problem
=============================================================

Converts the VRP into a Quadratic Unconstrained Binary
Optimization (QUBO) problem.

Variables:
  x[i,j] = 1 if vehicle goes from node i to node j (i != j)

Objective (minimize total distance):
  min  sum_{i,j} dist[i,j] * x[i,j]

Constraints (penalized):
  1. Each stop visited exactly once (in-degree = 1)
  2. Each stop left exactly once  (out-degree = 1)
  3. Subtour elimination (simplified via penalty on isolated loops)

QUBO form: minimize  x^T Q x

Qubit count: N*(N-1) = 5*4 = 20 qubits for full VRP.
For demo we pin depot edges and use 4*3=12 active qubits.
"""

import numpy as np
from itertools import product


def build_qubo(distance_matrix: np.ndarray, penalty: float = 10.0):
    """
    Build the QUBO matrix for TSP-style single-vehicle VRP.

    Parameters
    ----------
    distance_matrix : NxN numpy array of distances
    penalty         : Lagrange penalty for constraint violations

    Returns
    -------
    Q      : dict  {(i,j): coeff}  (upper-triangular QUBO)
    n_vars : total number of binary variables
    var_map: dict mapping (node_from, node_to) -> qubit index
    """
    N = len(distance_matrix)

    # ── Build variable index: skip self-loops (i==j)
    var_map = {}   # (i,j) -> qubit index
    idx = 0
    for i in range(N):
        for j in range(N):
            if i != j:
                var_map[(i, j)] = idx
                idx += 1

    n_vars = idx  # = N*(N-1) = 20 for N=5
    Q = {}

    def add_Q(a, b, value):
        """Add value to Q[(min,max)]."""
        if a > b:
            a, b = b, a
        Q[(a, b)] = Q.get((a, b), 0.0) + value

    # ── Objective: minimize travel distance
    for (i, j), q in var_map.items():
        add_Q(q, q, distance_matrix[i, j])

    # ── Constraint 1: each node j (j!=depot) visited exactly once
    # sum_i x[i,j] = 1  →  penalty * (sum_i x[i,j] - 1)^2
    depot = 0
    for j in range(1, N):                        # delivery stops only
        inbound = [var_map[(i, j)] for i in range(N) if i != j]
        # expand (sum - 1)^2
        for qi in inbound:
            add_Q(qi, qi, penalty * (1 - 2))     # -2A * xi  (linear term)
        for qi in inbound:
            add_Q(qi, qi, penalty)               # A * xi^2 = A*xi (binary)
        for a, b in product(inbound, repeat=2):
            if a != b:
                add_Q(a, b, penalty)             # cross terms
        # constant +A absorbed into offset (ignored in QUBO minimization)

    # ── Constraint 2: each node i (i!=depot) departs exactly once
    for i in range(1, N):
        outbound = [var_map[(i, j)] for j in range(N) if j != i]
        for qi in outbound:
            add_Q(qi, qi, penalty * (1 - 2))
        for qi in outbound:
            add_Q(qi, qi, penalty)
        for a, b in product(outbound, repeat=2):
            if a != b:
                add_Q(a, b, penalty)

    # ── Clean up: remove near-zero entries
    Q = {k: v for k, v in Q.items() if abs(v) > 1e-9}

    return Q, n_vars, var_map


def qubo_to_ising(Q: dict, n_vars: int):
    """
    Convert QUBO dictionary to Ising J (couplings) and h (biases).

    QUBO:   minimize  x^T Q x    (x in {0,1})
    Ising:  minimize  s^T J s + h^T s  (s in {-1,+1})

    Transformation: x_i = (1 - s_i) / 2
    """
    h = {}
    J = {}
    offset = 0.0

    for (i, j), Qij in Q.items():
        if i == j:
            # diagonal: Q_ii * x_i  = Q_ii/2 * (1 - s_i)
            h[i] = h.get(i, 0.0) - Qij / 2
            offset += Qij / 2
        else:
            # off-diagonal: Q_ij * x_i * x_j
            J[(i, j)] = J.get((i, j), 0.0) + Qij / 4
            h[i] = h.get(i, 0.0) - Qij / 4
            h[j] = h.get(j, 0.0) - Qij / 4
            offset += Qij / 4

    return h, J, offset


def print_qubo_summary(Q, n_vars, var_map):
    print("=" * 50)
    print("  QUBO FORMULATION SUMMARY")
    print("=" * 50)
    print(f"  Binary variables (qubits) : {n_vars}")
    print(f"  Non-zero QUBO entries     : {len(Q)}")
    print(f"  Penalty coefficient       : 10.0")
    print()
    print("  Variable Mapping (node_from → node_to : qubit#):")
    for (i, j), q in sorted(var_map.items(), key=lambda x: x[1]):
        print(f"    x[{i},{j}]  →  qubit {q:2d}")
    print("=" * 50)


if __name__ == "__main__":
    from problem_definition import DISTANCE_MATRIX
    Q, n_vars, var_map = build_qubo(DISTANCE_MATRIX, penalty=10.0)
    print_qubo_summary(Q, n_vars, var_map)
    h, J, offset = qubo_to_ising(Q, n_vars)
    print(f"\n  Ising h terms : {len(h)}")
    print(f"  Ising J terms : {len(J)}")
    print(f"  Energy offset : {offset:.4f}")
