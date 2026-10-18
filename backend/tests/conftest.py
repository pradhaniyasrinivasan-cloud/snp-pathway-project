"""
Shared pytest fixtures.

Each test gets its own fresh SQLite file (created in a pytest tmp_path),
seeded with the same demo data the app ships with. This keeps tests
isolated from each other and from whatever database a developer might
already have sitting in backend/app/database/snp_pathway.db.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db import Base
from app.database.seed_demo_data import (
    load_json, seed_proteins, seed_pathway, seed_variants,
    VARIANTS_JSON, MAPK_JSON,
)


@pytest.fixture()
def db_session(tmp_path):
    """A fresh, seeded database session, torn down after the test."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    session = TestSessionLocal()
    variants_data = load_json(VARIANTS_JSON)
    mapk_data = load_json(MAPK_JSON)
    seed_proteins(session, variants_data)
    seed_pathway(session, mapk_data)
    seed_variants(session, variants_data)

    yield session

    session.close()
    engine.dispose()


@pytest.fixture()
def api_client(db_session):
    """A FastAPI TestClient wired to the same seeded test database."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database.db import get_db

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
