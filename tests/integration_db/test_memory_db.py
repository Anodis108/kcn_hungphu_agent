from __future__ import annotations

"""Integration tests for Core Memory capability.

Combines:
- test_product_memory_api.py (REST API endpoints for memory management)
- test_product_memory_context.py (Context engineering, sliding window, summarization)
- test_product_memory_extract.py (Fact extraction from conversation turns)
- test_product_memory_shortterm.py (Short-term session memory buffer)
- test_product_graph_memory.py (LangGraph memory integration nodes)
- test_frontend_memory_connect.py (Frontend contract & memory UI badge)
- test_product_user_isolation.py (AC-2 multi-user memory isolation)
"""

# ==============================================================================
# --- Sourced from test_product_memory_api.py ---
# ==============================================================================

"""Unit & Integration test suite for Memory Management API (GET /api/memory, DELETE /api/memory).

Tương thích kiến trúc Memory & Context Engineering (v9):
1. GET /api/memory?user_id=...: Trả về danh sách facts của người dùng.
2. DELETE /api/memory?user_id=...: Xóa toàn bộ facts khi người dùng bấm Reset Memory.
3. User Isolation: Thao tác của User A không làm ảnh hưởng User B.
4. Input Validation: Yêu cầu bắt buộc user_id hợp lệ (không rỗng/khoảng trắng).
5. Graceful Degradation: Hoạt động bền bỉ, an toàn kể cả khi DB không khả dụng.
"""


import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.infra.memory.longterm import clear_long_term, recall_long_term, save_to_long_term


@pytest.fixture(autouse=True)
def clean_memory_fixture():
    """Tự động dọn dẹp bộ nhớ trước và sau mỗi test case."""
    clear_long_term()
    yield
    clear_long_term()


@pytest.fixture
def client():
    return TestClient(app)


