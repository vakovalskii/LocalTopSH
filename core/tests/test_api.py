"""Tests for Core API endpoints"""

import pytest
import httpx

BASE = "http://localhost:4000"
TEST_USER = 999999
TEST_CHAT = 999999


@pytest.fixture(scope="module")
def client():
    """HTTP client for API calls"""
    with httpx.Client(base_url=BASE, timeout=30) as c:
        yield c


# ============ Health ============

def test_health(client):
    """GET /health returns ok"""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "core"


# ============ Clear ============

def test_clear_session(client):
    """POST /api/clear resets session"""
    r = client.post("/api/clear", json={
        "user_id": TEST_USER,
        "chat_id": TEST_CHAT,
    })
    assert r.status_code == 200
    assert r.json()["status"] == "cleared"


# ============ Chat ============

def test_chat_simple(client):
    """POST /api/chat returns a response"""
    # Clear first
    client.post("/api/clear", json={"user_id": TEST_USER, "chat_id": TEST_CHAT})
    
    r = client.post("/api/chat", json={
        "user_id": TEST_USER,
        "chat_id": TEST_CHAT,
        "message": "Say exactly: PONG",
        "username": "tester",
        "chat_type": "private",
        "source": "bot",
    }, timeout=120)
    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    assert len(data["response"]) > 0


def test_chat_missing_fields(client):
    """POST /api/chat with missing required fields"""
    r = client.post("/api/chat", json={
        "user_id": TEST_USER,
        "chat_id": TEST_CHAT,
        "message": "",
    }, timeout=60)
    assert r.status_code == 200  # Should not crash


def test_chat_different_sources(client):
    """Both bot and userbot sources work"""
    for source in ["bot", "userbot"]:
        r = client.post("/api/chat", json={
            "user_id": TEST_USER,
            "chat_id": TEST_CHAT,
            "message": "ping",
            "source": source,
        }, timeout=120)
        assert r.status_code == 200
