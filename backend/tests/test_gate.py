"""The Life gate provider, on a mini app with a fake operator (`/api/people/me`)."""

import pytest
from app import gate
from app.config import settings
from fastapi import FastAPI
from fastapi.testclient import TestClient

ME = {
    "person_id": 7,
    "display_name": "Alice Example",
    "life_role": None,
    "memberships": [{"instance": "acme", "role": "player"}],
    "identities": {"email": "alice@example.com"},
}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    gate._CACHE.clear()
    monkeypatch.setattr(settings, "life_instance", "acme")
    calls: list[str] = []

    async def operator(token: str) -> dict | None:
        calls.append(token)
        return ME if token == "good" else None

    monkeypatch.setattr(gate, "_people_me", operator)
    app = FastAPI()
    gate.mount(app)
    return TestClient(app)


def test_no_token_is_401(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_operator_refusal_is_401(client: TestClient) -> None:
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer bad"}).status_code == 401


def test_member_is_an_editor_with_the_real_identity(client: TestClient) -> None:
    r = client.get("/api/auth/me", headers={"X-Life-Person": "Bearer good"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "alice@example.com" and body["nome"] == "Alice Example"
    assert body["ruoli"] == ["manager"] and body["is_admin"] is False


def test_owner_is_admin(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def operator(token: str) -> dict:
        return {**ME, "life_role": "owner"}

    monkeypatch.setattr(gate, "_people_me", operator)
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer good"})
    assert r.json()["is_admin"] is True


def test_member_of_another_instance_is_403(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "life_instance", "other")
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer good"}).status_code == 403