def test_get_memory_empty_for_new_user(client):
    """User mới chưa có facts nào thì GET /api/memory trả về mảng rỗng."""
    resp = client.get("/api/memory?user_id=fresh_user_001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["user_id"] == "fresh_user_001"
    assert data["facts"] == []
    assert data["memories"] == []
    assert data["total"] == 0


def test_get_memory_with_facts(client):
    """User đã lưu facts thì GET /api/memory trả về đúng danh sách."""
    uid = "test_user_inspector"
    save_to_long_term(uid, "Tôi tên là Nguyễn Văn Tuấn", category="identity")
    save_to_long_term(uid, "Tôi phụ trách giám sát an ninh ca đêm", category="role")

    resp = client.get(f"/api/memory?user_id={uid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["user_id"] == uid
    assert data["total"] == 2
    assert "Tôi tên là Nguyễn Văn Tuấn" in data["facts"]
    assert "Tôi phụ trách giám sát an ninh ca đêm" in data["facts"]
    assert data["memories"] == data["facts"]


def test_get_memory_with_limit(client):
    """Hỗ trợ phân trang/giới hạn số lượng facts trả về qua tham số limit."""
    uid = "user_multi_facts"
    for i in range(5):
        save_to_long_term(uid, f"Sự thật số {i+1} về công việc của tôi")

    resp = client.get(f"/api/memory?user_id={uid}&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert len(data["facts"]) == 2
    assert data["total"] == 2


def test_get_memory_missing_or_empty_user_id(client):
    """Thiếu hoặc rỗng user_id trả về lỗi 422 hoặc 400 Bad Request."""
    # Thiếu query param
    resp1 = client.get("/api/memory")
    assert resp1.status_code in (400, 422)

    # Rỗng hoặc chỉ có khoảng trắng
    resp2 = client.get("/api/memory?user_id=")
    assert resp2.status_code in (400, 422)

    resp3 = client.get("/api/memory?user_id=%20%20")
    assert resp3.status_code == 400
    assert "user_id is required" in resp3.json()["detail"]


def test_delete_memory_clears_user_facts(client):
    """DELETE /api/memory xóa sạch toàn bộ facts của user chỉ định."""
    uid = "user_to_be_reset"
    save_to_long_term(uid, "Tôi thích xem camera cổng chính")
    save_to_long_term(uid, "Tôi là ca trưởng ca chiều")

    # Kiểm tra trước khi xóa
    before_resp = client.get(f"/api/memory?user_id={uid}")
    assert before_resp.json()["total"] == 2

    # Gọi API Reset Memory
    del_resp = client.delete(f"/api/memory?user_id={uid}")
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["status"] == "ok"
    assert del_data["user_id"] == uid
    assert del_data["deleted"] is True
    assert uid in del_data["message"]

    # Kiểm tra sau khi xóa
    after_resp = client.get(f"/api/memory?user_id={uid}")
    assert after_resp.status_code == 200
    assert after_resp.json()["total"] == 0
    assert after_resp.json()["facts"] == []


def test_delete_memory_missing_or_empty_user_id(client):
    """DELETE không truyền user_id hoặc truyền rỗng trả về mã lỗi thích hợp."""
    resp1 = client.delete("/api/memory")
    assert resp1.status_code in (400, 422)

    resp2 = client.delete("/api/memory?user_id=")
    assert resp2.status_code in (400, 422)

    resp3 = client.delete("/api/memory?user_id=%20")
    assert resp3.status_code == 400
    assert "user_id is required" in resp3.json()["detail"]


def test_user_isolation_on_get_and_delete(client):
    """User Isolation (AC-2): Thao tác xóa hoặc đọc của User A không tác động User B."""
    user_a = "guard_alpha"
    user_b = "guard_beta"

    save_to_long_term(user_a, "Alpha phụ trách trạm cân")
    save_to_long_term(user_b, "Beta phụ trách hàng rào điện tử")

    # Xác nhận hai user độc lập
    resp_a = client.get(f"/api/memory?user_id={user_a}")
    assert resp_a.json()["total"] == 1
    assert "Alpha phụ trách trạm cân" in resp_a.json()["facts"]

    resp_b = client.get(f"/api/memory?user_id={user_b}")
    assert resp_b.json()["total"] == 1
    assert "Beta phụ trách hàng rào điện tử" in resp_b.json()["facts"]

    # Reset memory của user A
    del_a = client.delete(f"/api/memory?user_id={user_a}")
    assert del_a.status_code == 200

    # User A bị xóa sạch
    check_a = client.get(f"/api/memory?user_id={user_a}")
    assert check_a.json()["total"] == 0
    assert check_a.json()["facts"] == []

    # User B vẫn nguyên vẹn
    check_b = client.get(f"/api/memory?user_id={user_b}")
    assert check_b.json()["total"] == 1
    assert "Beta phụ trách hàng rào điện tử" in check_b.json()["facts"]


def test_graceful_degradation_endpoints_when_db_down(client, monkeypatch):
    """Graceful Degradation (AC-3): Giả lập DB lỗi, API vẫn hoạt động qua fallback."""
    from unittest.mock import MagicMock

    # Giả lập is_postgres_configured=True nhưng connection pool lỗi
    monkeypatch.setattr("src.infra.memory.longterm.is_postgres_configured", lambda: True)

    def mock_get_conn(*args, **kwargs):
        raise ConnectionError("Simulated PostgreSQL connection failure")

    monkeypatch.setattr("src.infra.memory.longterm.get_memory_connection", mock_get_conn)

    uid = "fallback_user"
    # Lưu và truy xuất qua fallback
    save_to_long_term(uid, "Thông tin lưu trong tình huống DB offline")

    # GET vẫn thành công (200), không trả 500
    resp_get = client.get(f"/api/memory?user_id={uid}")
    assert resp_get.status_code == 200
    assert resp_get.json()["status"] == "ok"
    assert "Thông tin lưu trong tình huống DB offline" in resp_get.json()["facts"]

    # DELETE vẫn thành công (200), không trả 500
    resp_del = client.delete(f"/api/memory?user_id={uid}")
    assert resp_del.status_code == 200
    assert resp_del.json()["status"] == "ok"

    # Sau khi xóa
    resp_after = client.get(f"/api/memory?user_id={uid}")
    assert resp_after.status_code == 200
    assert resp_after.json()["total"] == 0

# ==============================================================================
# --- Sourced from test_product_memory_context.py ---
# ==============================================================================

"""Unit tests for Context Engineering Engine (src/memory/context.py).

Kiểm thử toàn diện 5 trụ cột Context Engineering theo specs/test-plan.md:
1. Sliding Window (bảo tồn system message + giữ N message gần nhất).
2. Token Estimation & Context Usage.
3. Ngưỡng kích hoạt nén chủ động 40% (nguyên tắc 40-60%).
4. Summarization hội thoại cũ thành 1 system message mang tiền tố.
5. Tool-Output Compression (chỉ nén khi vượt ngưỡng, bỏ qua khi ngắn).
6. Instruction Re-injection ở cuối context.
7. Tương thích cả dict lẫn LangChain BaseMessage.
"""

from unittest.mock import patch
import pytest

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.infra.memory.context import (
    REINJECT_PREFIX,
    SUMMARY_PREFIX,
    compress_tool_result,
    context_usage,
    estimate_tokens,
    format_messages,
    reinject_instructions,
    should_compact,
    sliding_window,
    summarize_old_messages,
    summarize_text,
)


def test_sliding_window_preserves_system_and_recent():
    """Tạo 25 message (1 system + 24 turns). Sliding window max=10 trả về đúng 11 message."""
    messages = [{"role": "system", "content": "System prompt gốc VMS KCN"}]
    for i in range(1, 25):
        role = "user" if i % 2 != 0 else "assistant"
        messages.append({"role": role, "content": f"Turn {i} nội dung tin nhắn"})

    assert len(messages) == 25

    windowed = sliding_window(messages, max_messages=10)
    assert len(windowed) == 11
    # System message gốc được bảo tồn ở đầu
    assert windowed[0]["role"] == "system"
    assert "System prompt gốc" in windowed[0]["content"]
    # 10 message sau cùng là các turn mới nhất (15 đến 24)
    assert windowed[-1]["content"] == "Turn 24 nội dung tin nhắn"
    assert windowed[1]["content"] == "Turn 15 nội dung tin nhắn"


def test_sliding_window_short_history_unchanged():
    """Khi tổng số message nhỏ hơn max_messages, giữ nguyên danh sách."""
    messages = [
        {"role": "system", "content": "Prompt"},
        {"role": "user", "content": "Câu 1"},
        {"role": "assistant", "content": "Đáp 1"},
    ]
    windowed = sliding_window(messages, max_messages=10)
    assert len(windowed) == 3
    assert windowed == messages


def test_estimate_tokens_and_context_usage():
    """Ước lượng số token theo tỷ lệ 4 ký tự/token và đo tỷ lệ context_usage."""
    # 400 ký tự -> ~100 tokens
    messages = [
        {"role": "user", "content": "A" * 200},
        {"role": "assistant", "content": "B" * 200},
    ]
    tokens = estimate_tokens(messages)
    assert tokens == 100

    usage = context_usage(messages, window_tokens=1000)
    assert pytest.approx(usage, 0.001) == 0.1

    # Khi window_tokens <= 0
    assert context_usage(messages, window_tokens=0) == 0.0


def test_should_compact_activates_at_40_percent():
    """Kiểm tra điều kiện kích hoạt nén chủ động khi tỷ lệ vượt 40% window (nguyên tắc 40-60%)."""
    # 800 ký tự -> ~200 tokens
    messages = [
        {"role": "user", "content": "X" * 800},
    ]
    tokens = estimate_tokens(messages)
    assert tokens == 200

    # 200 tokens / 1000 window = 20% (< 40%) -> Không compact
    assert should_compact(messages, window_tokens=1000, threshold=0.40) is False

    # 200 tokens / 400 window = 50% (> 40%) -> Kích hoạt compact
    assert should_compact(messages, window_tokens=400, threshold=0.40) is True


def test_summarize_old_messages_creates_summary_message():
    """Tạo 15 message, summarize_old_messages(keep_recent=4) trả về 5 message với prefix chuẩn."""
    messages = [{"role": "system", "content": "Prompt VMS"}]
    for i in range(1, 15):
        messages.append({"role": "user", "content": f"Câu hỏi {i}"})

    assert len(messages) == 15

    with patch("src.infra.memory.context.summarize_text", return_value="Tóm tắt các sự kiện an ninh từ lượt 1 đến 10."):
        compacted = summarize_old_messages(messages, keep_recent=4)
        assert len(compacted) == 5
        # Message đầu tiên là bản tóm tắt
        assert compacted[0]["role"] == "system"
        assert compacted[0]["content"].startswith(SUMMARY_PREFIX)
        assert "Tóm tắt các sự kiện an ninh" in compacted[0]["content"]
        # 4 message gần nhất được giữ nguyên
        assert compacted[-1]["content"] == "Câu hỏi 14"
        assert compacted[-4]["content"] == "Câu hỏi 11"


def test_summarize_old_messages_short_history_no_compact():
    """Nếu lịch sử ít hơn hoặc bằng keep_recent + 1, không thực hiện tóm tắt."""
    messages = [
        {"role": "system", "content": "Prompt"},
        {"role": "user", "content": "Câu 1"},
        {"role": "assistant", "content": "Đáp 1"},
    ]
    res = summarize_old_messages(messages, keep_recent=4)
    assert len(res) == 3
    assert res == messages


def test_compress_tool_result_skips_short_output():
    """Kết quả tool ngắn (< 300 token * 4 chars) giữ nguyên bản, không gọi LLM nén."""
    short_table = "| camera | count |\n| C01 | 15 |\n"
    with patch("src.infra.memory.context.invoke_text") as mock_invoke:
        result = compress_tool_result(short_table, query="Số xe camera C01?", max_tokens=300)
        assert result == short_table
        assert not mock_invoke.called


def test_compress_tool_result_compresses_long_output():
    """Kết quả tool dài (> 300 token * 4 chars) kích hoạt nén và trả về kết quả tóm tắt."""
    long_raw_data = "Sự kiện chi tiết camera: " + ("ID: 15K, Loại xe: tải, Cổng: 1, Thời gian: 08:30;\n" * 60)
    assert len(long_raw_data) > 1200

    with patch("src.infra.memory.context.invoke_text", return_value="Tổng hợp: 60 lượt xe tải qua Cổng 1 lúc 08:30."):
        with patch("src.infra.memory.context.use_offline_tools", return_value=False):
            compressed = compress_tool_result(long_raw_data, query="Bao nhiêu xe tải qua cổng 1?", max_tokens=250)
            assert "Tổng hợp: 60 lượt xe tải" in compressed


def test_reinject_instructions_appends_to_end():
    """reinject_instructions chèn system message mang tiền tố [Nhắc lại chỉ dẫn] vào cuối danh sách."""
    messages = [
        {"role": "system", "content": "System prompt gốc"},
        {"role": "user", "content": "Tôi muốn kiểm tra camera"},
    ]
    instructions = "Chỉ truy vấn bảng read-only, tuyệt đối không suy đoán số liệu."

    reinjected = reinject_instructions(messages, instructions)
    assert len(reinjected) == 3
    last_msg = reinjected[-1]
    assert last_msg["role"] == "system"
    assert last_msg["content"].startswith(REINJECT_PREFIX)
    assert instructions in last_msg["content"]


def test_reinject_instructions_empty_instructions_passthrough():
    """Nếu instructions rỗng, trả về danh sách nguyên bản."""
    messages = [{"role": "user", "content": "Hello"}]
    assert reinject_instructions(messages, "") == messages
    assert reinject_instructions(messages, "   ") == messages


def test_langchain_base_messages_compatibility():
    """Xác nhận Context Engineering tương thích hoàn hảo với LangChain BaseMessage."""
    sys_m = SystemMessage(content="System prompt LangChain")
    human_m = HumanMessage(content="Hôm nay có bao nhiêu lượt xe?")
    ai_m = AIMessage(content="Có 150 lượt xe vào KCN.")

    msgs = [sys_m, human_m, ai_m]

    # format_messages
    text_repr = format_messages(msgs)
    assert "system: System prompt LangChain" in text_repr
    assert "human: Hôm nay có bao nhiêu lượt xe?" in text_repr
    assert "ai: Có 150 lượt xe vào KCN." in text_repr

    # estimate_tokens
    assert estimate_tokens(msgs) > 0

    # reinject_instructions
    re_msgs = reinject_instructions(msgs, "Không bịa số liệu")
    assert len(re_msgs) == 4
    assert isinstance(re_msgs[-1], SystemMessage)
    assert re_msgs[-1].content.startswith(REINJECT_PREFIX)


def test_latest_human_query_scans_backwards():
    """latest_human_query quét ngược qua các tool message để tìm câu hỏi user gần nhất."""
    from src.infra.memory.context import latest_human_query, _latest_human_query

    messages = [
        {"role": "user", "content": "Câu hỏi đầu tiên"},
        {"role": "assistant", "content": "Trả lời câu đầu"},
        {"role": "user", "content": "Xe tải biển số 65A có vào không?"},
        {"role": "assistant", "content": "Để tôi kiểm tra SQL", "tool_calls": [{"name": "sql_query"}]},
        {"role": "tool", "content": "Kết quả: 1 bản ghi xe 65A"},
    ]
    query = latest_human_query(messages)
    assert query == "Xe tải biển số 65A có vào không?"
    # Alias
    assert _latest_human_query(messages) == query


def test_detect_repetition_detects_infinite_loop():
    """detect_repetition trả về True khi có window tool calls giống hệt nhau liên tiếp."""
    from src.infra.memory.context import detect_repetition, _detect_repetition, REPETITION_WARNING

    # 4 tool calls giống nhau liên tiếp -> bị kẹt vòng lặp
    stuck_messages = [
        {"role": "user", "content": "Kiểm tra camera 1"},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c1"}]},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c1"}]},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c1"}]},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c1"}]},
    ]
    assert detect_repetition(stuck_messages, window=4) is True
    assert _detect_repetition(stuck_messages, window=4) is True
    assert "lặp lại cùng 1 hành động" in REPETITION_WARNING

    # Các calls khác nhau -> False
    normal_messages = [
        {"role": "user", "content": "Kiểm tra camera 1"},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c1"}]},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c2"}]},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c3"}]},
        {"role": "assistant", "content": "Gọi tool", "tool_calls": [{"name": "check_cam", "id": "c4"}]},
    ]
    assert detect_repetition(normal_messages, window=4) is False


