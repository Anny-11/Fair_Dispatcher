import streamlit as st
import time
from utils.state_manager import (inject_css, classify_route, kpi_card, badge,
                                  section_header, card, save_drivers_to_db, load_data_to_session)
from utils.database import get_db_session, TokenRequest

st.set_page_config(page_title="Driver Portal · Fair Dispatcher", page_icon="FD", layout="wide")

if not st.session_state.get('authenticated') or st.session_state.get('role') != "Driver":
    st.switch_page("app.py")

inject_css()
driver_sel = st.session_state.current_user

# ════════════════ SIDEBAR ════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 16px 0;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
            <div style="width:28px;height:28px;background:linear-gradient(135deg,#4f46e5,#818cf8);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.85rem;">⚡</div>
            <span style="font-size:1rem;font-weight:800;color:#f1f5f9;letter-spacing:-.02em;">Fair Dispatcher</span>
        </div>
        <div style="font-size:.7rem;color:#334155;text-transform:uppercase;letter-spacing:.08em;padding-left:36px;margin-bottom:20px;">Driver Portal</div>
    </div>
    <div style="height:1px;background:#1c2038;margin:0 16px 16px;"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin:0 8px 16px;background:#13172a;border:1px solid #1c2038;border-radius:10px;padding:14px 16px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#f59e0b,#fbbf24);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;color:#0f111a;font-size:.9rem;flex-shrink:0;">
                {driver_sel[0].upper()}
            </div>
            <div>
                <div style="font-size:.875rem;font-weight:600;color:#e2e8f0;">{driver_sel}</div>
                <div style="font-size:.7rem;color:#fbbf24;margin-top:1px;">● On Duty</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True):
        for k in ['authenticated', 'role', 'current_user']:
            st.session_state[k] = None
        st.session_state.authenticated = False
        st.switch_page("app.py")

