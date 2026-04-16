import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import time

import plotly.graph_objects as go
from utils.state_manager import (inject_css, style_difficulty, classify_route,
                                  kpi_card, badge, section_header, card,
                                  save_drivers_to_db, save_routes_to_db, load_data_to_session)
from utils.quantum_solver import run_hybrid_qaoa_allocation, compute_fairness_score
from utils.database import add_route_to_db, add_driver_to_db, delete_route_from_db

st.set_page_config(page_title="Admin · Fair Dispatcher", page_icon="FD", layout="wide")

if not st.session_state.get('authenticated') or st.session_state.get('role') != "Administrator":
    st.switch_page("app.py")

inject_css()

# ════════════════ SIDEBAR ════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 16px 0;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
            <div style="width:28px;height:28px;background:linear-gradient(135deg,#4f46e5,#818cf8);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;color:white;">FD</div>
            <span style="font-size:1rem;font-weight:800;color:#f1f5f9;letter-spacing:-.02em;">Fair Dispatcher</span>
        </div>
        <div style="font-size:.7rem;color:#334155;text-transform:uppercase;letter-spacing:.08em;padding-left:36px;margin-bottom:20px;">Admin Console</div>
    </div>
    <div style="height:1px;background:#1c2038;margin:0 16px 16px;"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin:0 8px 16px;background:#13172a;border:1px solid #1c2038;border-radius:10px;padding:14px 16px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f46e5,#818cf8);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:.9rem;flex-shrink:0;">
                {st.session_state.current_user[0].upper()}
            </div>
            <div>
                <div style="font-size:.875rem;font-weight:600;color:#e2e8f0;">{st.session_state.current_user}</div>
                <div style="font-size:.7rem;color:#34d399;margin-top:1px;">Administrator</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True):
        for k in ['authenticated', 'role', 'current_user']:
            st.session_state[k] = None
        st.session_state.authenticated = False
        st.switch_page("app.py")

# ════════════════ TOP KPIs ════════════════
st.markdown('<div style="padding:28px 0 8px;">', unsafe_allow_html=True)
st.markdown(section_header("Dispatch Operations Center",
            "Real-time fleet intelligence and QAOA-powered route optimization."), unsafe_allow_html=True)

drivers_df = st.session_state.get('drivers', None)
routes_df  = st.session_state.get('routes', None)
alloc_df   = st.session_state.get('allocations', None)

n_drivers   = len(drivers_df) if drivers_df is not None else 0
n_routes    = len(routes_df)  if routes_df  is not None else 0
n_alloc     = len(alloc_df)   if alloc_df is not None and not alloc_df.empty else 0
avg_fatigue = round(drivers_df['Fatigue_Score'].mean(), 2) if drivers_df is not None and n_drivers > 0 else "—"

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1: st.markdown(kpi_card("Active Drivers",  n_drivers,   "Fleet size",       "#6366f1"), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("Open Routes",     n_routes,    "Pending dispatch",  "#818cf8"), unsafe_allow_html=True)
with c3: st.markdown(kpi_card("Manifested",      n_alloc,     "QAOA assignments",  "#34d399"), unsafe_allow_html=True)
with c4: st.markdown(kpi_card("Avg Fatigue",     avg_fatigue, "Fleet health index","#fbbf24"), unsafe_allow_html=True)

st.markdown("</div><div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("---")

# ════════════════ TABS ════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "Fleet Operations",
    "Analytics",
    "Quantum Engine",
    "Token Governance"
])