def test_create_compaction_diff_persists_to_state():
    """create_compaction_diff tạo danh sách RemoveMessage(id) và 1 summary message."""
    from src.infra.memory.context import create_compaction_diff
    from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage, SystemMessage

    msgs = [
        HumanMessage(content="Tin nhắn cũ 1", id="m-1"),
        AIMessage(content="Trả lời cũ 1", id="m-2"),
        HumanMessage(content="Tin nhắn cũ 2", id="m-3"),
        AIMessage(content="Trả lời cũ 2", id="m-4"),
        HumanMessage(content="Tin nhắn gần 1", id="m-5"),
        AIMessage(content="Trả lời gần 1", id="m-6"),
        HumanMessage(content="Tin nhắn gần 2", id="m-7"),
        AIMessage(content="Trả lời gần 2", id="m-8"),
    ]

    with patch("src.infra.memory.context.use_offline_tools", return_value=True):
        diff = create_compaction_diff(msgs, keep_recent=4)
        assert "messages" in diff
        diff_msgs = diff["messages"]
        # 4 old messages -> 4 RemoveMessage + 1 SystemMessage (summary) = 5
        assert len(diff_msgs) == 5
        removals = [m for m in diff_msgs if isinstance(m, RemoveMessage)]
        assert len(removals) == 4
        assert [r.id for r in removals] == ["m-1", "m-2", "m-3", "m-4"]
        summary = diff_msgs[-1]
        assert isinstance(summary, SystemMessage)
        assert summary.content.startswith(SUMMARY_PREFIX)


def test_should_compact_route_conditional_edge():
    """should_compact_route trả về 'compact' nếu vượt 40% window, ngược lại 'continue'."""
    from src.infra.memory.context import should_compact_route

    # Dưới ngưỡng
    short_msgs = [{"role": "user", "content": "A" * 100}]
    assert should_compact_route(short_msgs, window_tokens=1000, threshold=0.40) == "continue"

    # Vượt ngưỡng 40% (500 tokens / 1000 tokens = 50%)
    long_msgs = [{"role": "user", "content": "A" * 2000}]
    assert should_compact_route(long_msgs, window_tokens=1000, threshold=0.40) == "compact"
    # State dict input
    assert should_compact_route({"messages": long_msgs}, window_tokens=1000, threshold=0.40) == "compact"


