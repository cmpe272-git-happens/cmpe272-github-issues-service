"""
Shared pytest fixtures for the GitHub Issues Service test suite.

The test configuration:
* provides a reusable FastAPI ``TestClient`` fixture; and
* allows API route tests to interact with the application without starting
  the server separately.

Author: Thanzeel Hassan
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture()
def client():
    return TestClient(app)