# ── TAB 1: FLEET ──
with tab1:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Quick Add Route ──
    st.markdown(section_header("Add New Route",
                "Define a new delivery route and it will immediately be available for QAOA optimization."), unsafe_allow_html=True)

    with st.form("add_route_form", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            new_rid   = st.text_input("Route ID", placeholder="e.g. R11")
            new_deliv = st.number_input("Deliveries", min_value=1, value=20)
        with fc2:
            new_wkg   = st.number_input("Weight (kg)", min_value=1, value=100)
            new_dist  = st.number_input("Distance (km)", min_value=1, value=30)
        with fc3:
            new_urg   = st.selectbox("Urgency", ["Normal", "Emergency", "Medical"])
            new_traf  = st.selectbox("Traffic", ["Low", "Medium", "High"])
        route_submitted = st.form_submit_button("Add Route", use_container_width=True)

    if route_submitted:
        if not new_rid.strip():
            st.error("Route ID cannot be empty.")
        else:
            ok, msg = add_route_to_db(new_rid.strip(), new_deliv, new_wkg, new_urg, new_traf, new_dist)
            if ok:
                load_data_to_session()
                st.success(f"Route {new_rid} added. Run the QAOA optimizer to include it in the manifest.")
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")

    # ── Current Routes Table ──
    st.markdown(section_header("Routes Registry",
                "Edit existing routes. Click Save after making changes."), unsafe_allow_html=True)

    edited_routes = st.data_editor(
        st.session_state.routes, num_rows="dynamic", use_container_width=True,
        column_config={
            "Route_ID":     st.column_config.TextColumn("Route ID", width="small"),
            "Deliveries":   st.column_config.NumberColumn("Deliveries", min_value=0),
            "Weight_kg":    st.column_config.NumberColumn("Weight (kg)", min_value=0),
            "Distance_km":  st.column_config.NumberColumn("Distance (km)", min_value=0),
            "Urgency":      st.column_config.SelectboxColumn("Urgency", options=["Normal","Emergency","Medical"]),
            "Traffic":      st.column_config.SelectboxColumn("Traffic",  options=["Low","Medium","High"]),
        }
    )
    col_save, col_del, _ = st.columns([1, 1, 2])
    with col_save:
        if st.button("Save Route Edits", use_container_width=True):
            save_routes_to_db(edited_routes)
            st.session_state.routes = edited_routes
            st.success("Changes saved to NeonDB.")
    with col_del:
        del_rid = st.text_input("Delete Route ID", placeholder="e.g. R10", label_visibility="collapsed")
        if st.button("Delete Route", use_container_width=True):
            if del_rid.strip():
                delete_route_from_db(del_rid.strip())
                load_data_to_session()
                st.success(f"Route {del_rid} deleted.")
                st.rerun()

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Quick Add Driver ──
    st.markdown(section_header("Register New Driver",
                "Onboard a new driver into the system. They will receive login access immediately."), unsafe_allow_html=True)

    with st.form("add_driver_form", clear_on_submit=True):
        fd1, fd2, fd3 = st.columns(3)
        with fd1:
            new_did   = st.text_input("Driver ID", placeholder="e.g. D7")
            new_dname = st.text_input("Name", placeholder="e.g. Grace")
        with fd2:
            new_dusr  = st.text_input("Login Username", placeholder="e.g. grace")
            new_dpwd  = st.text_input("Initial Password", type="password")
        with fd3:
            new_dcap  = st.number_input("Vehicle Capacity (kg)", min_value=50, value=200)
            new_dfat  = st.slider("Fatigue Score", 0.0, 1.0, 0.3, 0.05)
            new_dtok  = st.number_input("Starting Tokens", min_value=0, value=5)
        driver_submitted = st.form_submit_button("Register Driver", use_container_width=True)

    if driver_submitted:
        if not new_did.strip() or not new_dname.strip() or not new_dusr.strip() or not new_dpwd:
            st.error("All driver fields are required.")
        else:
            ok, msg = add_driver_to_db(new_did.strip(), new_dname.strip(), new_dusr.strip(),
                                       new_dpwd, new_dcap, new_dfat, new_dtok)
            if ok:
                load_data_to_session()
                st.success(f"Driver {new_dname} registered. They can now sign in.")
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    st.markdown(section_header("Driver Directory",
                "Edit driver fatigue, capacity, and token balance."), unsafe_allow_html=True)

    edited_drivers = st.data_editor(
        st.session_state.drivers, num_rows="fixed", use_container_width=True,
        column_config={
            "Driver_ID":          st.column_config.TextColumn("ID", width="small"),
            "Fatigue_Score":      st.column_config.NumberColumn("Fatigue (0-1)", min_value=0.0, max_value=1.0, format="%.2f"),
            "Monthly_Tokens":     st.column_config.NumberColumn("Tokens", min_value=0),
            "Vehicle_Capacity_kg": st.column_config.NumberColumn("Vehicle Cap (kg)", min_value=0),
        }
    )
    col_save2, _ = st.columns([1, 3])
    with col_save2:
        if st.button("Save Driver Edits", use_container_width=True):
            save_drivers_to_db(edited_drivers)
            st.session_state.drivers = edited_drivers
            st.success("Driver records updated in NeonDB.")

# ── TAB 2: ANALYTICS ──
with tab2:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Fleet Intelligence",
                "Route difficulty breakdown and driver fatigue correlation."), unsafe_allow_html=True)

    with st.expander("Route Difficulty Classification Matrix", expanded=True):
        routes_display = st.session_state.routes.copy()
        routes_display['Difficulty'] = routes_display.apply(classify_route, axis=1)
        st.dataframe(
            routes_display.style.map(style_difficulty, subset=['Difficulty']),
            use_container_width=True
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    with st.expander("Fatigue vs. Workload Correlation", expanded=True):
        if drivers_df is not None and not drivers_df.empty:
            fig = px.scatter(
                drivers_df, x="Past_Workload", y="Fatigue_Score",
                size="Monthly_Tokens", color="Name", hover_name="Name",
                template="plotly_dark",
                color_discrete_sequence=["#818cf8","#34d399","#fbbf24","#f87171","#a78bfa"],
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8')),
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(gridcolor='#1c2038', title="Past Workload (hrs)", title_font=dict(color='#64748b')),
                yaxis=dict(gridcolor='#1c2038', title="Fatigue Score",       title_font=dict(color='#64748b')),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No driver data available.")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if drivers_df is not None and not drivers_df.empty:
        with st.expander("Token Wallet Distribution", expanded=False):
            fig2 = px.bar(
                drivers_df, x="Name", y="Monthly_Tokens",
                color="Monthly_Tokens", template="plotly_dark",
                color_continuous_scale=["#1c2038","#4f46e5","#818cf8"],
                labels={"Monthly_Tokens": "Tokens"},
            )
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(gridcolor='#1c2038'),
                yaxis=dict(gridcolor='#1c2038'),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

# ── TAB 3: QUANTUM ENGINE ──
with tab3:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("QAOA Quantum Routing Engine",
                "Run the optimizer on your current fleet data and compare quantum vs classical assignment strategies."), unsafe_allow_html=True)

    col_run, col_info = st.columns([1, 2], gap="large")

    with col_run:
        st.markdown(card("""
        <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;font-weight:600;margin-bottom:10px;">Execution Control</div>
        <p style="font-size:.875rem;color:#64748b;margin:0;">Triggers QUBO matrix construction with your current routes and drivers, applies fatigue + capacity constraints, and generates a fair dispatch manifest.</p>
        """), unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Run QAOA Optimizer", use_container_width=True, type="primary"):
            with st.spinner("Compiling Hamiltonian and optimizing..."):
                time.sleep(1.5)
                run_hybrid_qaoa_allocation()
                load_data_to_session()
            alloc_df = st.session_state.get('allocations', None)
            st.success("Manifest generated and saved to NeonDB.")

    with col_info:
        cl_score = st.session_state.get('classical_score')
        qa_score = st.session_state.get('qaoa_score')
        ar       = st.session_state.get('approx_ratio')
        if cl_score is not None:
            m1, m2, m3 = st.columns(3)
            m1.metric("Classical Fairness", f"{cl_score}", help="Wage std-dev — lower is more equitable")
            m2.metric("QAOA Fairness",      f"{qa_score}", delta=f"-{round(cl_score-qa_score,2)}" if qa_score < cl_score else None,
                      help="Wage std-dev after QAOA optimization")
            m3.metric("Approx. Ratio",      f"{ar}x",     help="QAOA / Classical fairness improvement ratio")
        else:
            st.info("Run the optimizer to see Classical vs QAOA comparison metrics.")

    # ── Side-by-side comparison ──
    if st.session_state.get('classical_alloc') is not None and alloc_df is not None and not alloc_df.empty:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(section_header("Classical vs QAOA — Assignment Comparison",
                    "Left: greedy classical solver (sort by urgency). Right: QAOA-weighted solver (minimises fatigue + capacity jointly)."),
                    unsafe_allow_html=True)

        cmp_l, cmp_r = st.columns(2, gap="large")
        with cmp_l:
            st.markdown("""
            <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;font-weight:600;margin-bottom:12px;">Classical Greedy Solver</div>
            """, unsafe_allow_html=True)
            st.dataframe(st.session_state.classical_alloc.style.map(style_difficulty, subset=['Difficulty']),
                         use_container_width=True)
        with cmp_r:
            st.markdown("""
            <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#6366f1;font-weight:600;margin-bottom:12px;">QAOA Quantum Solver</div>
            """, unsafe_allow_html=True)
            st.dataframe(alloc_df.style.map(style_difficulty, subset=['Difficulty']),
                         use_container_width=True)

        # Wage equity chart
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        with st.expander("Wage Equity Distribution Comparison", expanded=True):
            cl_wages = st.session_state.classical_alloc.groupby('Driver')['Est_Wage ($)'].sum().reset_index()
            qa_wages = alloc_df.groupby('Driver')['Est_Wage ($)'].sum().reset_index()
            cl_wages['Solver'] = 'Classical'
            qa_wages['Solver'] = 'QAOA'
            import pandas as pd
            combined = pd.concat([cl_wages, qa_wages])
            fig_cmp = px.bar(
                combined, x='Driver', y='Est_Wage ($)', color='Solver', barmode='group',
                template='plotly_dark',
                color_discrete_map={'Classical': '#475569', 'QAOA': '#6366f1'},
            )
            fig_cmp.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(gridcolor='#1c2038'), yaxis=dict(gridcolor='#1c2038'),
                legend=dict(bgcolor='rgba(0,0,0,0)'),
            )
            st.plotly_chart(fig_cmp, use_container_width=True)

    # ── Circuit topology ──
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(section_header("Quantum Circuit Topology",
                "QAOA ansatz applied to the vehicle routing QUBO. One parametrized layer with Hadamard initialization."),
                unsafe_allow_html=True)

    try:
        n_q = min(5, max(2, n_drivers))
        qc = QuantumCircuit(n_q)
        qc.h(range(n_q))
        qc.barrier()
        gamma, beta = Parameter('gamma'), Parameter('beta')
        for i in range(n_q - 1):
            qc.cx(i, i + 1)
            qc.rz(gamma, i + 1)
            qc.cx(i, i + 1)
        qc.barrier()
        for i in range(n_q):
            qc.rx(beta, i)
        qc.measure_all()

        # Try matplotlib first, fall back to text
        circuit_drawn = False
        try:
            fig_qc, ax_qc = plt.subplots(figsize=(14, 3))
            fig_qc.patch.set_facecolor('#0f111a')
            ax_qc.set_facecolor('#0f111a')
            qc.draw(
                output='mpl', ax=ax_qc,
                style={
                    'backgroundcolor': '#0f111a',
                    'textcolor':       '#c7d2fe',
                    'gatefacecolor':   '#1c2038',
                    'gatetextcolor':   '#818cf8',
                    'subtextcolor':    '#475569',
                    'linecolor':       '#334155',
                    'creglinecolor':   '#4f46e5',
                    'measurearrowcolor': '#818cf8',
                },
                fold=40,
                initial_state=True,
                plot_barriers=True
            )
            plt.tight_layout()
            st.pyplot(fig_qc, use_container_width=True)
            plt.close(fig_qc)
            circuit_drawn = True
        except Exception:
            circuit_drawn = False

        if not circuit_drawn:
            circuit_text = qc.draw(output='text')
            st.code(str(circuit_text), language="text")

        # Metadata row
        st.markdown(f"""
        <div style="display:flex;gap:20px;margin-top:16px;flex-wrap:wrap;align-items:center;">
            <div style="background:#13172a;border:1px solid #1c2038;border-radius:6px;padding:6px 14px;font-size:.75rem;color:#64748b;">
                <span style="color:#818cf8;font-weight:600;">{n_q}</span> qubits
            </div>
            <div style="background:#13172a;border:1px solid #1c2038;border-radius:6px;padding:6px 14px;font-size:.75rem;color:#64748b;">
                <span style="color:#818cf8;font-weight:600;">1</span> QAOA layer
            </div>
            <div style="background:#13172a;border:1px solid #1c2038;border-radius:6px;padding:6px 14px;font-size:.75rem;color:#64748b;">
                <span style="color:#818cf8;font-weight:600;">2</span> variational parameters (gamma, beta)
            </div>
            <div style="background:#13172a;border:1px solid #1c2038;border-radius:6px;padding:6px 14px;font-size:.75rem;color:#64748b;">
                Qiskit Aer Simulator
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Circuit construction error: {e}")

# ── TAB 4: TOKEN GOVERNANCE ──
with tab4:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Driver Override Governance",
                "Review and arbitrate pending route renegotiation requests."), unsafe_allow_html=True)

    pending = [r for r in st.session_state.token_requests if r['status'] == 'Pending']

    if not pending:
        st.markdown(card("""
        <div style="text-align:center;padding:40px;">
            <div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:8px;">No Pending Requests</div>
            <div style="font-size:.875rem;color:#475569;">All override requests have been resolved. Dispatch manifest is stable.</div>
        </div>
        """), unsafe_allow_html=True)
    else:
        for idx, req in enumerate(st.session_state.token_requests):
            if req['status'] != 'Pending':
                continue
            with st.expander(
                f"Case #{req.get('id', '—')}  |  Driver: {req['driver']}  |  Route: {req['current_route']}  |  Difficulty: {req['difficulty']}",
                expanded=True
            ):
                col_info, col_action = st.columns([2, 1])
                with col_info:
                    st.markdown(f"""
                    <div style="margin-bottom:12px;">
                        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:4px;">Route Assignment</div>
                        <div style="font-size:.9rem;font-weight:600;color:#e2e8f0;">{req['current_route']} &nbsp; {badge(req['difficulty'])}</div>
                    </div>
                    <div>
                        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:4px;">Driver Justification</div>
                        <div style="font-size:.875rem;color:#94a3b8;">{req['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_action:
                    if st.button("Approve Override", key=f"app_{idx}", use_container_width=True, type="primary"):
                        d_df = st.session_state.drivers
                        d_idx = d_df.index[d_df['Name'] == req['driver']].tolist()
                        if d_idx:
                            st.session_state.drivers.at[d_idx[0], 'Monthly_Tokens'] -= 1
                            save_drivers_to_db(st.session_state.drivers)
                        if alloc_df is not None and not alloc_df.empty:
                            a_idx = alloc_df.index[alloc_df['Route_ID'] == req['current_route']].tolist()
                            if a_idx:
                                st.session_state.allocations.at[a_idx[0], 'Route_ID'] = "RELIEF-01"
                                st.session_state.allocations.at[a_idx[0], 'Difficulty'] = "LOW"
                                st.session_state.allocations.at[a_idx[0], 'Est_Wage ($)'] = 40
                        st.session_state.token_requests[idx]['status'] = 'Approved'
                        st.rerun()
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if st.button("Deny", key=f"den_{idx}", use_container_width=True):
                        st.session_state.token_requests[idx]['status'] = 'Denied'
                        st.rerun()
