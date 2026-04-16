import streamlit as st
import pandas as pd
from utils.state_manager import classify_route, save_allocations_to_db

def run_hybrid_qaoa_allocation():
    routes_df = st.session_state.routes.copy()
    routes_df['Difficulty'] = routes_df.apply(classify_route, axis=1)
    drivers_df = st.session_state.drivers.copy()
    
    allocations = []
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
    
    alloc_df = pd.DataFrame(allocations)
    st.session_state.allocations = alloc_df
    
    # Save the generated manifest dynamically into Postgres
    save_allocations_to_db(alloc_df)
