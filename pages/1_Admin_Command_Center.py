import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import time

from utils.state_manager import (inject_css, style_difficulty, classify_route,
                                  kpi_card, badge, section_header, card,
                                  save_drivers_to_db, save_routes_to_db, load_data_to_session)
from utils.quantum_solver import run_hybrid_qaoa_allocation

st.set_page_config(page_title="Admin · Fair Dispatcher", page_icon="🛰️", layout="wide")

if not st.session_state.get('authenticated') or st.session_state.get('role') != "Administrator":
    st.switch_page("app.py")

inject_css()

# ════════════════ SIDEBAR ════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 16px 0;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
            <div style="width:28px;height:28px;background:linear-gradient(135deg,#4f46e5,#818cf8);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.85rem;">⚡</div>
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
                <div style="font-size:.7rem;color:#34d399;margin-top:1px;">● Administrator</div>
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

n_drivers  = len(drivers_df) if drivers_df is not None else 0
n_routes   = len(routes_df)  if routes_df  is not None else 0
n_alloc    = len(alloc_df)   if alloc_df   is not None and not alloc_df.empty else 0
avg_fatigue = round(drivers_df['Fatigue_Score'].mean(), 2) if drivers_df is not None and n_drivers>0 else "—"

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1: st.markdown(kpi_card("Active Drivers", n_drivers, "Fleet size", "#6366f1"), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("Open Routes", n_routes, "Pending dispatch", "#818cf8"), unsafe_allow_html=True)
with c3: st.markdown(kpi_card("Manifested", n_alloc, "QAOA assignments", "#34d399"), unsafe_allow_html=True)
with c4: st.markdown(kpi_card("Avg Fatigue", avg_fatigue, "Fleet health index", "#fbbf24"), unsafe_allow_html=True)

st.markdown("</div><div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("---")

# ════════════════ TABS ════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "🚛  Fleet Operations",
    "📊  Analytics",
    "⚛️  Quantum Engine",
    "🪙  Token Governance"
])

# ── TAB 1: FLEET ──
with tab1:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Routes Registry",
                "Add, edit, or remove delivery routes before running the optimizer."), unsafe_allow_html=True)

    edited_routes = st.data_editor(
        st.session_state.routes, num_rows="dynamic", use_container_width=True,
        column_config={
            "Route_ID": st.column_config.TextColumn("Route ID", width="small"),
            "Deliveries": st.column_config.NumberColumn("Deliveries", min_value=0),
            "Weight_kg": st.column_config.NumberColumn("Weight (kg)", min_value=0),
            "Distance_km": st.column_config.NumberColumn("Distance (km)", min_value=0),
        }
    )
    col_save, _ = st.columns([1, 3])
    with col_save:
        if st.button("💾  Save Routes", use_container_width=True):
            save_routes_to_db(edited_routes)
            st.session_state.routes = edited_routes
            st.success("Routes saved to database.")

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(section_header("Driver Directory",
                "Manage driver profiles, capacity, and fatigue metrics."), unsafe_allow_html=True)

    edited_drivers = st.data_editor(
        st.session_state.drivers, num_rows="dynamic", use_container_width=True,
        column_config={
            "Driver_ID": st.column_config.TextColumn("ID", width="small"),
            "Fatigue_Score": st.column_config.NumberColumn("Fatigue (0–1)", min_value=0.0, max_value=1.0, format="%.2f"),
            "Monthly_Tokens": st.column_config.NumberColumn("Tokens", min_value=0),
            "Vehicle_Capacity_kg": st.column_config.NumberColumn("Vehicle Cap (kg)", min_value=0),
        }
    )
    col_save2, _ = st.columns([1, 3])
    with col_save2:
        if st.button("💾  Save Drivers", use_container_width=True):
            save_drivers_to_db(edited_drivers)
            st.session_state.drivers = edited_drivers
            st.success("Driver records saved to database.")

# ── TAB 2: ANALYTICS ──
with tab2:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Fleet Intelligence",
                "Route difficulty breakdown and driver fatigue correlation."), unsafe_allow_html=True)

    with st.expander("📋  Route Difficulty Classification Matrix", expanded=True):
        routes_display = st.session_state.routes.copy()
        routes_display['Difficulty'] = routes_display.apply(classify_route, axis=1)
        st.dataframe(
            routes_display.style.map(style_difficulty, subset=['Difficulty']),
            use_container_width=True
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    with st.expander("📈  Fatigue × Workload Correlation", expanded=True):
        if drivers_df is not None and not drivers_df.empty:
            fig = px.scatter(
                drivers_df, x="Past_Workload", y="Fatigue_Score",
                size="Monthly_Tokens", color="Name", hover_name="Name",
                template="plotly_dark",
                color_discrete_sequence=["#818cf8","#34d399","#fbbf24","#f87171","#a78bfa"],
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0,r=0,t=10,b=0),
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8')),
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(gridcolor='#1c2038', title="Past Workload", title_font=dict(color='#64748b')),
                yaxis=dict(gridcolor='#1c2038', title="Fatigue Score", title_font=dict(color='#64748b')),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No driver data available.")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if drivers_df is not None and not drivers_df.empty:
        with st.expander("🏦  Token Wallet Distribution", expanded=False):
            fig2 = px.bar(
                drivers_df, x="Name", y="Monthly_Tokens",
                color="Monthly_Tokens", template="plotly_dark",
                color_continuous_scale=["#1c2038","#4f46e5","#818cf8"],
                labels={"Monthly_Tokens": "Tokens"},
            )
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0,r=0,t=10,b=0),
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(gridcolor='#1c2038'), yaxis=dict(gridcolor='#1c2038'),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

