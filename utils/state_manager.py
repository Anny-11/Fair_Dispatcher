import streamlit as st
import pandas as pd

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

CREDENTIALS = {
    "admin": "admin123",
    "alice": "driver123",
    "bob": "driver123",
    "charlie": "driver123",
    "david": "driver123"
}

def inject_css():
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

def initialize_system_state():
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if 'role' not in st.session_state: st.session_state.role = None
    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'token_requests' not in st.session_state: st.session_state.token_requests = []
    if 'requesting_token' not in st.session_state: st.session_state.requesting_token = False

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
