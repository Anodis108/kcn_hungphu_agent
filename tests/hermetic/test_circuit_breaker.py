"""Unit tests cho Circuit Breaker (Phase 20.4 / G16).

Kiểm tra:
1. Chuyển trạng thái: CLOSED -> 5 lỗi liên tiếp -> OPEN -> lần 6 không gọi hàm thật.
2. Sau reset timeout -> HALF-OPEN -> 1 thành công -> CLOSED.
3. HALF-OPEN gặp lỗi -> quay lại OPEN.
4. LLM primary breaker OPEN -> nhảy thẳng fallback không gọi primary.
5. SQL breaker OPEN -> fail-fast với thông báo thân thiện "dữ liệu tạm thời không khả dụng".
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.infra.resilience.breaker import (
    CircuitBreaker,
    CircuitState,
    get_llm_breaker,
    get_sql_breaker,
)
from src.shared.models_config import ModelTarget


@pytest.fixture(autouse=True)
def reset_singleton_breakers():
    """Reset các singleton breaker sau mỗi test case."""
    yield
    get_llm_breaker().reset()
    get_sql_breaker().reset()


def test_circuit_breaker_state_transitions(caplog):
    """5 lỗi liên tiếp -> OPEN; lần 6 không cho gọi; sau reset -> HALF-OPEN -> 1 thành công -> CLOSED."""
    caplog.set_level("INFO")
    breaker = CircuitBreaker(name="test_service", fail_threshold=5, reset_seconds=30.0)

    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request() is True

    # 4 lỗi liên tiếp -> vẫn CLOSED
    for i in range(4):
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.allow_request() is True

    # Lỗi thứ 5 -> mở mạch (OPEN)
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert "circuit_open: breaker=test_service reached 5 consecutive failures" in caplog.text

    # Lần thứ 6 -> không cho phép gọi (fail-fast)
    assert breaker.allow_request() is False

    # Giả lập thời gian trôi qua quá reset_seconds (35s)
    current_time = time.time()
    with patch("time.time", return_value=current_time + 35.0):
        # Kiểm tra chuyển sang HALF_OPEN
        assert breaker.allow_request() is True
        assert breaker.state == CircuitState.HALF_OPEN
        assert "circuit_half_open" in caplog.text

        # 1 thành công trong probe -> đóng mạch trở lại CLOSED
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert "circuit_close: breaker=test_service recovered from half-open to closed" in caplog.text


def test_circuit_breaker_half_open_failure_reopens():
    """Nếu probe trong trạng thái HALF_OPEN thất bại -> ngay lập tức quay lại OPEN."""
    breaker = CircuitBreaker(name="test_probe_fail", fail_threshold=3, reset_seconds=10.0)

    for _ in range(3):
        breaker.record_failure()
    assert breaker.state == CircuitState.OPEN

    # Chuyển sang HALF_OPEN khi hết timeout
    current_time = time.time()
    with patch("time.time", return_value=current_time + 15.0):
        assert breaker.allow_request() is True
        assert breaker.state == CircuitState.HALF_OPEN

        # Thất bại ở probe call
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert breaker.allow_request() is False


def test_llm_primary_breaker_open_jumps_to_fallback(caplog):
    """Khi primary LLM breaker bị OPEN, invoke_text và invoke_with_tools nhảy thẳng fallback mà không gọi primary."""
    from src.infra.llm.completion import invoke_text, invoke_with_tools

    llm_breaker = get_llm_breaker()
    llm_breaker.reset()

    # Kích hoạt 5 lỗi liên tiếp trên primary LLM
    for _ in range(5):
        llm_breaker.record_failure()
    assert llm_breaker.state == CircuitState.OPEN

    mock_primary_target = ModelTarget(provider="openai", model="primary-gpt", base_url=None, api_key="k1", timeout=15.0)
    mock_fallback_target = ModelTarget(provider="self_hosted", model="fallback-qwen", base_url="http://mock", api_key="k2", timeout=15.0)

    mock_primary_llm = MagicMock()
    mock_fallback_llm = MagicMock()
    mock_fallback_resp = MagicMock(content="Câu trả lời từ fallback", usage_metadata={"total_tokens": 10})
    mock_fallback_llm.invoke.return_value = mock_fallback_resp

    def mock_base_llm(*args, **kwargs):
        if kwargs.get("model_override") == "primary-gpt":
            return mock_primary_llm
        return mock_fallback_llm

    with patch("src.shared.models_config.get_model_targets", return_value=[mock_primary_target, mock_fallback_target]), \
         patch("src.infra.llm.completion.base_llm", side_effect=mock_base_llm):

        # Lần gọi thứ 6: invoke_text
        caplog.clear()
        caplog.set_level("WARNING")
        result = invoke_text(system_prompt="sys", user_prompt="user", substep=None)

        # Primary LLM tuyệt đối không được invoke
        mock_primary_llm.invoke.assert_not_called()
        # Fallback LLM được invoke và trả về kết quả
        mock_fallback_llm.invoke.assert_called_once()
        assert result == "Câu trả lời từ fallback"
        assert "circuit breaker is OPEN; jumping to fallback=fallback-qwen" in caplog.text


def test_sql_breaker_open_returns_friendly_message():
    """Khi SQL breaker OPEN, get_connection ném lỗi thân thiện fail-fast 'dữ liệu tạm thời không khả dụng'."""
    from src.infra.storage.sql.connection import get_connection
    from src.shared.settings import settings

    sql_breaker = get_sql_breaker()
    sql_breaker.reset()

    # Kích hoạt 5 lỗi liên tiếp cho SQL breaker
    for _ in range(5):
        sql_breaker.record_failure()
    assert sql_breaker.state == CircuitState.OPEN

    with patch("psycopg2.connect") as mock_connect:
        with pytest.raises(RuntimeError) as exc_info:
            with get_connection(settings.db_name_its):
                pass

        # psycopg2.connect không hề được gọi (fail-fast)
        mock_connect.assert_not_called()

        # Thông điệp thân thiện theo yêu cầu spec
        err_msg = str(exc_info.value)
        assert "dữ liệu tạm thời không khả dụng" in err_msg.lower()


def test_execute_sql_with_sql_breaker_open():
    """execute_sql nhận diện lỗi khi breaker open và không crash 500."""
    from src.infra.storage.sql.executor import execute_sql

    sql_breaker = get_sql_breaker()
    sql_breaker.reset()

    # Ép breaker sang OPEN
    for _ in range(5):
        sql_breaker.record_failure()
    assert sql_breaker.state == CircuitState.OPEN

    with patch("src.shared.settings.settings.db_host", "127.0.0.1"), \
         patch("src.shared.settings.settings.db_user", "agent_readonly"), \
         patch("psycopg2.connect") as mock_connect:

        with pytest.raises(RuntimeError) as exc_info:
            execute_sql("SELECT count(*) FROM plate_event;")

        mock_connect.assert_not_called()
        assert "dữ liệu tạm thời không khả dụng" in str(exc_info.value).lower()
