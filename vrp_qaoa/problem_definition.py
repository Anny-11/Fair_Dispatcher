"""
=============================================================
VRP Problem Definition
=============================================================
Defines the Vehicle Routing Problem (VRP) dataset.

Problem Size:
  - Locations : 1 depot + 4 delivery stops = 5 nodes
  - Vehicles  : 2
  - Qubits    : ~20 (4 positions × 5 nodes = 20 binary vars)
  - QUBO vars : 20 binary decision variables

Dataset is synthetic but realistic for a small Indian city cluster.
"""

import numpy as np

# ─────────────────────────────────────────────
# 1. LOCATION DATA
# ─────────────────────────────────────────────
# Node 0 = Depot (Warehouse)
# Nodes 1-4 = Delivery stops
LOCATIONS = {
    0: {"name": "Depot (Warehouse)",    "coords": (11.0168, 76.9558)},  # Coimbatore central
    1: {"name": "Stop A – RS Puram",    "coords": (11.0082, 76.9494)},
    2: {"name": "Stop B – Gandhipuram", "coords": (11.0178, 76.9674)},
    3: {"name": "Stop C – Peelamedu",   "coords": (11.0272, 77.0000)},
    4: {"name": "Stop D – Saravanampatti", "coords": (11.0662, 77.0218)},
}

NUM_NODES    = len(LOCATIONS)   # 5
NUM_VEHICLES = 2
VEHICLE_CAPACITY = 15           # max demand units per vehicle

# Demand at each node (depot = 0)
DEMANDS = {
    0: 0,   # depot
    1: 4,
    2: 6,
    3: 5,
    4: 7,
}

# ─────────────────────────────────────────────
# 2. DISTANCE MATRIX  (km, symmetric)
# ─────────────────────────────────────────────
# Derived from approximate real distances between the coords above.
DISTANCE_MATRIX = np.array([
    [0.0,  1.2,  2.1,  4.3,  8.5],   # Depot
    [1.2,  0.0,  1.5,  3.8,  7.9],   # A
    [2.1,  1.5,  0.0,  2.6,  7.1],   # B
    [4.3,  3.8,  2.6,  0.0,  5.0],   # C
    [8.5,  7.9,  7.1,  5.0,  0.0],   # D
], dtype=float)

# ─────────────────────────────────────────────
# 3. QUBO SIZING SUMMARY
# ─────────────────────────────────────────────
"""
Binary variable: x[i,j] = 1 if vehicle travels edge i→j

For a TSP-style VRP on N=5 nodes, 2 vehicles:
  Variables per vehicle = N*(N-1) = 5*4 = 20
  Total variables       = 40 (but we simplify to single-vehicle QAOA demo)

For our QAOA demo (single vehicle, 4 stops + depot):
  Variables = N^2 = 25  →  ~16 meaningful binary vars (excluding self-loops)
  Qubits required ≈ 16–20

This is well within simulator capacity (up to ~25 qubits on laptop).
"""

def get_problem_summary():
    print("=" * 55)
    print("  VEHICLE ROUTING PROBLEM – PROJECT OVERVIEW")
    print("=" * 55)
    print(f"  Nodes          : {NUM_NODES}  (1 depot + 4 delivery stops)")
    print(f"  Vehicles       : {NUM_VEHICLES}")
    print(f"  Vehicle Cap.   : {VEHICLE_CAPACITY} units")
    print(f"  Total Demand   : {sum(DEMANDS.values())} units")
    print()
    print("  QUANTUM SIZING:")
    print(f"  Binary vars    : {NUM_NODES**2} (x[i,j] for all i,j)")
    print(f"  Useful vars    : ~{NUM_NODES*(NUM_NODES-1)} (no self-loops)")
    print(f"  Qubits needed  : ~16–20  (simulator-safe)")
    print(f"  QAOA layers(p) : 2–4  (higher p = better approximation)")
    print()
    print("  Distance Matrix (km):")
    header = "       " + "  ".join([f"N{i}" for i in range(NUM_NODES)])
    print(header)
    for i in range(NUM_NODES):
        row = f"  N{i}  " + "  ".join([f"{DISTANCE_MATRIX[i,j]:4.1f}" for j in range(NUM_NODES)])
        print(row)
    print("=" * 55)

if __name__ == "__main__":
    get_problem_summary()
