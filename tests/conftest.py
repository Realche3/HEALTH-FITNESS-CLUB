"""
Pytest configuration and shared fixtures.

These tests assume:
    - The PostgreSQL database is available.
    - Alembic migrations have been applied (schema is up to date).
"""

import os
import sys

# Ensure project root is on sys.path so "import app" works
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from app.db import SessionLocal


@pytest.fixture(scope="function")
def db_session():
    """
    Provide a database session for direct DB checks inside tests.

    This does not wrap tests in a transaction, so tests will persist data.
    It is suitable for a small academic project where the DB is dedicated.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
