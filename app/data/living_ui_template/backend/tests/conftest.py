"""
Test configuration for Living UI backend tests.

Provides a temporary in-memory SQLite database and a FastAPI test client.
All tests run against a fresh database — the real database is never touched.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path so imports work
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from models import Base
from database import get_db
from main import app


# Create a temporary in-memory database for testing
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    """Override the database dependency to use the test database."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the real database with the test database
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db():
    """Provide a database session for direct DB operations in tests."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