# ==============================================================================
# --- Sourced from test_product_memory_extract.py ---
# ==============================================================================

"""Unit tests for Fact Extraction (src/memory/extract.py).

Kiểm thử:
1. Regex tiếng Việt trích xuất Tên, Vai trò, Camera, Sở thích, Ghi nhớ
2. Lọc bỏ các từ nghi vấn trong câu hỏi (ai, gì, sao...)
3. Bỏ qua các số liệu thống kê realtime tạm thời (query_data)
4. Tích hợp LLM extraction với prompt memory_extract khi online
5. Trích xuất trực tiếp từ danh sách tin nhắn hội thoại (extract_from_messages)
6. Lưu trữ tự động vào PostgreSQL qua extract_and_store_memory
7. An toàn tuyệt đối (Graceful degradation): input rỗng hoặc lỗi không gây crash
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.infra.memory.extract import (
    _heuristic_extract,
    extract_and_store_memory,
    extract_from_messages,
    extract_memories,
    memory_detail_includes_answer,
)
from src.infra.memory.longterm import clear_long_term, recall_long_term


@pytest.fixture(autouse=True)
def clean_memory():
    """Tự động dọn dẹp long-term memory trước và sau mỗi ca test."""
    clear_long_term()
    yield
    clear_long_term()


def test_heuristic_extract_name():
    """Trích xuất tên người dùng qua nhiều dạng mẫu câu tiếng Việt."""
    assert _heuristic_extract("Xin chào, tôi tên là Tuấn Anh") == ["Tên người dùng là Tuấn Anh"]
    assert _heuristic_extract("Tên tôi là Hoàng Minh.") == ["Tên người dùng là Hoàng Minh"]
    assert _heuristic_extract("Mình tên là Thanh Trúc, phụ trách ca sáng") == [
        "Tên người dùng là Thanh Trúc",
        "Người dùng phụ trách ca sáng",
    ]


def test_heuristic_extract_role_and_camera():
    """Trích xuất vai trò và camera theo dõi."""
    facts = _heuristic_extract("Tôi phụ trách camera trạm cân số 1")
    assert any("trạm cân số 1" in f for f in facts)

    facts_cam = _heuristic_extract("Tôi theo dõi camera Cổng 2 và Cổng 3")
    assert any("Cổng 2 và Cổng 3" in f for f in facts_cam)


def test_heuristic_extract_preference_and_note():
    """Trích xuất sở thích và lưu ý cần ghi nhớ."""
    facts = _heuristic_extract("Tôi thích xem biểu đồ hình tròn. Nhớ là xe bồn vào sau 18h nhé.")
    assert any("biểu đồ hình tròn" in f for f in facts)
    assert any("xe bồn vào sau 18h" in f for f in facts)


def test_heuristic_extract_ignores_question_words():
    """Không trích xuất nhầm các câu hỏi truy vấn của người dùng."""
    assert _heuristic_extract("Tôi là ai?") == []
    assert _heuristic_extract("Tôi tên là gì?") == []
    assert _heuristic_extract("Ai phụ trách camera cổng 1?") == []


def test_memory_detail_includes_answer_filtering():
    """Chỉ cho phép trích xuất answer từ docs; bỏ qua query_data và out_of_scope."""
    assert memory_detail_includes_answer("docs") is True
    assert memory_detail_includes_answer("query_data") is False
    assert memory_detail_includes_answer("out_of_scope") is False
    assert memory_detail_includes_answer("orchestrator_multi") is False
    assert memory_detail_includes_answer("") is False


def test_extract_memories_skips_realtime_traffic_stats():
    """Câu hỏi thống kê lượt xe: Tuyệt đối không lưu số liệu 150 xe vào long-term memory."""
    facts = extract_memories(
        user_id="u_test_stat",
        question="Hôm nay có bao nhiêu lượt xe vào KCN?",
        answer="Hệ thống ghi nhận có 150 lượt xe tải và 45 lượt xe con.",
        detail="query_data",
    )
    # Không có fact nào chứa con số thống kê tạm thời
    assert facts == []
    assert not any("150" in f for f in facts)


def test_extract_memories_online_with_llm(monkeypatch):
    """Khi online và detail=docs: gọi LLM trích xuất thông tin hữu ích."""
    monkeypatch.setattr("src.infra.memory.extract.use_offline_tools", lambda: False)
    mock_invoke = MagicMock(return_value="- Người dùng phụ trách quản lý camera kho A\n- Lưu ý ca trực từ 6h-14h")
    monkeypatch.setattr("src.infra.memory.extract.invoke_text", mock_invoke)

    facts = extract_memories(
        user_id="u_online",
        question="Tài liệu camera kho A ở đâu?",
        answer="Xem tài liệu quy trình vận hành kho A.",
        detail="docs",
    )
    assert mock_invoke.call_count == 1
    assert "Người dùng phụ trách quản lý camera kho A" in facts
    assert "Lưu ý ca trực từ 6h-14h" in facts


def test_extract_from_messages_scans_history():
    """Trích xuất fact từ danh sách tin nhắn LangChain / dict."""
    messages = [
        {"role": "system", "content": "System prompt"},
        HumanMessage(content="Chào bạn, tôi tên là Đăng Khoa, phụ trách an ninh cổng 1"),
        AIMessage(content="Chào anh Đăng Khoa, tôi có thể giúp gì cho anh?"),
    ]
    facts = extract_from_messages("u_msg_test", messages)
    assert any("Đăng Khoa" in f for f in facts)
    assert any("cổng 1" in f for f in facts)


def test_extract_and_store_memory_persists_to_db():
    """extract_and_store_memory trích xuất và lưu ngay vào long-term store."""
    facts = extract_and_store_memory("u_persist", "Tôi tên là Quốc Hưng, tôi phụ trách trạm biến áp")
    assert len(facts) >= 2

    # Kiểm tra recall lại fact từ long-term
    recalled = recall_long_term("u_persist", "ai phụ trách trạm biến áp?")
    assert len(recalled) >= 1
    assert any("trạm biến áp" in r for r in recalled)


def test_extract_memories_empty_or_whitespace_noop():
    """Đầu vào rỗng hoặc whitespace không gây lỗi, trả về danh sách rỗng."""
    assert extract_memories("", "Tôi tên là Nam") == []
    assert extract_memories("   ", "Tôi tên là Nam") == []
    assert extract_memories("u1", "") == []
    assert extract_memories("u1", "   ") == []
    assert extract_from_messages("u1", []) == []

# ==============================================================================
# --- Sourced from test_product_memory_shortterm.py ---
# ==============================================================================

"""Unit tests for Short-Term Memory Checkpointer (src/memory/shortterm.py).

