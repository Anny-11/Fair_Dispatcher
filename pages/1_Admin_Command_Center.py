import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import time

from utils.state_manager import inject_css, style_difficulty, classify_route
from utils.quantum_solver import run_hybrid_qaoa_allocation

st.set_page_config(page_title="Admin Command Center | Fair Dispatcher", page_icon="🛰️", layout="wide")

if not st.session_state.get('authenticated') or st.session_state.get('role') != "Administrator":
    st.error("🔒 Unauthorized. Redirecting to gateway...")
    time.sleep(1)
    st.switch_page("app.py")

inject_css()

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style="padding: 24px 16px 16px 16px;">
        <div style="font-size: 1.15rem; font-weight: 700; color: #818cf8 !important;">⚡ Fair Dispatcher</div>
        <div style="font-size: 0.75rem; color: #475569 !important; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.8px;">Admin Console</div>
    </div>
    <hr style="border-color: #2d3148; margin: 0 16px 16px 16px;">
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding: 12px 16px; background: #1a1d27; border-radius: 10px; margin: 0 8px 20px 8px; border: 1px solid #2d3148;">
        <div style="font-size: 0.72rem; color: #475569 !important; text-transform: uppercase; letter-spacing: 1px;">Signed In As</div>
        <div style="font-size: 0.95rem; font-weight: 600; color: #c7d2fe !important; margin-top:4px;">{st.session_state.current_user}</div>
        <div style="font-size: 0.72rem; color: #10b981 !important; margin-top:3px;">● Administrator</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        for k in ['authenticated', 'role', 'current_user']:
            st.session_state[k] = None
        st.session_state.authenticated = False
        st.switch_page("app.py")

