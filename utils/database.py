import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role          = Column(String)

class Driver(Base):
    __tablename__ = "drivers"
    id                  = Column(String, primary_key=True)
    name                = Column(String, unique=True)
    past_workload       = Column(Float, default=0.0)
    fatigue_score       = Column(Float, default=0.0)
    monthly_tokens      = Column(Integer, default=5)
    wage_history        = Column(Float, default=0.0)
    vehicle_capacity_kg = Column(Float, default=100.0)

class Route(Base):
    __tablename__ = "routes"
    id          = Column(String, primary_key=True)
    deliveries  = Column(Integer)
    weight_kg   = Column(Float)
    urgency     = Column(String)
    traffic     = Column(String)
    distance_km = Column(Float)

class Allocation(Base):
    __tablename__ = "allocations"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    driver_name = Column(String)
    route_id    = Column(String)
    urgency     = Column(String)
    difficulty  = Column(String)
    est_wage    = Column(Float)

class TokenRequest(Base):
    __tablename__ = "token_requests"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    driver_name = Column(String)
    route_id    = Column(String)
    difficulty  = Column(String)
    reason      = Column(String)
    status      = Column(String, default="Pending")

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ── Users & Drivers ──
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", password_hash="admin123", role="Administrator"))

    drivers_seed = [
        ("alice",   "driver123", "D1", "Alice",   120, 0.80, 4, 1200, 300),
        ("bob",     "driver123", "D2", "Bob",      95, 0.40, 5,  950, 100),
        ("charlie", "driver123", "D3", "Charlie", 110, 0.60, 2, 1100, 400),
        ("david",   "driver123", "D4", "David",    85, 0.20, 5,  850, 200),
        ("eva",     "driver123", "D5", "Eva",     130, 0.90, 1, 1300, 500),
        ("frank",   "driver123", "D6", "Frank",    70, 0.15, 5,  700, 250),
    ]
    for uname, upass, did, dname, wload, fscore, tokens, wage, cap in drivers_seed:
        if not db.query(User).filter(User.username == uname).first():
            db.add(User(username=uname, password_hash=upass, role="Driver"))
        if not db.query(Driver).filter(Driver.id == did).first():
            db.add(Driver(id=did, name=dname, past_workload=wload, fatigue_score=fscore,
                          monthly_tokens=tokens, wage_history=wage, vehicle_capacity_kg=cap))
    db.commit()

    # ── Routes ── seed only if empty
    if db.query(Route).count() == 0:
        routes_seed = [
            Route(id="R1",  deliveries=45, weight_kg=200, urgency="Normal",    traffic="High",   distance_km=40),
            Route(id="R2",  deliveries=12, weight_kg=50,  urgency="Emergency", traffic="Low",    distance_km=15),
            Route(id="R3",  deliveries=60, weight_kg=300, urgency="Normal",    traffic="Medium", distance_km=60),
            Route(id="R4",  deliveries=25, weight_kg=100, urgency="Medical",   traffic="Low",    distance_km=20),
            Route(id="R5",  deliveries=8,  weight_kg=30,  urgency="Normal",    traffic="Low",    distance_km=10),
            Route(id="R6",  deliveries=55, weight_kg=450, urgency="Emergency", traffic="High",   distance_km=80),
            Route(id="R7",  deliveries=30, weight_kg=150, urgency="Normal",    traffic="Medium", distance_km=35),
            Route(id="R8",  deliveries=18, weight_kg=80,  urgency="Medical",   traffic="High",   distance_km=25),
            Route(id="R9",  deliveries=70, weight_kg=350, urgency="Normal",    traffic="High",   distance_km=90),
            Route(id="R10", deliveries=5,  weight_kg=20,  urgency="Normal",    traffic="Low",    distance_km=8),
        ]
        db.add_all(routes_seed)
        db.commit()

    db.close()

def get_db_session():
    return SessionLocal()

# ── Helpers for Admin "Quick Add" forms ──
def add_route_to_db(route_id, deliveries, weight_kg, urgency, traffic, distance_km):
    db = SessionLocal()
    try:
        existing = db.query(Route).filter(Route.id == route_id).first()
        if existing:
            return False, "Route ID already exists."
        db.add(Route(id=route_id, deliveries=deliveries, weight_kg=weight_kg,
                     urgency=urgency, traffic=traffic, distance_km=distance_km))
        db.commit()
        return True, "Route added."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def add_driver_to_db(driver_id, name, username, password, capacity, fatigue, tokens):
    db = SessionLocal()
    try:
        if db.query(Driver).filter(Driver.id == driver_id).first():
            return False, "Driver ID already exists."
        if db.query(User).filter(User.username == username.lower()).first():
            return False, "Username already taken."
        db.add(User(username=username.lower(), password_hash=password, role="Driver"))
        db.add(Driver(id=driver_id, name=name, past_workload=0, fatigue_score=fatigue,
                      monthly_tokens=tokens, wage_history=0, vehicle_capacity_kg=capacity))
        db.commit()
        return True, "Driver registered."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def delete_route_from_db(route_id):
    db = SessionLocal()
    r = db.query(Route).filter(Route.id == route_id).first()
    if r:
        db.delete(r)
        db.commit()
    db.close()