Kiểm thử:
1. Trạng thái bật/tắt (settings.short_term_memory_enabled)
2. Singleton pattern và thread-safety
3. Graceful degradation: Fallback MemorySaver khi DB chưa cấu hình hoặc ngắt kết nối
4. PostgresSaver checkpointer khi PostgreSQL sẵn sàng
5. Reset checkpointer và giải phóng tài nguyên
6. Đảm bảo cô lập dữ liệu theo thread_id / session_id
"""

import concurrent.futures
from unittest.mock import MagicMock, patch

import pytest
from langgraph.checkpoint.base import BaseCheckpointSaver, empty_checkpoint
from langgraph.checkpoint.memory import MemorySaver

from src.shared.settings import settings
from src.infra.memory.shortterm import (
    get_checkpointer,
    is_using_postgres_checkpointer,
    reset_checkpointer,
)


@pytest.fixture(autouse=True)
def clean_checkpointer():
    """Tự động dọn dẹp và reset checkpointer trước và sau mỗi ca test."""
    reset_checkpointer()
    yield
    reset_checkpointer()


def test_get_checkpointer_disabled(monkeypatch):
    """Khi short_term_memory_enabled=False, get_checkpointer trả về None."""
    monkeypatch.setattr(settings, "memory_enabled", False)
    assert settings.short_term_memory_enabled is False
    assert get_checkpointer() is None


def test_get_checkpointer_memory_saver_singleton_when_db_not_configured(monkeypatch):
    """Khi PostgreSQL không cấu hình, get_checkpointer trả về MemorySaver singleton."""
    monkeypatch.setattr(settings, "db_host", "")
    cp1 = get_checkpointer()
    cp2 = get_checkpointer()

    assert cp1 is not None
    assert cp1 is cp2
    assert isinstance(cp1, MemorySaver)
    assert isinstance(cp1, BaseCheckpointSaver)
    assert is_using_postgres_checkpointer() is False


def test_get_checkpointer_fallback_on_db_exception(monkeypatch):
    """Khi kết nối PostgreSQL bị lỗi (timeout/network down), tự động fallback MemorySaver an toàn."""
    monkeypatch.setattr(settings, "db_host", "192.0.2.1")
    monkeypatch.setattr(settings, "db_user", "postgres")

    with patch("src.infra.memory.shortterm._create_postgres_checkpointer", side_effect=Exception("Database down")):
        cp = get_checkpointer()
        assert cp is not None
        assert isinstance(cp, MemorySaver)
        assert is_using_postgres_checkpointer() is False


def test_get_checkpointer_postgres_success(monkeypatch):
    """Khi PostgreSQL kết nối thành công, PostgresSaver được khởi tạo và chạy .setup()."""
    monkeypatch.setattr(settings, "db_host", "localhost")
    monkeypatch.setattr(settings, "db_user", "postgres")

    mock_pool = MagicMock()
    mock_saver = MagicMock()
    mock_saver.setup = MagicMock()

    class FakePostgresSaver(BaseCheckpointSaver):
        pass

    FakePostgresSaver.__name__ = "PostgresSaver"
    mock_saver.__class__ = FakePostgresSaver

    with patch("psycopg_pool.ConnectionPool", return_value=mock_pool), \
         patch("langgraph.checkpoint.postgres.PostgresSaver", return_value=mock_saver):

        cp = get_checkpointer()
        assert cp is mock_saver
        mock_saver.setup.assert_called_once()
        assert is_using_postgres_checkpointer() is True


def test_reset_checkpointer_closes_pool_and_resets():
    """reset_checkpointer đóng pool kết nối và dọn sạch singleton."""
    mock_pool = MagicMock()
    with patch("src.infra.memory.shortterm._pool_instance", mock_pool):
        reset_checkpointer()
        mock_pool.close.assert_called_once()

    # Sau khi reset, gọi lại tạo instance mới
    cp_new = get_checkpointer()
    assert cp_new is not None


def test_thread_safety_checkpointer_singleton(monkeypatch):
    """Nhiều thread gọi get_checkpointer đồng thời phải nhận về cùng 1 singleton."""
    monkeypatch.setattr(settings, "db_host", "")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(get_checkpointer) for _ in range(20)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    assert len(results) == 20
    first = results[0]
    for cp in results:
        assert cp is first


def test_checkpoint_state_persistence_and_isolation(monkeypatch):
    """Kiểm tra lưu trữ và nạp checkpoint giữa các thread_id khác nhau."""
    monkeypatch.setattr(settings, "db_host", "")
    cp = get_checkpointer()
    assert cp is not None

    config_1 = {"configurable": {"thread_id": "session_user_1", "checkpoint_ns": ""}}
    config_2 = {"configurable": {"thread_id": "session_user_2", "checkpoint_ns": ""}}

    cp1_val = empty_checkpoint()
    cp1_val["channel_values"] = {"messages": ["Xin chào từ user 1"]}
    cp1_val["channel_versions"] = {"messages": 1}

    cp2_val = empty_checkpoint()
    cp2_val["channel_values"] = {"messages": ["Xin chào từ user 2"]}
    cp2_val["channel_versions"] = {"messages": 1}

    # Lưu checkpoint
    new_cfg_1 = cp.put(config_1, cp1_val, {"source": "update"}, new_versions={"messages": 1})
    new_cfg_2 = cp.put(config_2, cp2_val, {"source": "update"}, new_versions={"messages": 1})

    # Nạp lại checkpoint
    loaded_1 = cp.get_tuple(new_cfg_1)
    loaded_2 = cp.get_tuple(new_cfg_2)

    assert loaded_1 is not None
    assert loaded_1.checkpoint["channel_values"]["messages"] == ["Xin chào từ user 1"]

    assert loaded_2 is not None
    assert loaded_2.checkpoint["channel_values"]["messages"] == ["Xin chào từ user 2"]

# ==============================================================================
# --- Sourced from test_product_graph_memory.py ---
# ==============================================================================

"""Unit tests for Phase 4: Graph Memory & Context Engineering integration (src/agent/graph.py)."""


import pytest
from unittest.mock import MagicMock, patch

from src.domain.agents.graph import (Agent_Input, Agent_Output, run_agent, run_agent_stream)

from src.domain.agents.tools import memory_context_block as _memory_context_block

from src.domain.agents.nodes.memory import (extract_memory_node, recall_memory_node, recall_node)
from src.domain.agents.nodes.inline_respond import generate_inline_response
from src.infra.memory import (
    clear_long_term,
    clear_ttl_cache,
    recall_long_term,
    save_to_long_term,
)
from langchain_core.messages import AIMessage, HumanMessage


@pytest.fixture(autouse=True)
def clean_stores():
    clear_long_term()
    clear_ttl_cache()
    yield
    clear_long_term()
    clear_ttl_cache()


def test_recall_memory_node_alias_and_functionality():
    """recall_memory_node là alias hợp lệ của recall_node và truy vấn đúng fact."""
    assert recall_memory_node is recall_node

    save_to_long_term("u_graph_test", "Người dùng là kỹ sư trưởng ca sáng")
    state = {
        "user_id": "u_graph_test",
        "question": "Tôi làm nhiệm vụ gì?",
    }
    out = recall_memory_node(state)
    assert "recalled_memories" in out
    assert any("kỹ sư trưởng" in m for m in out["recalled_memories"])


def test_memory_context_block_formatting():
    """_memory_context_block định dạng chính xác tiền tố 'Thông tin đã biết về user:'."""
    state = {
        "recalled_memories": [
            "Tên người dùng là Tuấn",
            "Người dùng phụ trách camera cổng số 2",
        ]
    }
    block = _memory_context_block(state)
    assert "Thông tin đã biết về user:" in block
    assert "- Tên người dùng là Tuấn" in block
    assert "- Người dùng phụ trách camera cổng số 2" in block


def test_extract_memory_node_stores_facts_directly():
    """extract_memory_node trích xuất thông tin mới từ state và lưu vào bộ nhớ bền vững."""
    state = {
        "user_id": "u_extract_node",
        "question": "Tôi tên là Hoàng Minh, phụ trách trạm cân KCN Hưng Phú",
        "answer": "Chào bạn Hoàng Minh, tôi đã ghi nhận vai trò phụ trách trạm cân của bạn.",
        "respond_mode": "chat",
    }
    res = extract_memory_node(state)
    assert "extracted_memories" in res
    extracted = res["extracted_memories"]
    assert any("Hoàng Minh" in f for f in extracted)

    # Kiểm tra đã lưu bền vững
    saved_facts = recall_long_term("u_extract_node", "Hoàng Minh trạm cân")
    assert len(saved_facts) >= 1
    assert any("Hoàng Minh" in f for f in saved_facts)


def test_sliding_window_prunes_long_history(monkeypatch):
    """Lịch sử hội thoại dài trên 20 tin nhắn được sliding_window thu gọn an toàn."""
    from src.domain.agents.nodes.rewrite_classify import rewrite_node

    long_messages = [HumanMessage(content=f"Câu hỏi số {i}") for i in range(25)]
    state = {
        "question": "Hôm nay có bao nhiêu lượt xe tải?",
        "messages": long_messages,
    }
    out = rewrite_node(state)
    assert out["rewritten"] is not None


def test_compress_tool_result_applied_when_long(monkeypatch):
    """Khi kết quả tool/bảng SQL quá dài (> 1200 chars), compress_tool_result được gọi để nén."""
    from src.infra.memory.context import compress_tool_result

    raw_table = "\n".join(f"camera_{i}=Cổng_{i}, so_luot={i*10}, loai_xe=TRUCK" for i in range(50))
    assert len(raw_table) > 1200

    compressed = compress_tool_result(raw_table, query="Số lượt xe tải", max_tokens=300)
    assert len(compressed) <= len(raw_table)
    assert "... [đã nén]" in compressed or len(compressed) < len(raw_table)


def test_inline_respond_answers_identity_with_memories():
    """Khi người dùng hỏi 'Tôi là ai?', trợ lý dùng thông tin memories để phản hồi lịch sự."""
    memories = [
        "Tên người dùng là Tuấn",
        "Người dùng phụ trách camera cổng số 2",
    ]
    resp = generate_inline_response("Tôi là ai?", intent="chat", memories=memories)
    assert "Tuấn" in resp
    assert "Theo thông tin tôi ghi nhận về bạn" in resp


def test_instruction_reinject_in_respond_prompt(monkeypatch):
    """Chỉ dẫn an toàn [Nhắc lại chỉ dẫn] được tái chèn vào prompt trước khi gọi LLM."""
    captured_sys: list[str] = []

    def mock_invoke(sys_prompt: str, user_prompt: str, **kwargs) -> str:
        captured_sys.append(sys_prompt)
        return "Kết quả truy vấn xe tải."

    monkeypatch.setattr("src.infra.llm.client.use_offline_tools", lambda: False)
    monkeypatch.setattr("src.infra.llm.client.invoke_text", mock_invoke)
    monkeypatch.setattr("src.domain.agents.analytics.sql_agent.tools.generate.invoke_text", mock_invoke)
    monkeypatch.setattr("src.domain.agents.analytics.sql_agent.tools.generate.use_offline_tools", lambda: False)
    monkeypatch.setattr("src.domain.agents.analytics.sql_agent.tools.execute.use_offline_tools", lambda: False)
    monkeypatch.setattr(
        "src.domain.agents.analytics.sql_agent.tools.execute.execute_sql",
        lambda sql, params=None: ([{"loai_xe": "TRUCK", "so_luot": 25}], ["loai_xe", "so_luot"]),
    )

    inp = Agent_Input(question="Hôm nay có bao nhiêu xe tải vào cổng?", user_id="u_reinject")
    out = run_agent(inp, session_id="sess_reinject")
    assert out.answer.strip() != ""
    assert captured_sys
    assert any("[Nhắc lại chỉ dẫn]:" in s for s in captured_sys)


def test_end_to_end_graph_memory_flow():
    """Kiểm tra trọn vẹn luồng Agent Graph với recall, respond và store_extract."""
    # Lượt 1: Giới thiệu danh tính
    inp1 = Agent_Input(
        question="Chào bạn, tôi tên là Minh, tôi quản lý camera cổng chính",
        user_id="u_e2e_dong",
    )
    out1 = run_agent(inp1, session_id="sess_e2e_1")
    assert out1.answer.strip() != ""

    import time
    time.sleep(0.3)

    # Kiểm tra long-term memory đã có fact
    facts = recall_long_term("u_e2e_dong", "Minh cổng chính")
    assert len(facts) >= 1
    assert any("Minh" in f for f in facts)

    # Lượt 2: Hỏi lại danh tính trong phiên mới
    inp2 = Agent_Input(question="Tôi là ai?", user_id="u_e2e_dong")
    out2 = run_agent(inp2, session_id="sess_e2e_2")
    assert "Minh" in out2.answer

# ==============================================================================
# --- Sourced from test_frontend_memory_connect.py ---
# ==============================================================================

"""Unit and contract tests for Frontend Memory & Cache Hit connection (Phase 4 — Connect UI to data).

