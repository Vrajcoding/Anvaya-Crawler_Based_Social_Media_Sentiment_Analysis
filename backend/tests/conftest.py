# conftest.py – shared fixtures for pytest
import os
import pytest
from fastapi.testclient import TestClient

# Disable real crawler during tests
os.environ.setdefault("USE_REAL_CRAWLER", "false")

# Import the FastAPI app from the project package
from backend.main import app as fastapi_app

@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a TestClient for the FastAPI application.
    Scoped to the whole test session to avoid repeated startup overhead.
    """
    return TestClient(fastapi_app)

@pytest.fixture(autouse=True)
def disable_background_tasks(monkeypatch):
    """Patch background_crawler_loop to a no‑op for the duration of tests."""
    monkeypatch.setattr('backend.main.background_crawler_loop', lambda: None)
