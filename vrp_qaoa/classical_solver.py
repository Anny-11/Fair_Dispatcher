"""
=============================================================
Classical Baseline Solver for VRP  (Nearest Neighbor Greedy)
=============================================================
Used to compare against QAOA results.
"""

import numpy as np
import itertools


def nearest_neighbor_route(distance_matrix: np.ndarray, start: int = 0):
    """
    Greedy nearest-neighbor heuristic for TSP-style VRP.
    Always picks the closest unvisited node.
    Returns: route (list of nodes), total_distance (float)
    """
    N = len(distance_matrix)
    unvisited = set(range(N)) - {start}
    route = [start]
    total_dist = 0.0
    current = start

    while unvisited:
        next_node = min(unvisited, key=lambda j: distance_matrix[current][j])
        total_dist += distance_matrix[current][next_node]
        route.append(next_node)
        unvisited.remove(next_node)
        current = next_node

    # Return to depot
    total_dist += distance_matrix[current][start]
    route.append(start)
    return route, total_dist


def brute_force_optimal(distance_matrix: np.ndarray):
    """
    Brute force exact solution (only feasible for N <= 8).
    Returns: best_route, best_distance
    """
    N = len(distance_matrix)
    stops = list(range(1, N))   # exclude depot (node 0)
    best_dist = float("inf")
    best_perm = None

    for perm in itertools.permutations(stops):
        route = [0] + list(perm) + [0]
        dist = sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
        if dist < best_dist:
            best_dist = dist
            best_perm = route

    return best_perm, best_dist


def print_classical_results(distance_matrix, locations):
    print(f"\n{'='*55}")
    print(f"  CLASSICAL BASELINE COMPARISON")
    print(f"{'='*55}")

    nn_route, nn_dist = nearest_neighbor_route(distance_matrix, start=0)
    bf_route, bf_dist = brute_force_optimal(distance_matrix)

    print(f"\n  [Greedy Nearest Neighbor]")
    route_names = [locations[n]["name"].split("–")[-1].strip() for n in nn_route]
    print(f"  Route    : {' → '.join(route_names)}")
    print(f"  Distance : {nn_dist:.2f} km")

    print(f"\n  [Brute-Force Optimal]")
    route_names = [locations[n]["name"].split("–")[-1].strip() for n in bf_route]
    print(f"  Route    : {' → '.join(route_names)}")
    print(f"  Distance : {bf_dist:.2f} km")

    return nn_dist, bf_dist
