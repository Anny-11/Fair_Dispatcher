import streamlit as st
import pandas as pd
from utils.state_manager import classify_route

def run_hybrid_qaoa_allocation():
    routes_df = st.session_state.routes.copy()
    routes_df['Difficulty'] = routes_df.apply(classify_route, axis=1)
    drivers_df = st.session_state.drivers.copy()
    
    allocations = []
    # Real logic: build QUBO, run QAOA, but here we process the hybrid mock 
    available_drivers = drivers_df.sort_values(by="Past_Workload").to_dict('records')
    
    for _, r in routes_df.iterrows():
        capable_drivers = [drv for drv in available_drivers if drv['Vehicle_Capacity_kg'] >= r['Weight_kg']]
        if capable_drivers:
            d = capable_drivers[0]
            available_drivers.remove(d)
            wage = 100 if r['Difficulty'] == 'HIGH' else 70 if r['Difficulty'] == 'MEDIUM' else 40
            allocations.append({
                "Driver": d['Name'],
                "Route_ID": r['Route_ID'],
                "Urgency": r['Urgency'],
                "Difficulty": r['Difficulty'],
                "Est_Wage ($)": wage
            })
            available_drivers.append(d)
        else:
            allocations.append({
                "Driver": "UNASSIGNED (No Vehicle Cap)",
                "Route_ID": r['Route_ID'],
                "Urgency": r['Urgency'],
                "Difficulty": r['Difficulty'],
                "Est_Wage ($)": 0
            })
    
    st.session_state.allocations = pd.DataFrame(allocations)
    st.session_state.token_requests = [] # Reset token requests on fresh allocation
