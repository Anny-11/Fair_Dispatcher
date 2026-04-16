import streamlit as st
import pandas as pd
from utils.database import init_db, engine, SessionLocal, User, Driver, Route, Allocation, TokenRequest

PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* ── App background ── */
.stApp { background: #0f1117; color: #e2e8f0 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1d27 0%, #12151f 100%) !important;
    border-right: 1px solid #2d3148;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* ── All text override ── */
h1, h2, h3, h4, h5, h6, p, div, span, label { color: #e2e8f0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #1a1d27;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #2d3148;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #94a3b8 !important;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
    font-size: 0.88rem;
    border: none;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: #4f46e5 !important;
    color: white !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #4f46e5 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
}
.stButton > button:hover {
    background: #4338ca !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5) !important;
}

/* ── Input fields ── */
.stTextInput > div > div > input {
    background: #1e2130 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.25) !important;
}
label { color: #94a3b8 !important; font-size: 0.82rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.8px !important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #1a1d27;
    border: 1px solid #2d3148;
    border-radius: 12px;
    padding: 20px 24px !important;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: #4f46e5; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 1px; }
[data-testid="stMetricValue"] { color: #818cf8 !important; font-weight: 700 !important; font-size: 2rem !important; }

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: #1a1d27 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    padding: 14px 18px !important;
}
.streamlit-expanderContent {
    background: #141722 !important;
    border: 1px solid #2d3148 !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 20px !important;
}

/* ── Dataframes ── */
[data-testid="stDataFrame"] {
    border: 1px solid #2d3148 !important;
    border-radius: 10px !important;
    overflow: hidden;
}

/* ── Success/Warning/Error/Info ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 10px !important;
    border: none !important;
    padding: 14px 18px !important;
    font-weight: 500 !important;
}
.stSuccess { background: rgba(16, 185, 129, 0.15) !important; color: #34d399 !important; }
.stInfo { background: rgba(79, 70, 229, 0.12) !important; color: #818cf8 !important; }
.stWarning { background: rgba(245, 158, 11, 0.12) !important; color: #fbbf24 !important; }
.stError { background: rgba(239, 68, 68, 0.12) !important; color: #f87171 !important; }

/* ── Divider ── */
hr { border-color: #2d3148 !important; margin: 28px 0 !important; }

/* ── Spinner ── */
.stSpinner > div { border-color: #4f46e5 !important; }
</style>
"""

def inject_css():
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

def load_data_to_session():
    # Helper to sync NeonDB to Pandas for fast Streamlit UI rendering
    db = SessionLocal()
    st.session_state.drivers = pd.read_sql("SELECT id as \"Driver_ID\", name as \"Name\", past_workload as \"Past_Workload\", fatigue_score as \"Fatigue_Score\", monthly_tokens as \"Monthly_Tokens\", wage_history as \"Wage_History\", vehicle_capacity_kg as \"Vehicle_Capacity_kg\" FROM drivers", engine)
    st.session_state.routes = pd.read_sql("SELECT id as \"Route_ID\", deliveries as \"Deliveries\", weight_kg as \"Weight_kg\", urgency as \"Urgency\", traffic as \"Traffic\", distance_km as \"Distance_km\" FROM routes", engine)
    st.session_state.allocations = pd.read_sql("SELECT driver_name as \"Driver\", route_id as \"Route_ID\", urgency as \"Urgency\", difficulty as \"Difficulty\", est_wage as \"Est_Wage ($)\" FROM allocations", engine)
    
    # Load raw dict for tokens
    reqs = db.query(TokenRequest).all()
    st.session_state.token_requests = [{"id": r.id, "driver": r.driver_name, "current_route": r.route_id, "difficulty": r.difficulty, "reason": r.reason, "status": r.status} for r in reqs]
    db.close()

def save_drivers_to_db(df):
    db = SessionLocal()
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
    db.close()

def save_routes_to_db(df):
    db = SessionLocal()
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
    db.close()

def save_allocations_to_db(df):
    db = SessionLocal()
    db.query(Allocation).delete() # Clear old QAOA run
    alloc_list = []
    for _, row in df.iterrows():
        alloc = Allocation(
            driver_name=row['Driver'],
            route_id=row['Route_ID'],
            urgency=row['Urgency'],
            difficulty=row['Difficulty'],
            est_wage=float(row['Est_Wage ($)'])
        )
        alloc_list.append(alloc)
    db.add_all(alloc_list)
    db.commit()
    db.close()

def initialize_system_state():
    try:
        init_db() # Ensure tables exist
    except Exception as e:
        print(f"DB Init Error: {e}")

    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if 'role' not in st.session_state: st.session_state.role = None
    if 'current_user' not in st.session_state: st.session_state.current_user = None

    try:
        load_data_to_session()
    except Exception as e:
        print(f"Data Load Error: {e}")

def classify_route(row):
    score = sum([
        2 if row['Deliveries'] > 40 else 1 if row['Deliveries'] > 20 else 0,
        2 if row['Weight_kg'] > 150 else 0,
        2 if row['Traffic'] == 'High' else 0,
        3 if row['Urgency'] in ['Emergency', 'Medical'] else 0
    ])
    return "HIGH" if score >= 5 else "MEDIUM" if score >= 3 else "LOW"

def style_difficulty(val):
    colors = {'HIGH': '#f87171', 'MEDIUM': '#fbbf24', 'LOW': '#34d399'}
    return f'color: {colors.get(val, "#94a3b8")}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'