Validates:
1. index.html contains #memory-status-badge, #memory-status-text, and #btn-reset-memory.
2. style.css defines .badge-cache-hit, .btn-reset-memory, and .memory-badge.
3. app.js binds #btn-reset-memory to handleResetMemory.
4. handleResetMemory issues DELETE /api/memory?user_id=... and resets UI counter to 0.
5. app.js displays badge '⚡ Cache Hit' with class .badge-cache-hit when payload contains cache_hit: true.
6. fetchUserMemoryStatus fetches GET /api/memory?user_id=... and syncs facts count to UI.
7. Frontend static files (HTML, JS, CSS) are served with HTTP 200.
"""


from pathlib import Path
import re
import pytest
from fastapi.testclient import TestClient

from src.main import app

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"
APP_JS = FRONTEND_DIR / "app.js"
STYLE_CSS = FRONTEND_DIR / "style.css"


@pytest.fixture
def client():
    return TestClient(app)


def test_index_html_has_memory_elements():
    """index.html phải có đủ các element giao diện bộ nhớ (badge status và nút reset memory)."""
    assert INDEX_HTML.exists(), "frontend/index.html không tồn tại"
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="memory-status-badge"' in html, "Thiếu element #memory-status-badge trong index.html"
    assert 'id="memory-status-text"' in html, "Thiếu element #memory-status-text trong index.html"
    assert 'id="btn-reset-memory"' in html, "Thiếu element #btn-reset-memory trong index.html"
    assert "Reset Memory" in html, "Thiếu nhãn 'Reset Memory' trong index.html"


def test_style_css_has_memory_and_cache_badge_styles():
    """style.css phải chứa CSS selectors cho badge bộ nhớ, nút reset và huy hiệu Cache Hit."""
    assert STYLE_CSS.exists(), "frontend/style.css không tồn tại"
    css = STYLE_CSS.read_text(encoding="utf-8")

    assert ".memory-badge" in css, "Thiếu class .memory-badge trong style.css"
    assert ".btn-reset-memory" in css, "Thiếu class .btn-reset-memory trong style.css"
    assert ".badge-cache-hit" in css, "Thiếu class .badge-cache-hit trong style.css"
    # Kiểm tra màu sắc đặc trưng teal/cyan của Cache Hit
    assert "0d9488" in css or "10b981" in css, "style.css phải có màu nhận diện cho badge-cache-hit"


def test_app_js_wires_btn_reset_memory_to_handleResetMemory():
    """app.js phải map btnResetMemory từ DOM và gán sự kiện click handleResetMemory."""
    assert APP_JS.exists(), "frontend/app.js không tồn tại"
    js = APP_JS.read_text(encoding="utf-8")

    assert "btnResetMemory: document.getElementById('btn-reset-memory')" in js
    assert "el.btnResetMemory.addEventListener('click', handleResetMemory)" in js


def test_app_js_handleResetMemory_calls_delete_api():
    """handleResetMemory phải gửi DELETE /api/memory kèm user_id và gọi updateMemoryStatus(0)."""
    assert APP_JS.exists()
    js = APP_JS.read_text(encoding="utf-8")

    assert "async function handleResetMemory()" in js
    assert "/api/memory?user_id=" in js
    assert "method: 'DELETE'" in js
    assert "updateMemoryStatus(0)" in js
    assert "Đã xóa bộ nhớ" in js


def test_app_js_displays_cache_hit_badge():
    """app.js phải render thẻ .badge-cache-hit với nội dung '⚡ Cache Hit' khi có cờ cache_hit: true."""
    assert APP_JS.exists()
    js = APP_JS.read_text(encoding="utf-8")

    # Kiểm tra kiểm tra cờ cache_hit
    assert "cache_hit === true" in js
    # Kiểm tra chèn class badge-cache-hit
    assert "badge-cache-hit" in js
    # Kiểm tra icon và chữ tiếng Việt
    assert "⚡ Cache Hit" in js
    assert "Phản hồi tức thì từ bộ đệm TTL Cache" in js


def test_app_js_fetchUserMemoryStatus_syncs_memory_badge():
    """fetchUserMemoryStatus phải gọi GET /api/memory và đồng bộ số facts vào UI."""
    assert APP_JS.exists()
    js = APP_JS.read_text(encoding="utf-8")

    assert "async function fetchUserMemoryStatus()" in js
    assert "getApiEndpoint(`/api/memory?user_id=" in js
    assert "updateMemoryStatus" in js


def test_frontend_static_serving_of_assets(client):
    """Máy chủ backend phục vụ đúng mã nguồn tĩnh của Frontend."""
    # Trang chủ
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "Reset Memory" in res_index.text

    # File JS
    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "handleResetMemory" in res_js.text
    assert "⚡ Cache Hit" in res_js.text

    # File CSS
    res_css = client.get("/static/style.css")
    assert res_css.status_code == 200
    assert ".badge-cache-hit" in res_css.text

# ==============================================================================
# --- Sourced from test_product_user_isolation.py ---
# ==============================================================================


"""Comprehensive test suite for User Isolation (AC-2) — Phase 5 Validation.

