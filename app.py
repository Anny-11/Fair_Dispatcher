import streamlit as st
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

# Page config
st.set_page_config(page_title="Fair Dispatcher System", layout="wide", initial_sidebar_state="expanded")

# CSS: Clean, Professional, High-Contrast SaaS Theme (Minimalist)
def inject_custom_css():
    st.markdown("""
        <style>
        body { color: #1e293b; font-family: 'Inter', sans-serif; background-color: #f8fafc !important; }
        .stApp { background-color: #f8fafc; }
        h1, h2, h3, h4, h5, h6, p, div { color: #0f172a !important; }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #334155 !important; }
        div[data-testid="metric-container"] { background: #ffffff; border-radius: 6px; padding: 15px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02); }
        div[data-testid="metric-container"] label { color: #64748b !important; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px;}
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #4f46e5 !important; font-weight: 700; }
        .streamlit-expanderHeader { background-color: #f1f5f9 !important; color: #1e293b !important; border-radius: 4px; font-weight: 600; }
        .stButton>button { background-color: #4f46e5; color: white !important; border: none; border-radius: 4px; padding: 0.5rem 1rem; font-weight: 500; transition: all 0.2s ease; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .stButton>button:hover { background-color: #4338ca; transform: translateY(-1px); box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2); }
        .logout-btn button { background-color: #ef4444 !important; }
        .logout-btn button:hover { background-color: #dc2626 !important; }
        .approve-btn button { background-color: #10b981 !important; }
        .approve-btn button:hover { background-color: #059669 !important; }
        .deny-btn button { background-color: #f59e0b !important; }
        .deny-btn button:hover { background-color: #d97706 !important; }
        .action-button button { margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

# Persistent State Management
def initialize_state():
    if 'role' not in st.session_state: st.session_state.role = None
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'token_requests' not in st.session_state: st.session_state.token_requests = []

    if 'drivers' not in st.session_state:
        st.session_state.drivers = pd.DataFrame({
            "Driver_ID": ["D1", "D2", "D3", "D4"],
            "Name": ["Alice", "Bob", "Charlie", "David"],
            "Past_Workload": [120, 95, 110, 85], 
            "Fatigue_Score": [0.8, 0.4, 0.6, 0.2],
            "Monthly_Tokens": [4, 5, 2, 5],
            "Wage_History": [1200, 950, 1100, 850],
            "Vehicle_Capacity_kg": [300, 100, 400, 200]
        })
    if 'routes' not in st.session_state:
        st.session_state.routes = pd.DataFrame({
            "Route_ID": ["R1", "R2", "R3", "R4"],
            "Deliveries": [45, 12, 60, 25],
            "Weight_kg": [200, 50, 300, 100],
            "Urgency": ["Normal", "Emergency", "Normal", "Medical"],
            "Traffic": ["High", "Low", "Medium", "Low"],
            "Distance_km": [40, 15, 60, 20]
        })

# Core Logic
def classify_route(row):
    score = sum([
        2 if row['Deliveries'] > 40 else 1 if row['Deliveries'] > 20 else 0,
        2 if row['Weight_kg'] > 150 else 0,
        2 if row['Traffic'] == 'High' else 0,
        3 if row['Urgency'] in ['Emergency', 'Medical'] else 0
    ])
    return "HIGH" if score >= 5 else "MEDIUM" if score >= 3 else "LOW"

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
    
    st.session_state.allocations = pd.DataFrame(allocations)
    st.session_state.token_requests = [] # Reset token requests on fresh allocation

def style_difficulty(val):
    colors = {'HIGH': '#ef4444', 'MEDIUM': '#f59e0b', 'LOW': '#10b981', 'Pending': '#3b82f6'}
    return f'color: {colors.get(val, "gray")}; font-weight: bold;'


def login_screen():
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem; color: #4f46e5 !important; font-weight: 600;'>System Login</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown("#### Select Identity")
        role_choice = st.radio("Access Level", ["Administrator", "Driver"])
        
        if role_choice == "Driver":
            driver_names = st.session_state.drivers['Name'].tolist()
            selected_driver = st.selectbox("Select Driver Profile", driver_names)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Authenticate", use_container_width=True):
            st.session_state.role = role_choice
            st.session_state.current_user = "Admin" if role_choice == "Administrator" else selected_driver
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def admin_dashboard():
    st.sidebar.markdown('---')
    st.sidebar.markdown("**Module Navigation**")
    
    modules = [
        "Admin Control Center", 
        "Intelligence & Memory",
        "Quantum Optimization",
        "Token Approvals"
    ]
    
    pending_count = len([req for req in st.session_state.token_requests if req['status'] == 'Pending'])
    if pending_count > 0:
        modules[3] = f"Token Approvals ({pending_count})"

    selection = st.sidebar.radio("View Module", modules, label_visibility="collapsed")

    if selection == "Admin Control Center":
        st.markdown("### Admin Control Center")
        st.markdown("<p style='color: #64748b; font-size: 0.95rem;'>Update operational day-wise data for Routes and Drivers.</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Active Routes Database")
            st.session_state.routes = st.data_editor(st.session_state.routes, num_rows="dynamic", use_container_width=True)
        with col2:
            st.markdown("##### Driver Workforce Database")
            st.session_state.drivers = st.data_editor(st.session_state.drivers, num_rows="dynamic", use_container_width=True)

    elif selection == "Intelligence & Memory":
        st.markdown("### Intelligence & Memory")
        st.markdown("<p style='color: #64748b; font-size: 0.95rem;'>Historical workload analysis and automated route classifications.</p>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("##### Route Difficulty Matrix")
            routes_df = st.session_state.routes.copy()
            routes_df['Difficulty'] = routes_df.apply(classify_route, axis=1)
            st.dataframe(routes_df.style.applymap(style_difficulty, subset=['Difficulty']), use_container_width=True)
            
        with col2:
            st.markdown("##### Workload Distribution")
            chart_data = st.session_state.drivers.set_index("Name")[["Past_Workload", "Wage_History"]]
            st.bar_chart(chart_data)

    elif selection == "Quantum Optimization":
        st.markdown("### Quantum Optimization Center")
        col1, col2 = st.columns([1, 2], gap="large")
        with col1:
            st.markdown("##### Execution Engine")
            st.markdown("<p style='color: #475569; font-size: 0.9rem;'>Trigger QAOA Hamiltonian optimization to generate optimal routing manifest.</p>", unsafe_allow_html=True)
            if st.button("Execute QAOA Optimizer", use_container_width=True):
                with st.spinner("Applying Hamiltonian Constraints..."):
                    time.sleep(1)
                    run_hybrid_qaoa_allocation()
                    st.success("Allocation Processed Successfully.")

            if 'allocations' in st.session_state:
                st.markdown("<br>##### Current Dispatch Manifest", unsafe_allow_html=True)
                st.dataframe(st.session_state.allocations.style.applymap(style_difficulty, subset=['Difficulty']), use_container_width=True)

        with col2:
            st.markdown("##### Qiskit Circuit Topology")
            plt.style.use("default")
            qubits_to_show = min(4, len(st.session_state.drivers))
            qc = QuantumCircuit(qubits_to_show)
            qc.h(range(qubits_to_show))
            qc.barrier()
            gamma, beta = Parameter('gamma'), Parameter('beta')
            for i in range(qubits_to_show - 1):
                qc.cx(i, i+1)
                qc.rz(gamma, i+1)
                qc.cx(i, i+1)
            qc.barrier()
            for i in range(qubits_to_show): qc.rx(beta, i)
            qc.measure_all()
            
            fig, ax = plt.subplots(figsize=(8, 3))
            fig.patch.set_facecolor('#ffffff')
            qc.draw(output='mpl', ax=ax, style={'backgroundcolor': '#ffffff', 'textcolor':'#1e293b'})
            st.pyplot(fig)

    elif selection.startswith("Token Approvals"):
        st.markdown("### Inter-System Token Requests")
        if len(st.session_state.token_requests) == 0:
            st.info("No pending requests logged in the system.")
        else:
            for idx, req in enumerate(st.session_state.token_requests):
                with st.expander(f"Case ID {idx+100}: {req['driver']} (Status: {req['status']})", expanded=(req['status'] == 'Pending')):
                    colInfo, colAction = st.columns(2)
                    with colInfo:
                        st.write(f"**Assigned Task:** {req['current_route']} ({req['difficulty']})")
                        st.write(f"**Filed Reason:** {req['reason']}")
                    
                    if req['status'] == 'Pending':
                        with colAction:
                            st.markdown("<div class='approve-btn action-button'>", unsafe_allow_html=True)
                            if st.button("Approve & Reassign", key=f"app_{idx}", use_container_width=True):
                                st.session_state.drivers.loc[st.session_state.drivers['Name'] == req['driver'], 'Monthly_Tokens'] -= 1
                                idx_alloc = st.session_state.allocations.index[st.session_state.allocations['Route_ID'] == req['current_route']].tolist()[0]
                                st.session_state.allocations.at[idx_alloc, 'Route_ID'] = "R_RELIEF_01"
                                st.session_state.allocations.at[idx_alloc, 'Difficulty'] = "LOW"
                                st.session_state.allocations.at[idx_alloc, 'Est_Wage ($)'] = 50
                                st.session_state.token_requests[idx]['status'] = 'Approved'
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            st.markdown("<div class='deny-btn action-button'>", unsafe_allow_html=True)
                            if st.button("Deny Request", key=f"den_{idx}", use_container_width=True):
                                st.session_state.token_requests[idx]['status'] = 'Denied'
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

def driver_dashboard():
    st.markdown(f"### Dispatch Portal: {st.session_state.current_user}")
    st.markdown("<p style='color: #64748b; font-size: 0.95rem;'>View your daily scheduled task and manage flexibility tokens.</p>", unsafe_allow_html=True)
    
    if 'allocations' in st.session_state:
        driver_sel = st.session_state.current_user
        driver_data = st.session_state.drivers[st.session_state.drivers['Name'] == driver_sel].iloc[0]
        alloc_data_subset = st.session_state.allocations[st.session_state.allocations['Driver'] == driver_sel]
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Fatigue Index", f"{driver_data['Fatigue_Score']}")
        c2.metric("Tokens Remaining", f"{driver_data['Monthly_Tokens']}")
        c3.metric("Historical Load", f"{driver_data['Past_Workload']}")
        
        st.divider()
        
        if not alloc_data_subset.empty:
            assigned_route = alloc_data_subset.iloc[0]['Route_ID']
            assigned_diff = alloc_data_subset.iloc[0]['Difficulty']
            
            pending_reqs = [r for r in st.session_state.token_requests if r['driver'] == driver_sel and r['status'] == 'Pending']
            approved_reqs = [r for r in st.session_state.token_requests if r['driver'] == driver_sel and r['status'] == 'Approved']
            denied_reqs = [r for r in st.session_state.token_requests if r['driver'] == driver_sel and r['status'] == 'Denied']
            
            if len(pending_reqs) > 0:
                st.info("System Status: Awaiting Administrator Validation. Your token exchange request is under review.")
                st.markdown(f"**Pending Route Lock:** {assigned_route} ({assigned_diff})")
            else:
                if len(approved_reqs) > 0:
                    st.success("Notification: Administration has approved your token usage and downgraded your task difficulty.")
                elif len(denied_reqs) > 0:
                    st.error("Notification: Token request denied by administration. Original dispatch logic maintained.")
                    
                st.markdown(f"#### Daily Assignment: Route {assigned_route}")
                st.markdown(f"**Difficulty Classification:** {assigned_diff}")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if assigned_diff == "HIGH":
                    st.warning("🔥 **Surge Alert:** Completing this High-Difficulty route will earn you +1 Flexibility Token!")

                colA, colB = st.columns([1, 2])
                with colA:
                    if st.button("Acknowledge Assignment", use_container_width=True):
                        if assigned_diff == "HIGH":
                            idx = st.session_state.drivers.index[st.session_state.drivers['Name'] == driver_sel].tolist()[0]
                            st.session_state.drivers.at[idx, 'Monthly_Tokens'] += 1
                            st.success("Assignment Confirmed! +1 Token Earned.")
                        else:
                            st.success("Assignment Confirmed!")
                with colB:
                    st.markdown("<div class='deny-btn action-button' style='margin-top: 0px;'>", unsafe_allow_html=True)
                    if st.button("Initiate Token Exchange", use_container_width=True):
                        if driver_data['Monthly_Tokens'] > 0:
                            if assigned_diff in ['HIGH', 'MEDIUM']:
                                st.session_state.requesting_token = True
                            else:
                                st.warning("Notice: You are currently scheduled for the minimum available task difficulty.")
                        else:
                            st.error("Protocol Error: Insufficient tokens remaining on account.")
                    st.markdown("</div>", unsafe_allow_html=True)
                            
                if st.session_state.get('requesting_token', False):
                    st.markdown("<div style='background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 20px;'>", unsafe_allow_html=True)
                    st.markdown("##### Token Exchange Filing Form")
                    reason = st.text_area("Provide justification (e.g., Illness, physical fatigue limits):")
                    st.markdown("<div class='approve-btn action-button'>", unsafe_allow_html=True)
                    if st.button("Submit to Dispatch"):
                        st.session_state.token_requests.append({
                            "driver": driver_sel,
                            "current_route": assigned_route,
                            "difficulty": assigned_diff,
                            "reason": reason,
                            "status": "Pending"
                        })
                        st.session_state.requesting_token = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No tasks have been scheduled for your profile today.")
    else:
        st.warning("The global optimization engine has not been executed by Dispatch today.")

def main():
    initialize_state()
    inject_custom_css()

    if st.session_state.role is None:
        login_screen()
    else:
        st.sidebar.markdown(f"<div style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<span style='font-size: 1.1rem; font-weight: 600; color: #1e293b;'>Fair Dispatcher System</span>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<span style='color: #475569;'>Session: {st.session_state.current_user}</span>", unsafe_allow_html=True)
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.role == "Administrator":
            admin_dashboard()
        elif st.session_state.role == "Driver":
            driver_dashboard()
            
        st.sidebar.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
        st.sidebar.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
        if st.sidebar.button("Terminate Session", use_container_width=True):
            st.session_state.role = None
            st.session_state.current_user = None
            st.session_state.requesting_token = False
            st.rerun()
        st.sidebar.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
