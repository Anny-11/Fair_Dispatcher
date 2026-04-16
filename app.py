import streamlit as st
import time
from utils.state_manager import initialize_system_state, inject_css
from utils.database import get_db_session, User

st.set_page_config(page_title="Fair Dispatcher", page_icon="⚡", layout="centered")
initialize_system_state()
inject_css()

# Extra login-specific overrides for the centered layout
st.markdown("""
<style>
.main .block-container { max-width: 480px !important; padding-top: 5vh !important; }
</style>
""", unsafe_allow_html=True)

# ── Already signed in ──
if st.session_state.get('authenticated'):
    st.markdown(f"""
    <div style="text-align:center;padding:60px 0 32px;">
        <div style="font-size:2rem;font-weight:800;color:#f1f5f9;letter-spacing:-.04em;">Fair Dispatcher</div>
        <div style="font-size:.875rem;color:#475569;margin-top:6px;">Quantum-Powered Logistics Platform</div>
    </div>
    <div style="background:#0f111a;border:1px solid #1c2038;border-radius:14px;padding:28px;text-align:center;margin-bottom:16px;">
        <div style="width:48px;height:48px;background:linear-gradient(135deg,#4f46e5,#818cf8);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.3rem;font-weight:700;color:white;margin:0 auto 14px;">
            {st.session_state.current_user[0].upper()}
        </div>
        <div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;">{st.session_state.current_user}</div>
        <div style="font-size:.78rem;color:#475569;margin-top:4px;text-transform:uppercase;letter-spacing:.08em;">{st.session_state.role}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        for k in ['authenticated', 'role', 'current_user']:
            st.session_state[k] = None
        st.session_state.authenticated = False
        st.rerun()
    st.stop()

# ── Branding ──
st.markdown("""
<div style="text-align:center;padding:40px 0 32px;">
    <div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:20px;">
        <div style="width:36px;height:36px;background:linear-gradient(135deg,#4f46e5,#818cf8);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;">⚡</div>
        <span style="font-size:1.25rem;font-weight:800;color:#f1f5f9;letter-spacing:-.03em;">Fair Dispatcher</span>
    </div>
    <div style="font-size:1.6rem;font-weight:800;color:#f1f5f9;letter-spacing:-.04em;line-height:1.2;margin-bottom:8px;">
        Welcome back
    </div>
    <div style="font-size:.875rem;color:#475569;">Sign in to your dispatch portal.</div>
</div>
""", unsafe_allow_html=True)

# ── Card ──
st.markdown('<div style="background:#0f111a;border:1px solid #1c2038;border-radius:16px;padding:32px;box-shadow:0 20px 60px rgba(0,0,0,.5);">', unsafe_allow_html=True)

tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

with tab_login:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="admin or alice")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Sign In →", use_container_width=True)

    if submitted:
        db = get_db_session()
        user = db.query(User).filter(User.username == username.strip().lower()).first()
        db.close()
        if user and user.password_hash == password:
            st.session_state.authenticated = True
            st.session_state.role = user.role
            st.session_state.current_user = "Administrative Root" if user.role == "Administrator" else username.capitalize()
            with st.spinner("Authenticating…"):
                time.sleep(0.4)
            st.switch_page("pages/1_Admin_Command_Center.py" if user.role == "Administrator" else "pages/2_Driver_Portal.py")
        else:
            st.error("Invalid credentials. Please try again.")

with tab_register:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.form("register_form"):
        new_username = st.text_input("Choose a username")
        new_password = st.text_input("Choose a password", type="password")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        registered = st.form_submit_button("Create Driver Account", use_container_width=True)

    if registered:
        if not new_username or not new_password:
            st.warning("Please fill in both fields.")
        else:
            db = get_db_session()
            if db.query(User).filter(User.username == new_username.strip().lower()).first():
                st.error("Username already exists.")
            else:
                db.add(User(username=new_username.strip().lower(), password_hash=new_password, role="Driver"))
                db.commit()
                st.success("Account created! You can now sign in.")
            db.close()

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;margin-top:24px;">
    <span style="font-size:.75rem;color:#334155;">Demo: &nbsp;<code style="background:#0f111a;padding:2px 6px;border-radius:4px;color:#818cf8;">admin</code> / <code style="background:#0f111a;padding:2px 6px;border-radius:4px;color:#818cf8;">admin123</code>&nbsp;&nbsp;or&nbsp;&nbsp;<code style="background:#0f111a;padding:2px 6px;border-radius:4px;color:#818cf8;">alice</code> / <code style="background:#0f111a;padding:2px 6px;border-radius:4px;color:#818cf8;">driver123</code></span>
</div>
""", unsafe_allow_html=True)
