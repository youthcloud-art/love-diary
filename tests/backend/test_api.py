from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def signup(prefix: str):
    email = f"{prefix}-{uuid4().hex[:8]}@example.com"
    result = client.post("/api/v1/auth/register", json={"nickname": prefix, "email": email, "password": "secret123"})
    assert result.status_code == 200, result.text
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_phone_register_and_two_login_methods():
    phone = f"139{uuid4().int % 100000000:08d}"
    sent = client.post("/api/v1/auth/code", json={"phone": phone})
    assert sent.status_code == 200
    code = sent.json()["dev_code"]
    registered = client.post("/api/v1/auth/phone/register", json={"nickname": "小满", "phone": phone, "code": code, "password": "secret123"})
    assert registered.status_code == 200, registered.text
    assert client.post("/api/v1/auth/phone/login", json={"phone": phone, "password": "secret123"}).status_code == 200
    code = client.post("/api/v1/auth/code", json={"phone": phone}).json()["dev_code"]
    assert client.post("/api/v1/auth/phone/code-login", json={"phone": phone, "code": code}).status_code == 200


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
