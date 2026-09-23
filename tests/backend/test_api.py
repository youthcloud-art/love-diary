from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def signup(prefix: str):
    email = f"{prefix}-{uuid4().hex[:8]}@example.com"
    result = client.post("/api/v1/auth/register", json={"nickname": prefix, "email": email, "password": "secret123"})
    assert result.status_code == 200, result.text
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_two_person_sync_and_privacy():
    alice, bob = signup("Alice"), signup("Bob")
    created = client.post("/api/v1/spaces", headers=alice, json={"name": "我们"})
    assert created.status_code == 200
    joined = client.post("/api/v1/spaces/join", headers=bob, json={"code": created.json()["invite_code"]})
    assert len(joined.json()["members"]) == 2
    payload = {"title": "今天", "body": "想你", "mood": "甜蜜", "happened_on": "2026-09-23", "visibility": "shared", "media_ids": []}
    assert client.post("/api/v1/entries", headers=alice, json=payload).status_code == 200
    assert client.get("/api/v1/entries", headers=bob).json()[0]["body"] == "想你"
    payload["visibility"] = "private"; payload["body"] = "悄悄话"
    assert client.post("/api/v1/entries", headers=alice, json=payload).status_code == 200
    assert "悄悄话" not in [x["body"] for x in client.get("/api/v1/entries", headers=bob).json()]

