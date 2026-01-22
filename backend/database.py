# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ────────────────────────────────────────────────
#   Prefer environment variable (Docker Compose sets this)
#   Fallback only for local development without docker
# ────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cow:cow123@localhost:5432/cryptoshare"   # only used when NOT in Docker
)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()