# ── TAB 3: QUANTUM ENGINE ──
with tab3:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("QAOA Quantum Routing Engine",
                "Deploy QUBO Hamiltonian optimization across the vehicle routing graph."), unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown(card("""
        <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;font-weight:600;margin-bottom:12px;">Execution Control</div>
        <p style="font-size:.875rem;color:#64748b;margin-bottom:0;">Triggers QUBO matrix construction, applies driver fatigue and capacity constraints, and dispatches across the quantum simulator.</p>
        """), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        if st.button("⚡  Run QAOA Optimizer", use_container_width=True, type="primary"):
            with st.spinner("Compiling Hamiltonian & optimizing…"):
                time.sleep(1.8)
                run_hybrid_qaoa_allocation()
                load_data_to_session()
            st.success("✅  Dispatch manifest generated and saved to NeonDB.")

        if alloc_df is not None and not alloc_df.empty:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            st.markdown(section_header("Current Manifest"), unsafe_allow_html=True)
            st.dataframe(
                alloc_df.style.map(style_difficulty, subset=['Difficulty']),
                use_container_width=True
            )

    with right:
        st.markdown(card("""
        <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;font-weight:600;margin-bottom:16px;">Quantum Circuit Topology</div>
        """), unsafe_allow_html=True)

        try:
            n_q = min(5, max(2, n_drivers))
            qc = QuantumCircuit(n_q)
            qc.h(range(n_q))
            qc.barrier()
            gamma, beta = Parameter('γ'), Parameter('β')
            for i in range(n_q - 1):
                qc.cx(i, i+1); qc.rz(gamma, i+1); qc.cx(i, i+1)
            qc.barrier()
            for i in range(n_q):
                qc.rx(beta, i)
            qc.measure_all()
            circuit_text = qc.draw(output='text')
            st.code(str(circuit_text), language="text")
            st.markdown(f"""
            <div style="display:flex;gap:24px;margin-top:16px;flex-wrap:wrap;">
                <div>{badge("QAOA Layer 1","LOW")}</div>
                <div style="font-size:.78rem;color:#64748b">{n_q} qubits · 1 QAOA layer · 2 parameters</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Circuit error: {e}")

# ── TAB 4: TOKEN GOVERNANCE ──
with tab4:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Driver Override Governance",
                "Review and arbitrate pending route renegotiation requests."), unsafe_allow_html=True)

    pending = [r for r in st.session_state.token_requests if r['status'] == 'Pending']

    if not pending:
        st.markdown(card("""
        <div style="text-align:center;padding:32px;">
            <div style="font-size:2rem;margin-bottom:10px;">🎯</div>
            <div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:6px;">All Clear</div>
            <div style="font-size:.875rem;color:#475569;">No pending override requests. Dispatch manifest is stable.</div>
        </div>
        """), unsafe_allow_html=True)
    else:
        for idx, req in enumerate(st.session_state.token_requests):
            if req['status'] != 'Pending':
                continue
            with st.expander(
                f"Case #{req.get('id','—')}  ·  {req['driver']}  ·  Route {req['current_route']}  ·  {req['difficulty']}",
                expanded=True
            ):
                col_info, col_action = st.columns([2, 1])
                with col_info:
                    st.markdown(f"""
                    <div style="margin-bottom:10px;">
                        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:4px;">Route Assignment</div>
                        <div style="font-size:.9rem;font-weight:600;color:#e2e8f0;">{req['current_route']} &nbsp; {badge(req['difficulty'])}</div>
                    </div>
                    <div>
                        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:4px;">Justification</div>
                        <div style="font-size:.875rem;color:#94a3b8;">{req['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_action:
                    if st.button("✅ Approve Override", key=f"app_{idx}", use_container_width=True, type="primary"):
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
                    if st.button("❌ Deny", key=f"den_{idx}", use_container_width=True):
                        st.session_state.token_requests[idx]['status'] = 'Denied'
                        st.rerun()
