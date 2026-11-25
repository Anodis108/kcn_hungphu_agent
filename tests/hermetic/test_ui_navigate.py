"""Unit tests for Phase 19.8 — Deep-link UI Navigation (ui_navigate).

Coverage per test plan:
1. Whitelist path loaded from config/ui_navigate.yaml.
2. Filters (date range, area, device, plate...) build & URL-encode query string properly.
3. Unknown path (outside whitelist) is dropped (returns None / not emitted).
4. Domain queries resolve to appropriate whitelisted paths and filters.
5. SSE streaming yields both dedicated ui_navigate event and ui_navigate field in final payload.
6. Old SSE events remain intact and parseable without breaking changes.
7. Frontend static files contain UI navigate button ("Mở trang") and whitelist enforcement.
"""

from __future__ import annotations

import json
from pathlib import Path
import urllib.parse
import pytest

from src.domain.agents.ui_navigate import (
    DEFAULT_WHITELIST_PATHS,
    build_query_string,
    build_ui_navigate,
    extract_filters_from_question_or_state,
    is_whitelisted_path,
    load_whitelist_paths,
    normalize_path,
    resolve_ui_navigate,
)
from src.application.agent_turn import AgentTurnService, TurnInput, _detail_from_out
from src.domain.agents.state import Agent_Output


def test_whitelist_paths_loaded_from_config():
    """Whitelist path được load từ file config và chuẩn hóa đúng cách."""
    paths = load_whitelist_paths()
    assert "/dashboard" in paths
    assert "/dashboard/traffic" in paths
    assert "/devices" in paths
    assert "/security/intrusion" in paths
    assert "/reports" in paths

    # Kiểm tra chuẩn hóa
    assert normalize_path("dashboard/traffic") == "/dashboard/traffic"
    assert normalize_path("/devices/") == "/devices"
    assert normalize_path("   /zones   ") == "/zones"

    # is_whitelisted_path
    assert is_whitelisted_path("/dashboard/traffic") is True
    assert is_whitelisted_path("/devices") is True
    assert is_whitelisted_path("/unknown/admin/panel") is False
    assert is_whitelisted_path("http://evil.com/hack") is False


def test_filters_to_query_encoding():
    """Filters (date range, area, device, plate...) được encode query string chuẩn xác."""
    filters = {
        "start_date": "04/09/2026",
        "end_date": "16/09/2026",
        "area": "Khu Công Nghiệp Hưng Phú",
        "device": "cam_gate_01",
        "direction": "IN",
        "empty_key": "",
        "none_key": None,
    }

    query_str = build_query_string(filters)
    assert query_str != ""

    # Parse ngược lại để kiểm tra
    parsed = urllib.parse.parse_qs(query_str)
    assert parsed["start_date"] == ["04/09/2026"]
    assert parsed["end_date"] == ["16/09/2026"]
    assert parsed["area"] == ["Khu Công Nghiệp Hưng Phú"]
    assert parsed["device"] == ["cam_gate_01"]
    assert parsed["direction"] == ["IN"]
    assert "empty_key" not in parsed
    assert "none_key" not in parsed

    # Ký tự có dấu tiếng Việt phải được URL-encoded
    assert "%20" in query_str or "+" in query_str


def test_unknown_path_dropped():
    """Path lạ ngoài whitelist tuyệt đối không được emit (trả về None)."""
    filters = {"start_date": "2026-11-23", "area": "Zone A"}

    # Path lạ
    assert build_ui_navigate("/unknown/route", filters) is None
    assert build_ui_navigate("/etc/passwd", filters) is None
    assert build_ui_navigate("https://attacker.site", filters) is None
    assert build_ui_navigate("../secret", filters) is None

    # Path hợp lệ
    nav = build_ui_navigate("/dashboard/traffic", filters)
    assert nav is not None
    assert nav["path"] == "/dashboard/traffic"
    assert "start_date=2026-11-23" in nav["query"]


def test_resolve_ui_navigate_from_question():
    """Tự động phân giải câu hỏi nghiệp vụ ra path và filter phù hợp."""
    # 1. Câu hỏi lưu lượng xe
    q1 = "Hôm nay có bao nhiêu lượt xe vào cổng số 1?"
    nav1 = resolve_ui_navigate(q1)
    assert nav1 is not None
    assert nav1["path"] == "/dashboard/traffic"
    assert "direction=IN" in nav1["query"]
    assert "date_range=today" in nav1["query"]

    # 2. Câu hỏi thiết bị / camera
    q2 = "Làm sao đăng nhập AIOC để mở trang quản lý camera /devices?"
    nav2 = resolve_ui_navigate(q2)
    assert nav2 is not None
    assert nav2["path"] == "/devices"

    # 3. Câu hỏi xâm nhập khu vực
    q3 = "Trong khoảng 04/09/2026 đến 16/09/2026 có bao nhiêu vụ xâm nhập vùng cấm?"
    nav3 = resolve_ui_navigate(q3)
    assert nav3 is not None
    assert nav3["path"] == "/security/intrusion"
    assert "start_date=04%2F09%2F2026" in nav3["query"] or "start_date=04/09/2026" in urllib.parse.unquote(nav3["query"])

    # 4. Câu hỏi không liên quan điều hướng
    q4 = "Xin chào bạn, bạn tên là gì?"
    nav4 = resolve_ui_navigate(q4)
    assert nav4 is None


