import streamlit as st
import pandas as pd
from utils.database import init_db, engine, SessionLocal, User, Driver, Route, Allocation, TokenRequest

# ══════════════════════════════════════════════════
#   PREMIUM CSS — Inspired by Linear.app + Vercel
# ══════════════════════════════════════════════════
PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"], .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }

/* ── CORE BACKGROUND ── */
.stApp { background: #080a12 !important; }
.main .block-container { padding: 0 2rem 2rem 2rem !important; max-width: 1280px !important; }

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0c0e1a !important;
    border-right: 1px solid #1c2038 !important;
    width: 240px !important;
}
[data-testid="stSidebar"] .block-container { padding: 0 !important; }
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] strong { color: #e2e8f0 !important; }

/* ── GLOBAL TEXT ── */
h1, h2, h3, h4, h5, h6 { color: #f1f5f9 !important; font-weight: 700 !important; letter-spacing: -0.02em; }
p, div, span, li { color: #94a3b8 !important; }
label { color: #64748b !important; font-size: 0.75rem !important; font-weight: 500 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1c2038 !important;
    gap: 0 !important;
    padding: 0 !important;
    border-radius: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-radius: 0 !important;
    padding: 12px 20px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    transition: color 0.15s ease, border-color 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #c7d2fe !important; }
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #818cf8 !important;
    border-bottom: 2px solid #818cf8 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: #4f46e5 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 9px 18px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: -0.01em !important;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s !important;
    box-shadow: 0 0 0 1px rgba(79,70,229,0.5), 0 4px 12px rgba(79,70,229,0.3) !important;
}
.stButton > button:hover {
    background: #4338ca !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 0 0 1px rgba(79,70,229,0.7), 0 8px 20px rgba(79,70,229,0.4) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── FORM / INPUT ── */
[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.stTextInput > div > div { background: transparent !important; }
.stTextInput > div > div > input {
    background: #0f111a !important;
    border: 1px solid #1c2038 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    padding: 10px 14px !important;
    font-size: 0.875rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.2) !important;
    outline: none !important;
}
.stTextArea textarea {
    background: #0f111a !important;
    border: 1px solid #1c2038 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.875rem !important;
}
.stTextArea textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.2) !important;
}

/* ── DATA EDITOR ── */
.stDataEditor { border: 1px solid #1c2038 !important; border-radius: 10px !important; overflow: hidden !important; }

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: #0f111a !important;
    border: 1px solid #1c2038 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    position: relative !important;
    overflow: hidden !important;
    transition: border-color 0.2s !important;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #4f46e5, #818cf8);
    border-radius: 12px 12px 0 0;
}
[data-testid="metric-container"]:hover { border-color: #4f46e5 !important; }
[data-testid="stMetricLabel"] > div { color: #64748b !important; font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
[data-testid="stMetricValue"] > div { color: #6366f1 !important; font-size: 1.9rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; }
[data-testid="stMetricDelta"] { color: #34d399 !important; font-size: 0.8rem !important; }

/* ── EXPANDERS ── */
details[data-testid="stExpander"] {
    background: #0f111a !important;
    border: 1px solid #1c2038 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    margin-bottom: 12px !important;
}
details[data-testid="stExpander"] > summary {
    padding: 16px 20px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    color: #e2e8f0 !important;
    cursor: pointer !important;
    list-style: none !important;
    border-radius: 12px !important;
    transition: background 0.15s !important;
}
details[data-testid="stExpander"] > summary:hover { background: #13172a !important; }
details[data-testid="stExpander"] > div { padding: 0 20px 20px !important; }

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-width: 1px !important;
    padding: 12px 16px !important;
    font-size: 0.875rem !important;
}
.stSuccess { background: rgba(16,185,129,0.08) !important; border-color: rgba(16,185,129,0.3) !important; color: #34d399 !important; }
.stInfo    { background: rgba(99,102,241,0.08) !important; border-color: rgba(99,102,241,0.3) !important; color: #818cf8 !important; }
.stWarning { background: rgba(245,158,11,0.08) !important; border-color: rgba(245,158,11,0.3) !important; color: #fbbf24 !important; }
.stError   { background: rgba(239,68,68,0.08)  !important; border-color: rgba(239,68,68,0.3)  !important; color: #f87171 !important; }

/* ── Select / Multiselect ── */
[data-baseweb="select"] > div { background: #0f111a !important; border-color: #1c2038 !important; border-radius: 8px !important; }

/* ── Checkbox ── */
[data-testid="stCheckbox"] label { color: #94a3b8 !important; font-size: 0.9rem !important; }

/* ── Divider ── */
hr { border-color: #1c2038 !important; margin: 24px 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0c0e1a; }
::-webkit-scrollbar-thumb { background: #1c2038; border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: #4f46e5; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #4f46e5 !important; }

/* ── Code block ── */
.stCode { background: #0a0c18 !important; border: 1px solid #1c2038 !important; border-radius: 8px !important; font-size: 0.78rem !important; }

/* ── Sidebar nav links ── */
[data-testid="stSidebarNavItems"] a {
    color: #64748b !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    transition: background 0.15s, color 0.15s !important;
}
[data-testid="stSidebarNavItems"] a:hover { background: #13172a !important; color: #c7d2fe !important; }
[data-testid="stSidebarNavItems"] [aria-current="page"] {
    background: #13172a !important; color: #818cf8 !important;
}
</style>
"""

def inject_css():
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

def kpi_card(label, value, sub="", color="#6366f1"):
    return f"""
    <div style="background:#0f111a; border:1px solid #1c2038; border-radius:12px; padding:20px 22px; position:relative; overflow:hidden; transition:border-color .2s; cursor:default;">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{color},{color}88);"></div>
      <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:.1em;color:#64748b;font-weight:600;margin-bottom:10px;">{label}</div>
      <div style="font-size:2rem;font-weight:800;color:{color};letter-spacing:-.04em;">{value}</div>
      <div style="font-size:0.78rem;color:#475569;margin-top:5px;">{sub}</div>
    </div>"""

def badge(text, kind="default"):
    palette = {
        "HIGH":    ("#f87171","rgba(239,68,68,.12)","rgba(239,68,68,.25)"),
        "MEDIUM":  ("#fbbf24","rgba(245,158,11,.12)","rgba(245,158,11,.25)"),
        "LOW":     ("#34d399","rgba(16,185,129,.12)","rgba(16,185,129,.25)"),
        "Pending": ("#818cf8","rgba(99,102,241,.12)", "rgba(99,102,241,.25)"),
        "Approved":("#34d399","rgba(16,185,129,.12)","rgba(16,185,129,.25)"),
        "Denied":  ("#f87171","rgba(239,68,68,.12)","rgba(239,68,68,.25)"),
    }
    c, bg, border = palette.get(text, ("#94a3b8","rgba(148,163,184,.1)","rgba(148,163,184,.2)"))
    return f'<span style="background:{bg};border:1px solid {border};color:{c};border-radius:6px;padding:3px 10px;font-size:.72rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;">{text}</span>'

def section_header(title, subtitle=""):
    sub_html = f'<p style="color:#475569;font-size:.875rem;margin-top:4px;">{subtitle}</p>' if subtitle else ""
    return f'<div style="margin-bottom:24px;"><h2 style="font-size:1.4rem;font-weight:700;color:#f1f5f9;letter-spacing:-.02em;">{title}</h2>{sub_html}</div>'

def card(content_html, padding="24px"):
    return f'<div style="background:#0f111a;border:1px solid #1c2038;border-radius:12px;padding:{padding};">{content_html}</div>'

def load_data_to_session():
    db = SessionLocal()
    try:
        st.session_state.drivers = pd.read_sql(
            'SELECT id as "Driver_ID", name as "Name", past_workload as "Past_Workload", '
            'fatigue_score as "Fatigue_Score", monthly_tokens as "Monthly_Tokens", '
            'wage_history as "Wage_History", vehicle_capacity_kg as "Vehicle_Capacity_kg" FROM drivers', engine)
        st.session_state.routes = pd.read_sql(
            'SELECT id as "Route_ID", deliveries as "Deliveries", weight_kg as "Weight_kg", '
            'urgency as "Urgency", traffic as "Traffic", distance_km as "Distance_km" FROM routes', engine)
        try:
            st.session_state.allocations = pd.read_sql(
                'SELECT driver_name as "Driver", route_id as "Route_ID", urgency as "Urgency", '
                'difficulty as "Difficulty", est_wage as "Est_Wage ($)" FROM allocations', engine)
        except Exception:
            st.session_state.allocations = pd.DataFrame()

        reqs = db.query(TokenRequest).all()
        st.session_state.token_requests = [
            {"id": r.id, "driver": r.driver_name, "current_route": r.route_id,
             "difficulty": r.difficulty, "reason": r.reason, "status": r.status}
            for r in reqs]
    finally:
        db.close()

def save_drivers_to_db(df):
    db = SessionLocal()
    try:
        for _, row in df.iterrows():
            driver = db.query(Driver).filter(Driver.id == row['Driver_ID']).first()
            if not driver:
                driver = Driver(id=row['Driver_ID'], name=row['Name'])
                db.add(driver)
            driver.past_workload = float(row['Past_Workload'])
            driver.fatigue_score = float(row['Fatigue_Score'])
            driver.monthly_tokens = int(row['Monthly_Tokens'])
            driver.wage_history = float(row['Wage_History'])
            driver.vehicle_capacity_kg = float(row['Vehicle_Capacity_kg'])
        db.commit()
    finally:
        db.close()

def save_routes_to_db(df):
    db = SessionLocal()
    try:
        for _, row in df.iterrows():
            route = db.query(Route).filter(Route.id == row['Route_ID']).first()
            if not route:
                route = Route(id=row['Route_ID'])
                db.add(route)
            route.deliveries = int(row['Deliveries'])
            route.weight_kg = float(row['Weight_kg'])
            route.urgency = row['Urgency']
            route.traffic = row['Traffic']
            route.distance_km = float(row['Distance_km'])
        db.commit()
    finally:
        db.close()

def save_allocations_to_db(df):
    db = SessionLocal()
    try:
        db.query(Allocation).delete()
        for _, row in df.iterrows():
            db.add(Allocation(driver_name=row['Driver'], route_id=row['Route_ID'],
                              urgency=row['Urgency'], difficulty=row['Difficulty'],
                              est_wage=float(row['Est_Wage ($)'])))
        db.commit()
    finally:
        db.close()

def initialize_system_state():
    try:
        init_db()
    except Exception as e:
        st.error(f"DB Init: {e}")
    for k, v in [('authenticated', False), ('role', None), ('current_user', None),
                 ('requesting_token', False)]:
        if k not in st.session_state:
            st.session_state[k] = v
    try:
        load_data_to_session()
    except Exception as e:
        print(f"Data load err: {e}")

def classify_route(row):
    score = sum([
        2 if row['Deliveries'] > 40 else 1 if row['Deliveries'] > 20 else 0,
        2 if row['Weight_kg'] > 150 else 0,
        2 if row['Traffic'] == 'High' else 0,
        3 if row['Urgency'] in ['Emergency', 'Medical'] else 0
    ])
    return "HIGH" if score >= 5 else "MEDIUM" if score >= 3 else "LOW"

def style_difficulty(val):
    c = {'HIGH': '#f87171', 'MEDIUM': '#fbbf24', 'LOW': '#34d399'}
    return f'color:{c.get(val,"#94a3b8")};font-weight:700;text-transform:uppercase;letter-spacing:.05em;'