# ── Page Header ──
st.markdown("""
<div style="padding: 32px 0 8px 0;">
    <div style="font-size: 0.78rem; color: #475569; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600;">Admin Command Center</div>
    <div style="font-size: 2rem; font-weight: 800; margin-top: 4px; color: #e2e8f0;">Dispatch Operations Dashboard</div>
    <div style="font-size: 0.9rem; color: #64748b; margin-top: 6px;">Manage fleet logistics, quantum routing, and driver token governance.</div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🚛  Fleet Operations", "📊  Intelligence", "⚛️  Quantum Engine", "🪙  Token Governance"])

# ── TAB 1: FLEET OPERATIONS ──
with tab1:
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">Fleet & Operations Registry</h3>
        <p style="color: #64748b; font-size: 0.88rem;">Configure real-time route and driver data before dispatching the QAOA engine.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style="background:#1a1d27; border:1px solid #2d3148; border-radius:12px; padding:24px; margin-bottom:24px;">
    <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600; margin-bottom:16px;">Active Routes Registry</div>""", unsafe_allow_html=True)
    st.session_state.routes = st.data_editor(st.session_state.routes, num_rows="dynamic", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""<div style="background:#1a1d27; border:1px solid #2d3148; border-radius:12px; padding:24px;">
    <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600; margin-bottom:16px;">Driver Workforce Directory</div>""", unsafe_allow_html=True)
    st.session_state.drivers = st.data_editor(st.session_state.drivers, num_rows="dynamic", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── TAB 2: INTELLIGENCE ──
with tab2:
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">Intelligence & Workload Analysis</h3>
        <p style="color: #64748b; font-size: 0.88rem;">Programmatic classification and fatigue correlation across the active fleet.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋  Route Difficulty Classification Matrix", expanded=True):
        routes_df = st.session_state.routes.copy()
        routes_df['Difficulty'] = routes_df.apply(classify_route, axis=1)
        st.dataframe(routes_df.style.map(style_difficulty, subset=['Difficulty']), width='stretch')

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    with st.expander("📈  Driver Fatigue & Workload Correlation", expanded=True):
        fig = px.scatter(
            st.session_state.drivers,
            x="Past_Workload", y="Fatigue_Score",
            size="Monthly_Tokens", color="Name",
            hover_name="Name",
            title="",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(bgcolor='rgba(0,0,0,0)')
        )
        fig.update_xaxes(gridcolor='#2d3148', zerolinecolor='#2d3148')
        fig.update_yaxes(gridcolor='#2d3148', zerolinecolor='#2d3148')
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 3: QUANTUM ENGINE ──
with tab3:
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">QAOA Quantum Routing Engine</h3>
        <p style="color: #64748b; font-size: 0.88rem;">Deploy QUBO Hamiltonian optimization to generate a balanced dispatch manifest.</p>
    </div>
    """, unsafe_allow_html=True)

    col_ctrl, col_status = st.columns([1, 1], gap="large")

    with col_ctrl:
        st.markdown("""<div style="background:#1a1d27; border:1px solid #2d3148; border-radius:12px; padding:24px;">
        <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600; margin-bottom:12px;">Execution Control</div>
        <p style="color:#64748b; font-size:0.85rem; margin-bottom:20px;">Triggers the QUBO matrix construction and hybrid QAOA solver across the vehicle routing graph.</p>
        """, unsafe_allow_html=True)

        if st.button("⚡  Initialize QAOA Allocation", use_container_width=True, type="primary"):
            with st.spinner("Compiling Hamiltonian constraints..."):
                time.sleep(1.5)
                run_hybrid_qaoa_allocation()
            st.success("✅ Quantum manifest generated.")

        st.markdown("</div>", unsafe_allow_html=True)

        if 'allocations' in st.session_state:
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown("""<div style="background:#1a1d27; border:1px solid #2d3148; border-radius:12px; padding:24px;">
            <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600; margin-bottom:16px;">Current Dispatch Manifest</div>""", unsafe_allow_html=True)
            st.dataframe(st.session_state.allocations.style.map(style_difficulty, subset=['Difficulty']), width='stretch')
            st.markdown("</div>", unsafe_allow_html=True)

    with col_status:
        st.markdown("""<div style="background:#1a1d27; border:1px solid #2d3148; border-radius:12px; padding:24px;">
        <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600; margin-bottom:16px;">Quantum Circuit Topology</div>""", unsafe_allow_html=True)

        try:
            qubits_to_show = min(5, len(st.session_state.drivers) + 1)
            qc = QuantumCircuit(qubits_to_show)
            qc.h(range(qubits_to_show))
            qc.barrier()
            gamma, beta = Parameter('γ'), Parameter('β')
            for i in range(qubits_to_show - 1):
                qc.cx(i, i + 1)
                qc.rz(gamma, i + 1)
                qc.cx(i, i + 1)
            qc.barrier()
            for i in range(qubits_to_show):
                qc.rx(beta, i)
            qc.measure_all()
            
            # Using text backend which works identically across all systems
            circuit_text = qc.draw(output='text')
            st.code(str(circuit_text), language="text")
        except Exception as e:
            st.error(f"Circuit visualizer error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

# ── TAB 4: TOKEN GOVERNANCE ──
with tab4:
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">Driver Token Override Governance</h3>
        <p style="color: #64748b; font-size: 0.88rem;">Review and arbitrate pending driver-initiated route renegotiation requests.</p>
    </div>
    """, unsafe_allow_html=True)

    pending_reqs = [r for r in st.session_state.token_requests if r['status'] == 'Pending']

    if not pending_reqs:
        st.markdown("""
        <div style="background:#1a1d27; border:1px solid #2d3148; border-radius:12px; padding:40px; text-align:center;">
            <div style="font-size:2rem; margin-bottom:12px;">🎯</div>
            <div style="font-weight:600; color:#e2e8f0; margin-bottom:6px;">All Clear</div>
            <div style="font-size:0.87rem; color:#475569;">No pending override requests. Dispatch manifest is stable.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, req in enumerate(st.session_state.token_requests):
            if req['status'] != 'Pending':
                continue
            with st.expander(f"🔴  Case #{idx+874}  ·  Agent: {req['driver']}  ·  Route: {req['current_route']}", expanded=True):
                col_i, col_a = st.columns([2, 1])
                with col_i:
                    st.markdown(f"""
                    <div style='margin-bottom:8px;'>
                        <span style='color:#475569;font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;'>Assigned Task</span><br>
                        <span style='font-weight:600;'>{req['current_route']} — Difficulty: {req['difficulty']}</span>
                    </div>
                    <div>
                        <span style='color:#475569;font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;'>Driver Justification</span><br>
                        <span style='color:#94a3b8;'>{req['reason']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_a:
                    if st.button("✅ Approve Override", key=f"app_{idx}", use_container_width=True, type="primary"):
                        d_idx = st.session_state.drivers.index[st.session_state.drivers['Name'] == req['driver']].tolist()[0]
                        st.session_state.drivers.at[d_idx, 'Monthly_Tokens'] -= 1
                        idx_alloc = st.session_state.allocations.index[st.session_state.allocations['Route_ID'] == req['current_route']].tolist()[0]
                        st.session_state.allocations.at[idx_alloc, 'Route_ID'] = "R_RELIEF_01"
                        st.session_state.allocations.at[idx_alloc, 'Difficulty'] = "LOW"
                        st.session_state.allocations.at[idx_alloc, 'Est_Wage ($)'] = 50
                        st.session_state.token_requests[idx]['status'] = 'Approved'
                        st.rerun()
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if st.button("❌ Deny Request", key=f"den_{idx}", use_container_width=True):
                        st.session_state.token_requests[idx]['status'] = 'Denied'
                        st.rerun()
