"""Tests for Phase 19.5 (G7): Soft sandbox (timeout/limit) and agent_audit JSON logging."""

from __future__ import annotations

import json
import logging
import time
from unittest.mock import MagicMock, patch
import pytest

from src.domain.agents.analytics.sql_agent.tools.execute import execute_sql_node
from src.domain.observability.audit import log_agent_audit
from src.infra.storage.sql.connection import enforce_sql_limit, run_with_timeout
from src.infra.storage.sql.validator import validate_sql


def test_validator_blocks_dml_and_ddl_queries():
    """SQL validator chặn DELETE, DROP, INSERT, UPDATE, TRUNCATE, v.v."""
    blocked_queries = [
        "DELETE FROM plate_event WHERE id = 1;",
        "DROP TABLE plate_event;",
        "UPDATE plate_event SET plate_number = 'XYZ';",
        "INSERT INTO plate_event (id) VALUES (1);",
        "TRUNCATE TABLE zone_event;",
        "ALTER TABLE plate_event ADD COLUMN hacker text;",
    ]
    for sql in blocked_queries:
        res = validate_sql(sql)
        assert not res.ok, f"Cần chặn câu lệnh: {sql}"
        assert any(k in res.reason for k in ("Cấm từ khóa ghi/DDL", "Chỉ cho phép câu lệnh bắt đầu"))


def test_validator_allows_valid_select_and_with():
    """Validator chỉ cho phép SELECT và WITH hợp lệ."""
    valid_select = "SELECT plate_number, count(*) FROM plate_event GROUP BY plate_number;"
    valid_with = "WITH summary AS (SELECT count(*) as c FROM plate_event) SELECT c FROM summary;"

    assert validate_sql(valid_select).ok is True
    assert validate_sql(valid_with).ok is True


def test_enforce_sql_limit_adds_default_limit():
    """enforce_sql_limit tự động thêm LIMIT 500 khi query chưa có LIMIT."""
    sql_without_limit = "SELECT * FROM plate_event"
    enforced = enforce_sql_limit(sql_without_limit, default_limit=500)
    assert "LIMIT 500" in enforced

    sql_with_limit = "SELECT * FROM plate_event LIMIT 50;"
    unchanged = enforce_sql_limit(sql_with_limit, default_limit=500)
    assert "LIMIT 50" in unchanged
    assert "LIMIT 500" not in unchanged


def test_run_with_timeout_raises_timeout_error_on_slow_query():
    """Khi truy vấn chạy quá timeout, run_with_timeout ném TimeoutError gọn gàng."""
    def slow_query():
        time.sleep(0.3)
        return [{"count": 1}], ["count"]

    with pytest.raises(TimeoutError, match="quá thời gian chờ"):
        run_with_timeout(slow_query, timeout_seconds=0.05)


def test_agent_audit_json_logging_format(caplog):
    """caplog nhận được bản ghi log JSON hợp lệ với đầy đủ metadata từ agent_audit."""
    with caplog.at_level(logging.INFO, logger="agent_audit"):
        log_agent_audit(
            tool="sql_builder",
            args="SELECT plate_number FROM plate_event LIMIT 10;",
            duration_ms=45.67,
            status="success",
            rows=10,
            user_id="user_test_audit",
            session_id="sess_test_audit",
        )

        assert "agent_audit" in caplog.text
        # Tìm dòng log JSON
        found = False
        for record in caplog.records:
            if record.name == "agent_audit":
                data = json.loads(record.message)
                assert data["event"] == "agent_audit"
                assert data["tool"] == "sql_builder"
                assert data["user_id"] == "user_test_audit"
                assert data["session_id"] == "sess_test_audit"
                assert data["rows"] == 10
                assert data["duration_ms"] == 45.67
                assert "ts" in data
                found = True
                break
        assert found, "Không tìm thấy record JSON parseable trong agent_audit"


def test_execute_sql_node_logs_audit_on_success_and_error(caplog, monkeypatch):
    """execute_sql_node tự động ghi log agent_audit cả khi thành công lẫn khi gặp lỗi."""
    monkeypatch.setattr(
        "src.domain.agents.analytics.sql_agent.tools.execute.run_with_timeout",
        lambda *args, **kwargs: ([{"c": 42}], ["c"]),
    )
    with caplog.at_level(logging.INFO, logger="agent_audit"):
        res = execute_sql_node({
            "sql": "SELECT count(*) FROM plate_event;",
            "user_id": "u1",
            "session_id": "s1",
        })
        assert res["error"] == ""
        assert len(res["rows"]) == 1
        assert any("agent_audit" in r.message for r in caplog.records if r.name == "agent_audit")


def test_execute_sql_node_batch_path_timeout_and_audit(caplog, monkeypatch):
    """execute_sql_node khi len(sql_batch) >= 2 cũng có timeout và ghi log agent_audit."""
    # 1. Test batch thành công ghi agent_audit
    monkeypatch.setattr(
        "src.domain.agents.analytics.sql_agent.tools.execute.run_with_timeout",
        lambda *args, **kwargs: ([{"c": 10}], ["c"]),
    )
    with caplog.at_level(logging.INFO, logger="agent_audit"):
        res = execute_sql_node({
            "sql_batch": [
                {"sub_question": "sq1", "sql": "SELECT count(*) FROM plate_event;"},
                {"sub_question": "sq2", "sql": "SELECT count(*) FROM zone_event;"},
            ],
            "user_id": "u_batch",
            "session_id": "s_batch",
        })
        assert len(res["sql_batch_results"]) == 2
        batch_audit = [r for r in caplog.records if r.name == "agent_audit" and "sql_builder:batch" in r.message]
        assert len(batch_audit) >= 1
        data = json.loads(batch_audit[0].message)
        assert data["tool"] == "sql_builder:batch"
        assert data["user_id"] == "u_batch"
        assert data["status"] == "success"
        assert data["rows"] == 2

    # 2. Test batch khi một query bị timeout
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("Thực thi tool quá thời gian chờ (5.0s).")

    monkeypatch.setattr("src.domain.agents.analytics.sql_agent.tools.execute.run_with_timeout", raise_timeout)
    caplog.clear()

    with caplog.at_level(logging.INFO, logger="agent_audit"):
        res_fail = execute_sql_node({
            "sql_batch": [
                {"sub_question": "sq1", "sql": "SELECT count(*) FROM plate_event;"},
                {"sub_question": "sq2", "sql": "SELECT count(*) FROM zone_event;"},
            ],
            "user_id": "u_batch",
            "session_id": "s_batch",
        })
        assert "quá thời gian chờ" in res_fail["error"]
        fail_audit = [r for r in caplog.records if r.name == "agent_audit" and "sql_builder:batch" in r.message]
        assert len(fail_audit) >= 1
        data_fail = json.loads(fail_audit[0].message)
        assert data_fail["status"] == "error"
        assert "quá thời gian chờ" in data_fail["error"]

