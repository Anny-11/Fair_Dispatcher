import streamlit as st
import time
from utils.state_manager import inject_css

st.set_page_config(page_title="Driver Portal | Fair Dispatcher", page_icon="🚚", layout="centered")

if not st.session_state.get('authenticated') or st.session_state.get('role') != "Driver":
    st.error("🔒 Unauthorized. Redirecting to gateway...")
    time.sleep(1)
    st.switch_page("app.py")

inject_css()

driver_sel = st.session_state.current_user

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style="padding: 24px 16px 16px 16px;">
        <div style="font-size: 1.15rem; font-weight: 700; color: #818cf8 !important;">⚡ Fair Dispatcher</div>
        <div style="font-size: 0.75rem; color: #475569 !important; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.8px;">Driver Portal</div>
    </div>
    <hr style="border-color: #2d3148; margin: 0 16px 16px 16px;">
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding: 12px 16px; background: #1a1d27; border-radius: 10px; margin: 0 8px 20px 8px; border: 1px solid #2d3148;">
        <div style="font-size: 0.72rem; color: #475569 !important; text-transform: uppercase; letter-spacing: 1px;">Licensed Operator</div>
        <div style="font-size: 0.95rem; font-weight: 600; color: #c7d2fe !important; margin-top:4px;">{driver_sel}</div>
        <div style="font-size: 0.72rem; color: #fbbf24 !important; margin-top:3px;">● On Duty</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        for k in ['authenticated', 'role', 'current_user']:
            st.session_state[k] = None
        st.session_state.authenticated = False
        st.switch_page("app.py")

