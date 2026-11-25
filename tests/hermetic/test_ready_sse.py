"""Tests for Phase 19.2 (G13): /ready endpoint & SSE client disconnect."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.testclient import TestClient

from src.api.routers.agent.routes_agent import _sse_generator_with_disconnect
from src.api.models.schemas import ChatRequest
from src.domain.authz.access_context import AccessContext
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ── GET /ready Tests ──────────────────────────────────────────────────────────


def test_ready_endpoint_all_ok(monkeypatch, client):
    """Khi Postgres ok (hoặc disabled/ok), Qdrant ok/skipped, LLM ok -> 200 ready=true."""
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_postgres", lambda: ("ok", None))
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_qdrant", lambda: ("skipped", None))
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_llm", lambda: ("ok", None))

    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["checks"]["postgres"] == "ok"
    assert data["checks"]["qdrant"] == "skipped"
    assert data["checks"]["llm"] == "ok"

    # Cũng test alias /api/ready
    resp_api = client.get("/api/ready")
    assert resp_api.status_code == 200
    assert resp_api.json()["ready"] is True


def test_ready_endpoint_db_failed(monkeypatch, client):
    """Khi Postgres fail -> 503 ready=false."""
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_postgres", lambda: ("failed", "Connection refused"))
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_qdrant", lambda: ("ok", None))
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_llm", lambda: ("ok", None))

    resp = client.get("/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["ready"] is False
    assert data["checks"]["postgres"] == "failed"
    assert "details" in data
    assert "Connection refused" in data["details"]["postgres"]


def test_ready_endpoint_llm_failed(monkeypatch, client):
    """Khi LLM config fail -> 503 ready=false."""
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_postgres", lambda: ("ok", None))
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_qdrant", lambda: ("ok", None))
    monkeypatch.setattr("src.api.routers.web_backend.routes_meta._check_llm", lambda: ("failed", "Missing API key"))

    resp = client.get("/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["ready"] is False
    assert data["checks"]["llm"] == "failed"


def test_ready_endpoint_checks_postgres_real_logic(monkeypatch):
    """Kiểm tra logic thực của _check_postgres khi tắt và bật."""
    from src.api.routers.web_backend.routes_meta import _check_postgres

    monkeypatch.setattr("src.shared.settings.settings.agent_db_host", "")
    st, err = _check_postgres()
    assert st == "skipped"
    assert err is None

    monkeypatch.setattr("src.shared.settings.settings.agent_db_host", "127.0.0.1")
    monkeypatch.setattr("src.shared.settings.settings.agent_db_user", "test_user")
    monkeypatch.setattr("src.shared.settings.settings.agent_db_password", "test_pass")
    with patch("psycopg2.connect", side_effect=Exception("DB down")):
        st, err = _check_postgres()
        assert st == "failed"
        assert "DB down" in err


def test_ready_endpoint_checks_qdrant_real_logic(monkeypatch):
    """Kiểm tra logic thực của _check_qdrant khi tắt và bật."""
    from src.api.routers.web_backend.routes_meta import _check_qdrant

    monkeypatch.setattr("src.shared.settings.settings.memory_long_term_enabled", False)
    monkeypatch.setattr("src.shared.settings.settings.qdrant_url", "")
    st, err = _check_qdrant()
    assert st == "skipped"
    assert err is None

    monkeypatch.setattr("src.shared.settings.settings.memory_long_term_enabled", True)
    monkeypatch.setattr("src.shared.settings.settings.memory_enabled", True)
    monkeypatch.setattr("src.shared.settings.settings.qdrant_url", "http://fake-qdrant:6333")
    with patch("src.infra.memory.longterm.get_qdrant_client", side_effect=Exception("Qdrant down")):
        st, err = _check_qdrant()
        assert st == "failed"
        assert "Qdrant down" in err


# ── SSE Disconnect Tests ──────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_sse_disconnect_cancels_generator_and_logs(caplog):
    """Khi client disconnect, generator dừng ngay lập tức và ghi log sse_client_disconnected."""
    import logging

    req = ChatRequest(
        question="Hello test question",
        session_id="test_sess_disc",
        user_id="test_user_disc",
    )
    access = AccessContext(user_id="test_user_disc", effective_org_id=1, role_group="ALL")

    # Fake request với is_disconnected()
    disconnected_flag = False

    class FakeRequest:
        async def is_disconnected(self) -> bool:
            return disconnected_flag

    fake_req = FakeRequest()

    def fake_frames():
        for i in range(10):
            yield f"data: frame_{i}\n\n"

    # Giả lập turn service trả về generator phát 10 frames
    with patch("src.api.routers.agent.routes_agent._turn.stream_sse_frames", return_value=fake_frames()):
        with caplog.at_level(logging.INFO):
            gen = _sse_generator_with_disconnect(req, fake_req, access, "test_user_disc")

            # Frame 0 bình thường
            f0 = await gen.__anext__()
            assert "frame_0" in f0

            # Giả lập client ngắt kết nối (đóng tab)
            disconnected_flag = True

            # Lần next tiếp theo phát hiện is_disconnected -> break -> StopAsyncIteration
            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()

            assert "sse_client_disconnected" in caplog.text
            assert "session_id=test_sess_disc" in caplog.text


def test_api_agent_stream_normal_flow_integration(monkeypatch, client):
    """Đảm bảo /api/agent/stream với async generator wrapper vẫn hoạt động bình thường qua TestClient."""
    def fake_frames(req, *, access, user_id, **kwargs):
        yield 'data: {"node": "cache", "output": "Test answer"}\n\n'
        yield 'data: {"complete": true, "answer": "Test answer"}\n\n'

    monkeypatch.setattr("src.api.routers.agent.routes_agent._turn.stream_sse_frames", fake_frames)

    resp = client.post(
        "/api/agent/stream",
        json={
            "question": "Kiểm tra hệ thống",
            "session_id": "test_normal_sess",
            "user_id": "test_normal_user",
        },
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "Test answer" in resp.text
