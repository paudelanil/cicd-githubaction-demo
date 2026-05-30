"""Tests for the support-ticket API.

Each test uses a fresh TestClient and clears the in-memory store so
flipping one assertion produces a clean, localized failure in CI —
useful for the live "break it / fix it" demo.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import support


@pytest.fixture(autouse=True)
def _reset_store():
    support._tickets.clear()
    yield
    support._tickets.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_ticket_returns_open_ticket(client: TestClient) -> None:
    response = client.post(
        "/tickets",
        json={"subject": "login broken", "message": "cannot sign in", "priority": "high"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["subject"] == "login broken"
    assert body["priority"] == "high"
    assert body["status"] == "open"


def test_priority_defaults_to_normal(client: TestClient) -> None:
    response = client.post("/tickets", json={"subject": "s", "message": "m"})
    assert response.status_code == 201
    assert response.json()["priority"] == "normal"


def test_list_tickets_returns_in_id_order(client: TestClient) -> None:
    for subject in ["first", "second", "third"]:
        client.post("/tickets", json={"subject": subject, "message": "m"})

    response = client.get("/tickets")
    assert response.status_code == 200
    subjects = [t["subject"] for t in response.json()]
    assert subjects == ["first", "second", "third"]


def test_get_missing_ticket_returns_404(client: TestClient) -> None:
    response = client.get("/tickets/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "ticket not found"


def test_close_ticket_flips_status(client: TestClient) -> None:
    created = client.post("/tickets", json={"subject": "s", "message": "m"}).json()

    closed = client.post(f"/tickets/{created['id']}/close")
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    fetched = client.get(f"/tickets/{created['id']}")
    assert fetched.json()["status"] == "closed"


def test_close_missing_ticket_returns_404(client: TestClient) -> None:
    response = client.post("/tickets/999/close")
    assert response.status_code == 404


def test_subject_cannot_be_empty(client: TestClient) -> None:
    response = client.post("/tickets", json={"subject": "", "message": "m"})
    assert response.status_code == 422
