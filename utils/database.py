import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# We remove channel_binding=require if it causes issues, standard sslmode=require is fine for psycopg2
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String) # Storing plaintext for demo brevity, but named hash for standard practice
    role = Column(String)

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(String, primary_key=True)  # e.g., D1, D2
    name = Column(String, unique=True)
    past_workload = Column(Float, default=0.0)
    fatigue_score = Column(Float, default=0.0)
    monthly_tokens = Column(Integer, default=5)
    wage_history = Column(Float, default=0.0)
    vehicle_capacity_kg = Column(Float, default=100.0)

class Route(Base):
    __tablename__ = "routes"
    id = Column(String, primary_key=True) # e.g., R1, R2
    deliveries = Column(Integer)
    weight_kg = Column(Float)
    urgency = Column(String)
    traffic = Column(String)
    distance_km = Column(Float)

class Allocation(Base):
    __tablename__ = "allocations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_name = Column(String)
    route_id = Column(String)
    urgency = Column(String)
    difficulty = Column(String)
    est_wage = Column(Float)

class TokenRequest(Base):
    __tablename__ = "token_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_name = Column(String)
    route_id = Column(String)
    difficulty = Column(String)
    reason = Column(String)
    status = Column(String, default="Pending")

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed Data if Empty
    db = SessionLocal()
    
    # Add root admin if missing
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", password_hash="admin123", role="Administrator"))
        
    drivers_list = [
        ("alice", "driver123", "D1", "Alice", 120, 0.8, 4, 1200, 300),
        ("bob", "driver123", "D2", "Bob", 95, 0.4, 5, 950, 100),
        ("charlie", "driver123", "D3", "Charlie", 110, 0.6, 2, 1100, 400),
        ("david", "driver123", "D4", "David", 85, 0.2, 5, 850, 200)
    ]
    
    for uname, upass, did, dname, wload, fscore, tokens, wage, cap in drivers_list:
        if not db.query(User).filter(User.username == uname).first():
            db.add(User(username=uname, password_hash=upass, role="Driver"))
        if not db.query(Driver).filter(Driver.id == did).first():
            db.add(Driver(id=did, name=dname, past_workload=wload, fatigue_score=fscore, monthly_tokens=tokens, wage_history=wage, vehicle_capacity_kg=cap))
            
    db.commit()

    # Seed Routes
    if db.query(Route).count() == 0:
        routes_data = [
            Route(id="R1", deliveries=45, weight_kg=200, urgency="Normal", traffic="High", distance_km=40),
            Route(id="R2", deliveries=12, weight_kg=50, urgency="Emergency", traffic="Low", distance_km=15),
            Route(id="R3", deliveries=60, weight_kg=300, urgency="Normal", traffic="Medium", distance_km=60),
            Route(id="R4", deliveries=25, weight_kg=100, urgency="Medical", traffic="Low", distance_km=20)
        ]
        db.add_all(routes_data)
        db.commit()

    db.close()

# Helper Data Functions
def get_db_session():
    return SessionLocal()
