import streamlit as st
import pandas as pd
from utils.state_manager import classify_route, save_allocations_to_db

def _classical_solve(routes_df, drivers_df):
    """Greedy classical baseline: sort by urgency+difficulty, assign lowest-workload capable driver."""
    routes = routes_df.copy()
    routes['Difficulty'] = routes.apply(classify_route, axis=1)
    urgency_order = {'Emergency': 0, 'Medical': 1, 'Normal': 2}
    diff_order    = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    routes['_u'] = routes['Urgency'].map(urgency_order).fillna(3)
    routes['_d'] = routes['Difficulty'].map(diff_order).fillna(3)
    routes = routes.sort_values(['_u', '_d']).reset_index(drop=True)

    drivers = drivers_df.copy().sort_values('Past_Workload').reset_index(drop=True)
    assignments = []
    assigned_drivers = set()

    for _, r in routes.iterrows():
        best = None
        for _, d in drivers.iterrows():
            if d['Name'] in assigned_drivers:
                continue
            if d['Vehicle_Capacity_kg'] >= r['Weight_kg']:
                best = d
                break
        if best is not None:
            assigned_drivers.add(best['Name'])
            wage = 100 if r['Difficulty'] == 'HIGH' else 70 if r['Difficulty'] == 'MEDIUM' else 40
            assignments.append({
                "Driver": best['Name'],
                "Route_ID": r['Route_ID'],
                "Urgency": r['Urgency'],
                "Difficulty": r['Difficulty'],
                "Est_Wage ($)": wage
            })
        else:
            assignments.append({
                "Driver": "UNASSIGNED",
                "Route_ID": r['Route_ID'],
                "Urgency": r['Urgency'],
                "Difficulty": r['Difficulty'],
                "Est_Wage ($)": 0
            })

    return pd.DataFrame(assignments)

def _qaoa_solve(routes_df, drivers_df):
    """QAOA-inspired allocation: weights fatigue + capacity + urgency jointly (hybrid mock)."""
    routes = routes_df.copy()
    routes['Difficulty'] = routes.apply(classify_route, axis=1)

    diff_weight    = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    urgency_weight = {'Emergency': 3, 'Medical': 2, 'Normal': 1}

    assignments = []
    available = drivers_df.copy().to_dict('records')

    # Sort routes by combined quantum cost weight (most constrained first)
    routes['_cost'] = (
        routes['Difficulty'].map(diff_weight).fillna(1) +
        routes['Urgency'].map(urgency_weight).fillna(1) +
        routes['Weight_kg'] / routes['Weight_kg'].max()
    )
    routes = routes.sort_values('_cost', ascending=False).reset_index(drop=True)

    for _, r in routes.iterrows():
        # QAOA scoring: pick driver that minimises combined fatigue + workload imbalance
        best, best_score = None, float('inf')
        for d in available:
            if d['Vehicle_Capacity_kg'] < r['Weight_kg']:
                continue
            # Lower is better: high fatigue & high workload → high cost
            score = (d['Fatigue_Score'] * 0.6) + (d['Past_Workload'] / 200.0 * 0.4)
            if score < best_score:
                best_score = score
                best = d

        if best is not None:
            available.remove(best)
            wage = 100 if r['Difficulty'] == 'HIGH' else 70 if r['Difficulty'] == 'MEDIUM' else 40
            assignments.append({
                "Driver": best['Name'],
                "Route_ID": r['Route_ID'],
                "Urgency": r['Urgency'],
                "Difficulty": r['Difficulty'],
                "Est_Wage ($)": wage,
                "Fatigue_Cost": round(best_score, 3)
            })
            available.append(best)   # Driver can handle multiple routes in real fleet
        else:
            assignments.append({
                "Driver": "UNASSIGNED",
                "Route_ID": r['Route_ID'],
                "Urgency": r['Urgency'],
                "Difficulty": r['Difficulty'],
                "Est_Wage ($)": 0,
                "Fatigue_Cost": 999
            })

    return pd.DataFrame(assignments)

def compute_fairness_score(alloc_df, drivers_df):
    """Standard deviation of wage distribution — lower = more equitable."""
    if alloc_df is None or alloc_df.empty:
        return 999.0
    driver_wages = alloc_df.groupby('Driver')['Est_Wage ($)'].sum()
    return round(float(driver_wages.std()), 2)

def run_hybrid_qaoa_allocation():
    routes_df  = st.session_state.routes.copy()
    drivers_df = st.session_state.drivers.copy()

    classical_df = _classical_solve(routes_df, drivers_df)
    qaoa_df      = _qaoa_solve(routes_df, drivers_df)

    classical_score = compute_fairness_score(classical_df, drivers_df)
    qaoa_score      = compute_fairness_score(qaoa_df, drivers_df)

    # QAOA approximation ratio — lower std-dev means more fair
    approx_ratio = round(classical_score / qaoa_score, 3) if qaoa_score > 0 else 1.0

    # Clean manifest (drop internal column)
    manifest_df = qaoa_df.drop(columns=['Fatigue_Cost'], errors='ignore')
    st.session_state.allocations      = manifest_df
    st.session_state.classical_alloc  = classical_df.drop(columns=['Fatigue_Cost'], errors='ignore')
    st.session_state.classical_score  = classical_score
    st.session_state.qaoa_score       = qaoa_score
    st.session_state.approx_ratio     = approx_ratio

    save_allocations_to_db(manifest_df)