Tiêu chuẩn nghiệm thu AC-2:
1. Mọi thao tác bộ nhớ phải cô lập theo user_id. Không bao giờ để rò rỉ fact của user này sang context của user khác.
2. Hai phiên chat song song với 2 user_id khác nhau: thông tin cá nhân của User A (tên, vai trò, ca trực, khu vực phụ trách)
   tuyệt đối không xuất hiện trong phản hồi hay ngữ cảnh của User B.
3. TTL Cache không cache các câu hỏi danh tính người dùng nhằm ngăn ngừa rò rỉ chéo giữa các user.
4. Reset Memory (DELETE /api/memory) của User A chỉ xóa dữ liệu của User A, không tác động đến User B.
5. Lịch sử hội thoại của User A được bảo vệ, User B không thể đọc được.
"""

from tests.support.sse import sse_answer

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.domain.agents.graph import (Agent_Input, run_agent)
from src.domain.agents.nodes.memory import recall_node
from src.infra.memory.longterm import clear_long_term, recall_long_term, save_to_long_term
from src.infra.memory.ttl_cache import clear_ttl_cache, make_cache_key, get_ttl_cached
from src.infra.session import create_session, append_session_messages


@pytest.fixture(autouse=True)
def cleanup_isolation_environment():
    """Dọn sạch bộ nhớ dài hạn và TTL cache trước và sau mỗi test case."""
    clear_long_term()
    clear_ttl_cache()
    yield
    clear_long_term()
    clear_ttl_cache()


@pytest.fixture
def client():
    return TestClient(app)


def test_two_users_chat_isolation_identity_not_leaked(client):
    """Kịch bản chính AC-2: User A và User B chat trong 2 phiên riêng biệt.
    
    Thông tin của User A tuyệt đối không bao giờ rò rỉ sang User B.
    """
    user_a = "user_alpha_an"
    user_b = "user_beta_binh"
    sess_a = "session_alpha_01"
    sess_b = "session_beta_01"

    # 1. User A giới thiệu tên và vai trò trong phiên của mình
    save_to_long_term(user_a, "Tôi tên là Nguyễn Văn An", category="identity")
    save_to_long_term(user_a, "Tôi phụ trách giám sát an ninh ca đêm khu vực cổng 1", category="role")

    # 2. User B (chưa giới thiệu bản thân) hỏi "Tôi là ai?"
    res_b1 = client.post("/api/agent/stream", json={
        "question": "Tôi là ai?",
        "session_id": sess_b,
        "user_id": user_b,
    })
    assert res_b1.status_code == 200
    ans_b1 = sse_answer(res_b1)
    # Xác nhận câu trả lời cho User B TUYỆT ĐỐI KHÔNG chứa danh tính của User A
    assert "Nguyễn Văn An" not in ans_b1
    assert "nguyen van an" not in ans_b1.lower()
    assert "cổng 1" not in ans_b1

    # 3. User B giới thiệu bản thân
    save_to_long_term(user_b, "Tôi tên là Trần Thị Bình", category="identity")
    save_to_long_term(user_b, "Tôi là ca trưởng ca sáng", category="role")

    # 4. User A hỏi lại "Tôi là ai?"
    res_a = client.post("/api/agent/stream", json={
        "question": "Tôi là ai?",
        "session_id": sess_a,
        "user_id": user_a,
    })
    assert res_a.status_code == 200
    ans_a = sse_answer(res_a)
    # User A nhận đúng thông tin của An, không có thông tin của Bình
    assert "Nguyễn Văn An" in ans_a or "cổng 1" in ans_a
    assert "Trần Thị Bình" not in ans_a
    assert "ca sáng" not in ans_a

    # 5. User B hỏi "Tôi là ai?"
    res_b2 = client.post("/api/agent/stream", json={
        "question": "Tôi là ai?",
        "session_id": sess_b,
        "user_id": user_b,
    })
    assert res_b2.status_code == 200
    ans_b2 = sse_answer(res_b2)
    # User B nhận đúng thông tin của Bình, không có thông tin của An
    assert "Trần Thị Bình" in ans_b2 or "ca sáng" in ans_b2
    assert "Nguyễn Văn An" not in ans_b2
    assert "cổng 1" not in ans_b2


def test_graph_recall_node_context_strictly_isolated():
    """Node recall_memory_node chỉ nạp facts của đúng user_id vào state context."""
    user_a = "user_guard_alpha"
    user_b = "user_guard_beta"

    save_to_long_term(user_a, "Tôi chuyên theo dõi camera nhiệt cổng 3")
    save_to_long_term(user_b, "Tôi chuyên xử lý cảnh báo xâm nhập hàng rào điện tử")

    # Chạy recall cho user A
    state_a = {"question": "tôi phụ trách gì", "user_id": user_a, "session_id": "s_a"}
    res_a = recall_node(state_a)
    memories_a = res_a.get("recalled_memories", [])

    assert any("cổng 3" in m for m in memories_a)
    assert not any("hàng rào" in m for m in memories_a)

    # Chạy recall cho user B
    state_b = {"question": "tôi phụ trách gì", "user_id": user_b, "session_id": "s_b"}
    res_b = recall_node(state_b)
    memories_b = res_b.get("recalled_memories", [])

    assert any("hàng rào" in m for m in memories_b)
    assert not any("cổng 3" in m for m in memories_b)


def test_ttl_cache_does_not_leak_identity_between_users(client):
    """TTL Cache bỏ qua câu hỏi danh tính cá nhân để tránh user_B trúng cache câu trả lời của user_A."""
    user_a = "user_alpha_vip"
    user_b = "user_beta_guest"
    save_to_long_term(user_a, "Tôi tên là Đỗ Minh Quân, Giám đốc an ninh")

    # User A hỏi "Tôi là ai?"
    res_a = client.post("/api/agent/stream", json={
        "question": "Tôi là ai?",
        "session_id": "sess_a",
        "user_id": user_a,
    })
    assert res_a.status_code == 200
    assert "Đỗ Minh Quân" in sse_answer(res_a)

    # Kiểm tra TTL Cache không lưu key này
    cache_key = make_cache_key("Tôi là ai?")
    assert get_ttl_cached(cache_key) is None

    # User B hỏi ngay sau đó cùng câu "Tôi là ai?"
    res_b = client.post("/api/agent/stream", json={
        "question": "Tôi là ai?",
        "session_id": "sess_b",
        "user_id": user_b,
    })
    assert res_b.status_code == 200
    ans_b = sse_answer(res_b)
    # User B không bị cache câu trả lời của User A
    assert "Đỗ Minh Quân" not in ans_b
    assert "Giám đốc an ninh" not in ans_b


def test_memory_api_isolation_and_delete_independence(client):
    """API GET và DELETE /api/memory chỉ tác động đến đúng user_id được chỉ định."""
    u1 = "operator_1"
    u2 = "operator_2"

    save_to_long_term(u1, "Fact của Operator 1: Trực camera số 5")
    save_to_long_term(u2, "Fact của Operator 2: Trực camera số 9")

    # GET u1 và u2
    resp_u1 = client.get(f"/api/memory?user_id={u1}").json()
    resp_u2 = client.get(f"/api/memory?user_id={u2}").json()

    assert resp_u1["total"] == 1
    assert "camera số 5" in resp_u1["facts"][0]
    assert resp_u2["total"] == 1
    assert "camera số 9" in resp_u2["facts"][0]

    # Reset memory của u1
    del_u1 = client.delete(f"/api/memory?user_id={u1}")
    assert del_u1.status_code == 200

    # Kiểm tra lại: u1 bị xóa, u2 vẫn còn nguyên
    after_u1 = client.get(f"/api/memory?user_id={u1}").json()
    assert after_u1["total"] == 0
    assert after_u1["facts"] == []

    after_u2 = client.get(f"/api/memory?user_id={u2}").json()
    assert after_u2["total"] == 1
    assert "camera số 9" in after_u2["facts"][0]


def test_sessions_message_history_user_isolation(client):
    """User B không thể truy cập hoặc đọc trộm tin nhắn từ session của User A."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    user_a = "user_owner_a"
    user_b = "user_intruder_b"

    # Tạo session cho User A
    sess_a = create_session(user_id=user_a, title="Phiên bảo mật của User A")
    sid_a = sess_a["id"]

    append_session_messages(sid_a, user_a, [
        {"role": "user", "content": "Khu vực bí mật là phòng máy chủ", "timestamp": now},
        {"role": "assistant", "content": "Đã ghi nhận khu vực phòng máy chủ.", "timestamp": now},
    ])

    # User A đọc thành công (200)
    res_a = client.get(f"/api/sessions/{sid_a}/messages?user_id={user_a}")
    assert res_a.status_code == 200
    assert len(res_a.json()["messages"]) == 2

    # User B cố tình đọc session của User A -> Bị từ chối (404 Not Found)
    res_b = client.get(f"/api/sessions/{sid_a}/messages?user_id={user_b}")
    assert res_b.status_code == 404
