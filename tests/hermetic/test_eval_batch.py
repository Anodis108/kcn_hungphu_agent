"""Tests for Phase 19.7 (G11): Offline Batch API runner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from eval.batch import (
    build_batch_requests_from_dataset,
    get_batch_client,
    main,
    submit_and_poll_batch,
    write_jsonl,
)
from src.shared.models_config import ModelTarget


def test_build_batch_requests_from_dataset_standard(tmp_path: Path):
    """Kiểm tra build requests JSONL từ dataset yaml chuẩn."""
    dummy_yaml = tmp_path / "dataset.yaml"
    dummy_yaml.write_text(
        """
dataset: agent_stat
version: 1
cases:
  - id: case_01
    question: "Có bao nhiêu xe vào?"
    expected: "10 xe"
  - id: case_02
    question: "Có bao nhiêu xe ra?"
    expected: "5 xe"
""",
        encoding="utf-8",
    )

    requests = build_batch_requests_from_dataset(dummy_yaml, model="gpt-4o-mini", is_judge=False)
    assert len(requests) == 2

    # Kiểm tra cấu trúc dòng 1
    r1 = requests[0]
    assert r1["custom_id"] == "case_01"
    assert r1["method"] == "POST"
    assert r1["url"] == "/v1/chat/completions"
    assert r1["body"]["model"] == "gpt-4o-mini"
    assert r1["body"]["messages"][1]["content"] == "Có bao nhiêu xe vào?"


def test_build_batch_requests_judge_format(tmp_path: Path):
    """Kiểm tra build requests cho LLM as a Judge."""
    dummy_yaml = tmp_path / "dataset.yaml"
    dummy_yaml.write_text(
        """
dataset: agent_stat
version: 1
cases:
  - id: judge_case_01
    question: "Khu vực nào an toàn nhất?"
    expected: "Khu A"
""",
        encoding="utf-8",
    )

    requests = build_batch_requests_from_dataset(dummy_yaml, model="Qwen/Qwen2.5-7B-Instruct", is_judge=True)
    assert len(requests) == 1
    r = requests[0]
    assert r["custom_id"] == "judge_case_01"
    assert "LLM as a Judge" in r["body"]["messages"][0]["content"]
    assert "Kỳ vọng:\nKhu A" in r["body"]["messages"][1]["content"]


def test_write_jsonl(tmp_path: Path):
    """Kiểm tra ghi file JSONL."""
    requests = [
        {"custom_id": "c1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "m"}},
        {"custom_id": "c2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "m"}},
    ]
    out_file = tmp_path / "sub" / "requests.jsonl"
    written = write_jsonl(requests, out_file)
    assert written.is_file()

    lines = written.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["custom_id"] == "c1"
    assert json.loads(lines[1])["custom_id"] == "c2"


def test_batch_main_dry_run_no_network(tmp_path: Path):
    """Kiểm tra cờ --dry-run: tạo file JSONL nhưng không gọi API mạng."""
    dummy_yaml = tmp_path / "dataset.yaml"
    dummy_yaml.write_text(
        """
dataset: test
version: 1
cases:
  - id: test_dry_01
    question: "Hỏi kiểm thử dry run"
""",
        encoding="utf-8",
    )

    out_dir = tmp_path / "results"
    exit_code = main(["--dataset", str(dummy_yaml), "--output-dir", str(out_dir), "--dry-run"])
    assert exit_code == 0

    # Phải có file batch-input-*.jsonl được tạo trong out_dir
    jsonl_files = list(out_dir.glob("batch-input-*.jsonl"))
    assert len(jsonl_files) == 1
    content = jsonl_files[0].read_text(encoding="utf-8")
    assert "test_dry_01" in content


def test_submit_and_poll_batch_mocked(tmp_path: Path):
    """Kiểm tra submit và polling với mock client OpenAI."""
    mock_client = MagicMock()

    # Mock file upload
    mock_file = MagicMock()
    mock_file.id = "file-abc123xyz"
    mock_client.files.create.return_value = mock_file

    # Mock batch create
    mock_batch = MagicMock()
    mock_batch.id = "batch_test_789"
    mock_batch.status = "validating"
    mock_client.batches.create.return_value = mock_batch

    # Mock batch retrieve (lần 1: in_progress, lần 2: completed)
    mock_batch_progress = MagicMock(status="in_progress")
    mock_batch_done = MagicMock(status="completed", output_file_id="file-out-456")
    mock_client.batches.retrieve.side_effect = [mock_batch_progress, mock_batch_done]

    # Mock file content download
    mock_content = MagicMock()
    mock_content.read.return_value = b'{"custom_id": "c1", "response": "ok"}\n'
    mock_client.files.content.return_value = mock_content

    input_jsonl = tmp_path / "input.jsonl"
    input_jsonl.write_text('{"custom_id": "c1"}\n', encoding="utf-8")
    out_dir = tmp_path / "results"

    result_file = submit_and_poll_batch(
        input_jsonl,
        output_dir=out_dir,
        poll_interval_s=0.01,
        max_wait_s=5.0,
        client=mock_client,
    )

    assert result_file.is_file()
    assert result_file.name == "batch-batch_test_789.jsonl"
    assert result_file.read_text(encoding="utf-8") == '{"custom_id": "c1", "response": "ok"}\n'
