import streamlit as st
import time
from utils.state_manager import initialize_system_state, inject_css, CREDENTIALS

st.set_page_config(
    page_title="Fair Dispatcher — Secure Gateway",
    page_icon="⚡",
    layout="centered"
)

initialize_system_state()
inject_css()

# ── Already authenticated → show session info ──
if st.session_state.get('authenticated', False):
    st.markdown(f"""
    <div style="text-align:center; padding: 80px 0 40px 0;">
        <div style="font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #818cf8, #4f46e5); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Fair Dispatcher
        </div>
        <div style="color: #64748b; margin-top: 8px; font-size: 1rem;">Quantum-Powered Delivery Logistics</div>
    </div>
    <div style="background:#1a1d27; border:1px solid #2d3148; border-radius:14px; padding:28px 32px; text-align:center;">
        <p style="color:#94a3b8; margin-bottom:6px; font-size:0.85rem; text-transform:uppercase; letter-spacing:1px;">Active Session</p>
        <p style="font-size:1.4rem; font-weight:700; color:#818cf8 !important;">{st.session_state.current_user}</p>
        <p style="color:#64748b; font-size:0.88rem; margin-top:4px;">Role: {st.session_state.role}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Terminate Session", use_container_width=True):
        for k in ['authenticated', 'role', 'current_user']:
            st.session_state[k] = None
        st.session_state.authenticated = False
        st.rerun()
    st.stop()

# ── Login Gateway ──
st.markdown("""
<div style="padding: 60px 0 36px 0; text-align: center;">
    <div style="font-size: 2.8rem; font-weight: 800; background: linear-gradient(135deg, #818cf8 0%, #4f46e5 50%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.2;">
        Fair Dispatcher
    </div>
    <div style="color: #64748b; margin-top: 10px; font-size: 0.95rem; letter-spacing: 0.3px;">
        Quantum-Powered Logistics & Driver Equity Platform
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: linear-gradient(145deg, #1a1d27, #141722); border: 1px solid #2d3148; border-radius: 16px; padding: 36px 40px 32px 40px; box-shadow: 0 24px 60px rgba(0,0,0,0.5);">
    <p style="color:#64748b; font-size:0.78rem; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:24px; font-weight:600;">System Authentication</p>
""", unsafe_allow_html=True)

with st.form("login_form"):
    username = st.text_input("Username", placeholder="e.g. admin or alice")
    password = st.text_input("Password", type="password", placeholder="••••••••")
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Sign In →", use_container_width=True)

    if submitted:
        if username.lower() in CREDENTIALS and CREDENTIALS[username.lower()] == password:
            st.session_state.authenticated = True
            if username.lower() == "admin":
                st.session_state.role = "Administrator"
                st.session_state.current_user = "Administrative Root"
            else:
                st.session_state.role = "Driver"
                st.session_state.current_user = username.capitalize()
            with st.spinner("Authenticating..."):
                time.sleep(0.5)
            if st.session_state.role == "Administrator":
                st.switch_page("pages/1_Admin_Command_Center.py")
            else:
                st.switch_page("pages/2_Driver_Portal.py")
        else:
            st.error("Invalid credentials. Access denied.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top: 24px;">
    <p style="color: #334155; font-size: 0.78rem;">Demo credentials: admin / admin123 &nbsp;|&nbsp; alice / driver123</p>
</div>
""", unsafe_allow_html=True)
