import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure workspace root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import database
from app import app


@pytest.fixture(scope="session", autouse=True)
def ensure_database():
    """Ensure the SQLite database exists and is properly seeded."""
    database.init_db(force_reseed=False)
    yield


@pytest.fixture
def client():
    """Provides a FastAPI TestClient instance."""
    return TestClient(app)