def test_agent_output_detail_and_sse_field():
    """Agent_Output chứa ui_navigate và _detail_from_out map đúng."""
    nav_data = {"path": "/dashboard/traffic", "query": "direction=IN"}
    out = Agent_Output(
        question="Hôm nay có bao nhiêu lượt xe vào?",
        answer="Có 150 xe vào hôm nay.",
        detail="query_data",
        ui_navigate=nav_data,
    )
    detail = _detail_from_out(out)
    assert "ui_navigate" in detail
    assert detail["ui_navigate"] == nav_data


def test_sse_stream_ui_navigate_event_and_old_events(monkeypatch):
    """SSE stream phát event mới 'ui_navigate' và field 'ui_navigate' trong payload cuối, giữ nguyên SSE cũ."""
    service = AgentTurnService()

    # Mock DB storage khi chạy offline unit test
    monkeypatch.setattr("src.application.agent_turn.persist_session_turn", lambda **_: None)
    monkeypatch.setattr("src.application.agent_turn.store_turn_cache", lambda *_, **__: None)

    # Mock run_agent_stream để kiểm tra luồng SSE frames
    from unittest.mock import patch

    mock_nav = {"path": "/dashboard/traffic", "query": "direction=IN&date_range=today"}
    mock_final_result = Agent_Output(
        question="Xe vào hôm nay?",
        answer="Có 100 xe vào.",
        detail="query_data",
        ui_navigate=mock_nav,
    )

    mock_events = [
        {"node_id": "__answer__", "status": "chunk", "delta": "Có 100 xe"},
        {"node_id": "__answer__", "status": "chunk", "delta": " vào."},
        {"__final_result__": mock_final_result},
    ]

    with patch("src.main.run_agent_stream", return_value=iter(mock_events)):
        from src.api.models.schemas import ChatRequest

        req = ChatRequest(question="Xe vào hôm nay?", user_id="test_user", session_id="test_sess")
        sse_frames = list(service.stream_sse_frames(req, access=None, user_id="test_user"))

    # Kiểm tra các frame SSE
    parsed_events = []
    for frame in sse_frames:
        if frame.startswith("data: "):
            raw = frame[6:].strip()
            if raw and raw != "[DONE]":
                parsed_events.append(json.loads(raw))

    # 1. Có event mới node_id: ui_navigate
    nav_events = [e for e in parsed_events if e.get("node_id") == "ui_navigate"]
    assert len(nav_events) == 1
    assert nav_events[0]["ui_navigate"] == mock_nav

    # 2. Final event __answer__ chứa field ui_navigate
    done_events = [e for e in parsed_events if e.get("node_id") == "__answer__" and e.get("status") == "done"]
    assert len(done_events) == 1
    assert done_events[0]["ui_navigate"] == mock_nav
    assert done_events[0]["detail"]["ui_navigate"] == mock_nav

    # 3. Các event cũ (chunk, answer, complete) vẫn nguyên vẹn
    chunk_events = [e for e in parsed_events if e.get("node_id") == "__answer__" and e.get("status") == "chunk"]
    assert len(chunk_events) == 2
    assert done_events[0]["complete"] is True
    assert done_events[0]["output"] == "Có 100 xe vào."


def test_frontend_code_contract():
    """frontend/app.js và style.css chứa code xử lý ui_navigate, nút 'Mở trang' và kiểm tra whitelist."""
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    app_js_path = frontend_dir / "app.js"
    style_css_path = frontend_dir / "style.css"

    assert app_js_path.exists()
    app_js = app_js_path.read_text(encoding="utf-8")

    # Có whitelist ở FE
    assert "UI_NAVIGATE_WHITELIST" in app_js
    assert "isWhitelistedNavPath" in app_js
    assert "appendUiNavigateButton" in app_js
    assert "Mở trang" in app_js
    assert "ui-navigate-container" in app_js
    assert "btn-ui-navigate" in app_js

    # CSS có selector cho button và container
    assert style_css_path.exists()
    style_css = style_css_path.read_text(encoding="utf-8")
    assert ".ui-navigate-container" in style_css
    assert ".btn-ui-navigate" in style_css