# ── Page Header ──
st.markdown(f"""
<div style="padding: 32px 0 8px 0;">
    <div style="font-size: 0.78rem; color: #475569; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600;">Driver Portal</div>
    <div style="font-size: 2rem; font-weight: 800; margin-top: 4px; color: #e2e8f0;">Welcome back, {driver_sel} 👋</div>
    <div style="font-size: 0.9rem; color: #64748b; margin-top: 6px;">Your real-time dispatch manifest, token wallet, and route assignment controls.</div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Fetch driver data ──
try:
    driver_data = st.session_state.drivers[st.session_state.drivers['Name'].str.lower() == driver_sel.lower()].iloc[0]
except IndexError:
    st.error(f"Driver profile '{driver_sel}' not found in active roster.")
    st.stop()

# ── KPI Metrics Row ──
st.markdown("""<div style="margin-bottom: 8px; font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600;">Operator Status Dashboard</div>""", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Fatigue Index", f"{driver_data['Fatigue_Score']}")
c2.metric("Token Wallet", f"{int(driver_data['Monthly_Tokens'])} pts")
c3.metric("Vehicle Capacity", f"{driver_data['Vehicle_Capacity_kg']} kg")
c4.metric("Shift Workload", f"{driver_data['Past_Workload']} hrs")

st.markdown("---")

# ── Route Assignment ──
if 'allocations' not in st.session_state:
    st.markdown("""
    <div style="background:#1a1d27; border:1px solid #2d3148; border-radius:12px; padding:40px; text-align:center;">
        <div style="font-size:2rem; margin-bottom:12px;">⏳</div>
        <div style="font-weight:600; color:#e2e8f0; margin-bottom:6px;">Awaiting Dispatch</div>
        <div style="font-size:0.87rem; color:#475569;">The QAOA central optimizer has not yet generated today's manifest. Check back shortly.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

alloc_data_subset = st.session_state.allocations[st.session_state.allocations['Driver'].str.lower() == driver_sel.lower()]

if alloc_data_subset.empty:
    st.info("No routes assigned to your profile in the current manifest.")
    st.stop()

assigned_route = alloc_data_subset.iloc[0]['Route_ID']
assigned_diff = alloc_data_subset.iloc[0]['Difficulty']
diff_colors = {'HIGH': '#f87171', 'MEDIUM': '#fbbf24', 'LOW': '#34d399'}
diff_color = diff_colors.get(assigned_diff, '#94a3b8')
diff_icons = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
diff_icon = diff_icons.get(assigned_diff, '⚪')

pending_reqs = [r for r in st.session_state.token_requests if r['driver'].lower() == driver_sel.lower() and r['status'] == 'Pending']
approved_reqs = [r for r in st.session_state.token_requests if r['driver'].lower() == driver_sel.lower() and r['status'] == 'Approved']
denied_reqs = [r for r in st.session_state.token_requests if r['driver'].lower() == driver_sel.lower() and r['status'] == 'Denied']

# ── Notification Banner ──
if pending_reqs:
    st.markdown(f"""<div style="background:rgba(99,102,241,0.12); border:1px solid #4f46e5; border-radius:10px; padding:14px 18px; margin-bottom:20px; font-size:0.87rem; color:#818cf8;">
    ⏳ <strong>Token override pending admin review.</strong> Your request for Route {assigned_route} has been submitted and is under evaluation.
    </div>""", unsafe_allow_html=True)
elif approved_reqs:
    st.success("✅ Override approved. You've been rerouted to a relief assignment.")
elif denied_reqs:
    st.error("❌ Override denied. Original manifest maintained by dispatch.")

# ── Route Card ──
st.markdown(f"""
<div style="background: linear-gradient(145deg, #1a1d27, #141722); border:1px solid #2d3148; border-radius:16px; padding:28px 32px; margin-bottom:24px;">
    <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600; margin-bottom:16px;">Active Route Assignment</div>
    <div style="display:flex; align-items:baseline; gap:12px;">
        <div style="font-size:2.2rem; font-weight:800; color:#e2e8f0;">Route {assigned_route}</div>
        <div style="background: {diff_color}22; border: 1px solid {diff_color}66; border-radius:6px; padding:4px 12px; font-size:0.78rem; font-weight:700; color:{diff_color}; letter-spacing:1px;">{diff_icon} {assigned_diff}</div>
    </div>
    <div style="margin-top:12px; color:#64748b; font-size:0.87rem;">Terrain & payload complexity evaluated by the QAOA constraint engine.</div>
</div>
""", unsafe_allow_html=True)

# ── Surge Bonus Alert ──
if assigned_diff == "HIGH":
    st.markdown("""
    <div style="background:rgba(251,191,36,0.1); border:1px solid #fbbf24; border-radius:10px; padding:14px 18px; margin-bottom:20px;">
        🔥 <strong style="color:#fbbf24;">Surge Bonus Active</strong><br>
        <span style="font-size:0.85rem; color:#94a3b8;">Completing this HIGH-difficulty route will award +1 Flexibility Token to your wallet automatically.</span>
    </div>
    """, unsafe_allow_html=True)

# ── Action Buttons ──
if not pending_reqs:
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        if st.button("✅  Acknowledge & Lock Manifest", use_container_width=True, type="primary"):
            if assigned_diff == "HIGH":
                idx = st.session_state.drivers.index[st.session_state.drivers['Name'].str.lower() == driver_sel.lower()].tolist()[0]
                st.session_state.drivers.at[idx, 'Monthly_Tokens'] += 1
                st.success("Route confirmed! +1 token has been credited to your wallet. 💎")
            else:
                st.success("Manifest locked. Have a safe shift! 🚛")
    with col_b:
        if st.button("🔄  Request Token Override", use_container_width=True):
            if int(driver_data['Monthly_Tokens']) > 0:
                if assigned_diff in ['HIGH', 'MEDIUM']:
                    st.session_state.requesting_token = True
                else:
                    st.warning("You're already on the lowest difficulty assignment.")
            else:
                st.error("Token wallet empty. No override credits available.")

# ── Token Request Form ──
if st.session_state.get('requesting_token', False):
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("""<div style="background:#1a1d27; border:1px solid #4f46e5; border-radius:12px; padding:24px;">
        <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1px; color:#475569; font-weight:600; margin-bottom:16px;">File Override Exception</div>""", unsafe_allow_html=True)

        with st.form("token_form"):
            reason = st.text_area("Override justification", placeholder="e.g. Physical fatigue threshold exceeded, cumulative 6-day load...")
            submitted = st.form_submit_button("Submit to Dispatch Network", use_container_width=True)
            if submitted and reason:
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
