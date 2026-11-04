"""Shared test setup: demo mode (no API key) and a fresh temporary database per test."""
import os

# Must be set before the app is imported, so a real key in .env is never used in tests.
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

TEST_USERNAME = "tester"
TEST_EMAIL = "tester@example.com"
TEST_PASSWORD = "secret123"


def _make_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from app.main import app

    return TestClient(app)


@pytest.fixture()
def anon_client(tmp_path, monkeypatch):
    """A client that is NOT logged in."""
    with _make_client(tmp_path, monkeypatch) as test_client:
        yield test_client


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A client already signed up and logged in as the test user."""
    with _make_client(tmp_path, monkeypatch) as test_client:
        response = test_client.post(
            "/api/auth/register",
            json={
                "username": TEST_USERNAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 201, response.text
        test_client.headers["Authorization"] = f"Bearer {response.json()['token']}"
        yield test_client


@pytest.fixture()
def setup_payload() -> dict:
    return {
        "role": "Software Engineer",
        "domain": "Python Backend",
        "experience_level": "Fresher",
        "interview_type": "Technical",
        "num_questions": 3,
    }