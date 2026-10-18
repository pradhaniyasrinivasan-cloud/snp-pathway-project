"""
Database connection setup.

We use SQLite for the MVP - it's a single file on disk, needs no server,
and is perfectly fine for a project of this size. If we ever need to swap
to Postgres, only this file needs to change (SQLAlchemy handles the rest).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The .db file will be created in backend/app/database/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "snp_pathway.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False is needed because FastAPI can use the connection
# across different threads (SQLite is single-threaded by default).
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this Base class.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency: gives each request its own DB session,
    and always closes it afterwards, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
