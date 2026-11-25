"""Tests for Phase 19.6 (G10): Eval Gate, baseline comparison, and trajectory verification."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from eval.run import (
    DEFAULT_BASELINE_PATH,
    CaseEvalResult,
    PipelineResult,
    check_case,
    run,
)


def test_baseline_json_exists_and_valid():
    """File baseline.json phải tồn tại và chứa các metrics chuẩn."""
    assert DEFAULT_BASELINE_PATH.is_file(), "resource/eval/results/baseline.json phải tồn tại"
    data = json.loads(DEFAULT_BASELINE_PATH.read_text(encoding="utf-8"))
    assert "pass_rate" in data
    assert "total_cases" in data
    assert "total_pass" in data
    assert "difficulty_breakdown" in data
    assert "type_breakdown" in data
    assert data["pass_rate"] >= 0.85


def test_trajectory_validation_in_check_case():
    """Kiểm tra đối chiếu expected_route và expected_agents trong check_case."""
    case_with_route = {
        "id": "test_traj_01",
        "expected_route": ["guardrail_input", "recall", "rewrite", "top_supervisor", "analytics_team"],
        "expected_agents": ["query_data"],
    }

    # Case 1: Trajectory khớp
    res_ok = PipelineResult(
        answer="ok",
        tools={"query_data"},
        trajectory=["guardrail_input", "recall", "rewrite", "classify", "top_supervisor", "analytics_team", "query_data", "respond"],
    )
    failures_ok = check_case(case_with_route, res_ok)
    assert len(failures_ok) == 0

    # Case 2: Trajectory thiếu node bắt buộc
    res_missing = PipelineResult(
        answer="ok",
        tools={"query_data"},
        trajectory=["guardrail_input", "respond"],
    )
    failures_missing = check_case(case_with_route, res_missing)
    assert any("thiếu expected_route node" in f for f in failures_missing)

    # Case 3: Dataset không có expected_route -> không báo lỗi
    case_no_route = {"id": "test_no_route"}
    assert len(check_case(case_no_route, res_missing)) == 0


def test_eval_gate_passes_when_at_or_above_baseline(tmp_path, monkeypatch):
    """Eval Gate trả về 0 khi pass rate >= baseline - 2pp."""
    dummy_baseline = tmp_path / "baseline.json"
    dummy_baseline.write_text(json.dumps({"pass_rate": 0.80}), encoding="utf-8")

    # Giả lập dataset 10 cases
    dummy_dataset = tmp_path / "dataset.yaml"
    dummy_dataset.write_text(
        """
dataset: test
version: 1
cases:
  - id: c1
    question: q1
    slice: { type: lookup, difficulty: easy }
  - id: c2
    question: q2
    slice: { type: lookup, difficulty: easy }
""",
        encoding="utf-8",
    )

    # Mock pipeline result thành công (pass rate 100% > 78%)
    monkeypatch.setattr(
        "eval.run.run_pipeline",
        lambda *args, **kwargs: PipelineResult(answer="ok", tools={"count_vehicle_flow"}),
    )
    monkeypatch.setattr("eval.run.check_case", lambda *args, **kwargs: [])

    exit_code = run(
        dummy_dataset,
        output_path=tmp_path / "report.md",
        use_judge=False,
        offline=True,
        gate=True,
        baseline_path=dummy_baseline,
    )
    assert exit_code == 0


def test_eval_gate_fails_when_below_baseline_minus_2pp(tmp_path, monkeypatch):
    """Eval Gate trả về 1 khi pass rate < baseline - 2pp (vd: 50% vs baseline 80%)."""
    dummy_baseline = tmp_path / "baseline.json"
    dummy_baseline.write_text(json.dumps({"pass_rate": 0.80}), encoding="utf-8")

    dummy_dataset = tmp_path / "dataset.yaml"
    dummy_dataset.write_text(
        """
dataset: test
version: 1
cases:
  - id: c1
    question: q1
    slice: { type: lookup, difficulty: easy }
  - id: c2
    question: q2
    slice: { type: lookup, difficulty: easy }
""",
        encoding="utf-8",
    )

    # Mock case 1 pass, case 2 fail -> pass rate = 50% (< 78%)
    calls = 0

    def mock_check(case, *args, **kwargs):
        nonlocal calls
        calls += 1
        return [] if calls == 1 else ["Intent mismatch"]

    monkeypatch.setattr(
        "eval.run.run_pipeline",
        lambda *args, **kwargs: PipelineResult(answer="ok", tools=set()),
    )
    monkeypatch.setattr("eval.run.check_case", mock_check)

    exit_code = run(
        dummy_dataset,
        output_path=tmp_path / "report.md",
        use_judge=False,
        offline=True,
        gate=True,
        baseline_path=dummy_baseline,
    )
    assert exit_code == 1


def test_eval_gate_fails_when_baseline_missing(tmp_path, monkeypatch):
    """Eval Gate khi thiếu baseline file không được tự ý ghi baseline hay pass (bypass); phải fail với exit code 1."""
    non_existent_baseline = tmp_path / "does_not_exist.json"

    dummy_dataset = tmp_path / "dataset.yaml"
    dummy_dataset.write_text(
        """
dataset: test
version: 1
cases:
  - id: c1
    question: q1
    slice: { type: lookup, difficulty: easy }
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "eval.run.run_pipeline",
        lambda *args, **kwargs: PipelineResult(answer="ok", tools=set()),
    )
    monkeypatch.setattr("eval.run.check_case", lambda *args, **kwargs: [])

    exit_code = run(
        dummy_dataset,
        output_path=tmp_path / "report.md",
        use_judge=False,
        offline=True,
        gate=True,
        baseline_path=non_existent_baseline,
    )
    assert exit_code == 1
    assert not non_existent_baseline.exists(), "Không được tự ý tạo baseline khi chỉ dùng cờ --gate"