# ════════════════ PAGE HEADER ════════════════
st.markdown(f"""
<div style="padding:28px 0 8px;">
    <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#475569;font-weight:600;margin-bottom:6px;">Driver Portal</div>
    <div style="font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-.03em;">Hey, {driver_sel} 👋</div>
    <div style="font-size:.875rem;color:#475569;margin-top:4px;">Your live dispatch manifest, token wallet, and shift controls.</div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ════════════════ FETCH DRIVER DATA ════════════════
drivers_df = st.session_state.get('drivers')
try:
    driver_data = drivers_df[drivers_df['Name'].str.lower() == driver_sel.lower()].iloc[0]
except (IndexError, AttributeError):
    st.error(f"Driver profile '{driver_sel}' not found. Contact your administrator.")
    st.stop()

token_requests = st.session_state.get('token_requests', [])
pending_reqs  = [r for r in token_requests if r['driver'].lower() == driver_sel.lower() and r['status'] == 'Pending']
approved_reqs = [r for r in token_requests if r['driver'].lower() == driver_sel.lower() and r['status'] == 'Approved']
denied_reqs   = [r for r in token_requests if r['driver'].lower() == driver_sel.lower() and r['status'] == 'Denied']

# ════════════════ KPI CARDS ════════════════
st.markdown(section_header("Your Metrics", "Live biometric and economic snapshot."), unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4, gap="medium")
fatigue_pct = int(driver_data['Fatigue_Score'] * 100)
fatigue_color = "#f87171" if fatigue_pct > 70 else "#fbbf24" if fatigue_pct > 40 else "#34d399"
with c1: st.markdown(kpi_card("Fatigue Index", f"{driver_data['Fatigue_Score']}", f"{fatigue_pct}% of limit", fatigue_color), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("Token Wallet", f"{int(driver_data['Monthly_Tokens'])}", "Override credits", "#818cf8"), unsafe_allow_html=True)
with c3: st.markdown(kpi_card("Vehicle Capacity", f"{int(driver_data['Vehicle_Capacity_kg'])} kg", "Max payload", "#34d399"), unsafe_allow_html=True)
with c4: st.markdown(kpi_card("Shift Workload", f"{int(driver_data['Past_Workload'])}h", "Cumulative hours", "#6366f1"), unsafe_allow_html=True)

st.markdown("---")

# ════════════════ ROUTE ASSIGNMENT ════════════════
alloc_df = st.session_state.get('allocations')

if alloc_df is None or alloc_df.empty:
    st.markdown(card("""
    <div style="text-align:center;padding:40px;">
        <div style="font-size:2.5rem;margin-bottom:12px;">⏳</div>
        <div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:6px;">Awaiting Dispatch</div>
        <div style="font-size:.875rem;color:#475569;">The central QAOA optimizer has not generated today's manifest yet.</div>
    </div>
    """), unsafe_allow_html=True)
    st.stop()

my_alloc = alloc_df[alloc_df['Driver'].str.lower() == driver_sel.lower()]
if my_alloc.empty:
    st.info("No routes assigned to you in the current manifest.")
    st.stop()

assigned_route = my_alloc.iloc[0]['Route_ID']
assigned_diff  = my_alloc.iloc[0]['Difficulty']
assigned_wage  = my_alloc.iloc[0]['Est_Wage ($)']

diff_meta = {
    "HIGH":   {"color":"#f87171","bg":"rgba(239,68,68,.1)","border":"rgba(239,68,68,.3)","icon":"🔴"},
    "MEDIUM": {"color":"#fbbf24","bg":"rgba(245,158,11,.1)","border":"rgba(245,158,11,.3)","icon":"🟡"},
    "LOW":    {"color":"#34d399","bg":"rgba(16,185,129,.1)","border":"rgba(16,185,129,.3)","icon":"🟢"},
}
dm = diff_meta.get(assigned_diff, {"color":"#94a3b8","bg":"rgba(148,163,184,.1)","border":"rgba(148,163,184,.3)","icon":"⚪"})

st.markdown(section_header("Today's Assignment"), unsafe_allow_html=True)

# Notification banners
if pending_reqs:
    st.markdown(f"""<div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.3);border-radius:10px;padding:14px 18px;margin-bottom:16px;font-size:.875rem;color:#818cf8;">
    ⏳ &nbsp;<strong>Token override pending.</strong> Route {assigned_route} is under admin review.
    </div>""", unsafe_allow_html=True)
elif approved_reqs:
    st.success("✅  Override approved. You've been rerouted to a relief assignment.")
elif denied_reqs:
    st.error("❌  Override denied by dispatch. Original manifest will be enforced.")

# Route Card — using Streamlit native components to avoid LaTeX/$ conflicts
col_left, col_right = st.columns([3, 1])
with col_left:
    st.markdown(f"""
    <div style="background:#0f111a;border:1px solid #1c2038;border-left:3px solid {dm['color']};border-radius:12px;padding:24px 28px;margin-bottom:20px;">
        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:#475569;font-weight:600;margin-bottom:10px;">Active Route Assignment</div>
        <div style="font-size:2.4rem;font-weight:800;color:#f1f5f9;letter-spacing:-.04em;">Route {assigned_route}</div>
        <div style="font-size:.875rem;color:#64748b;margin-top:8px;">QAOA-optimized — based on fatigue load, payload and urgency constraints.</div>
    </div>
    """, unsafe_allow_html=True)
with col_right:
    st.markdown(f"""
    <div style="background:#0f111a;border:1px solid #1c2038;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px;">
        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;margin-bottom:8px;">Difficulty</div>
        <div style="background:{dm['bg']};border:1px solid {dm['border']};border-radius:8px;padding:8px 0;font-size:.85rem;font-weight:700;color:{dm['color']};letter-spacing:.06em;text-transform:uppercase;">{dm['icon']} {assigned_diff}</div>
        <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;margin-top:14px;margin-bottom:4px;">Est. Wage</div>
        <div style="font-size:1.4rem;font-weight:800;color:#34d399;">USD {assigned_wage}</div>
    </div>
    """, unsafe_allow_html=True)

if assigned_diff == "HIGH" and not pending_reqs:
    st.markdown("""
    <div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.25);border-radius:10px;padding:14px 18px;margin-bottom:20px;">
        <strong style="color:#fbbf24;">Surge Bonus Active</strong><br>
        <span style="font-size:.85rem;color:#94a3b8;margin-top:2px;display:block;">Acknowledging this HIGH-difficulty route will award +1 Flexibility Token to your wallet.</span>
    </div>
    """, unsafe_allow_html=True)

# Action buttons
if not pending_reqs:
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        if st.button("Acknowledge and Lock Manifest", use_container_width=True, type="primary"):
            if assigned_diff == "HIGH":
                idx = st.session_state.drivers.index[st.session_state.drivers['Name'].str.lower() == driver_sel.lower()].tolist()
                if idx:
                    st.session_state.drivers.at[idx[0], 'Monthly_Tokens'] += 1
                    save_drivers_to_db(st.session_state.drivers)
                st.success("Route confirmed. +1 Flexibility Token has been credited to your wallet.")
            else:
                st.success("Manifest locked. Have a safe shift.")
    with col_b:
        if st.button("Request Route Override", use_container_width=True):
            if int(driver_data['Monthly_Tokens']) > 0:
                if assigned_diff in ['HIGH', 'MEDIUM']:
                    st.session_state.requesting_token = True
                else:
                    st.warning("You're already on the lowest difficulty assignment.")
            else:
                st.error("Token wallet empty — no override credits available.")

# Override Form
if st.session_state.get('requesting_token', False):
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0f111a;border:1px solid rgba(99,102,241,.4);border-radius:12px;padding:24px;margin-bottom:8px;">
        <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;font-weight:600;margin-bottom:16px;">File Override Exception</div>
    """, unsafe_allow_html=True)

    with st.form("token_form"):
        reason = st.text_area("Justification", placeholder="e.g. Cumulative fatigue threshold exceeded, mechanical issue with vehicle…", height=100)
        submitted = st.form_submit_button("Submit to Dispatch Network", use_container_width=True)
        if submitted:
            if not reason.strip():
                st.warning("Please provide a justification.")
            else:
                db = get_db_session()
                new_req = TokenRequest(
                    driver_name=driver_sel,
                    route_id=assigned_route,
                    difficulty=assigned_diff,
                    reason=reason.strip(),
                    status="Pending"
                )
                db.add(new_req)
                db.commit()
                db.close()
                load_data_to_session()
                st.session_state.requesting_token = False
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# Request history
past_reqs = [r for r in token_requests if r['driver'].lower() == driver_sel.lower() and r['status'] != 'Pending']
if past_reqs:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    with st.expander("Override Request History", expanded=False):
        for req in past_reqs:
            status_badge = badge(req['status'])
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #1c2038;">
                <div style="font-size:.875rem;color:#94a3b8;">Route {req['current_route']} — {req['difficulty']}</div>
                <div>{status_badge}</div>
            </div>
            """, unsafe_allow_html=True)
