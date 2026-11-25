"""Unit tests for Phase 19.10 G17 feedback to golden dataset pipeline.

Tests:
- 2 feedback giả (1 up/positive, 1 down/negative) -> draft chứa đúng 1 case.
- File YAML sinh ra nạp lại được (valid YAML), đúng cấu trúc schema draft.
- review: pending, slice để trống cho reviewer duyệt.
- Xử lý CLI arguments (--output, --date, --input-file).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import yaml

from scripts.feedback_to_golden import (
    extract_negative_feedback,
    convert_feedback_to_draft_cases,
    generate_draft_golden_yaml,
    main,
)


def test_feedback_to_golden_two_cases_one_down(tmp_path: Path):
    """Tiêu chí chính: 2 feedback giả (1 up, 1 down) -> draft chứa đúng 1 case; YAML load được."""
    mock_feedbacks = [
        {
            "id": "fb_001",
            "timestamp": "2026-11-23T10:00:00Z",
            "rating": "positive",
            "question": "Hôm nay có bao nhiêu lượt xe vào?",
            "answer": "Có 120 xe vào cổng.",
            "feedback_reason": None,
        },
        {
            "id": "fb_002",
            "timestamp": "2026-11-23T10:05:00Z",
            "rating": "negative",
            "question": "Biển số 15K40139 đi qua cổng nào?",
            "answer": "Không tìm thấy dữ liệu.",
            "feedback_reason": "Thực tế xe có đi qua cổng số 2 lúc 8h sáng.",
        },
    ]

    out_file = tmp_path / "draft-test.yaml"
    generated_path, count = generate_draft_golden_yaml(
        feedback_records=mock_feedbacks,
        output_path=out_file,
        date_str="20261123",
    )

    assert generated_path == out_file
    assert count == 1
    assert out_file.exists()

    # YAML load được và hợp lệ
    with open(out_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict)
    assert data["dataset"] == "agent_stat"
    assert data["version"] == "draft-20261123"
    assert data["review"] == "pending"
    assert data["total_cases"] == 1
    assert len(data["cases"]) == 1

    case = data["cases"][0]
    assert case["id"] == "draft_20261123_001"
    assert case["feedback_id"] == "fb_002"
    assert case["question"] == "Biển số 15K40139 đi qua cổng nào?"
    assert case["observed_answer"] == "Không tìm thấy dữ liệu."
    assert case["feedback_reason"] == "Thực tế xe có đi qua cổng số 2 lúc 8h sáng."
    assert case["expected"] == ""
    assert case["review"] == "pending"

    # Slice trống cho người duyệt
    assert "slice" in case
    assert case["slice"]["type"] == ""
    assert case["slice"]["difficulty"] == ""
    assert case["slice"]["multihop"] is None
    assert case["slice"]["out_of_scope"] is None


def test_feedback_to_golden_empty_or_all_positive(tmp_path: Path):
    """Khi chỉ có positive feedback hoặc danh sách trống, draft YAML có 0 case."""
    mock_feedbacks = [
        {
            "id": "fb_pos_1",
            "rating": "positive",
            "question": "Tra cứu xe",
            "answer": "Kết quả...",
        }
    ]

    out_file = tmp_path / "draft-empty.yaml"
    _, count = generate_draft_golden_yaml(
        feedback_records=mock_feedbacks,
        output_path=out_file,
        date_str="20261123",
    )
    assert count == 0

    with open(out_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["total_cases"] == 0
    assert data["cases"] == []


def test_feedback_to_golden_cli_main(tmp_path: Path):
    """Kiểm tra chạy qua CLI main với file input json."""
    input_file = tmp_path / "feedbacks.json"
    output_file = tmp_path / "draft-cli.yaml"

    sample_data = [
        {"id": "fb_1", "rating": "negative", "question": "Hỏi A", "answer": "Đáp A", "feedback_reason": "Sai"},
        {"id": "fb_2", "rating": "positive", "question": "Hỏi B", "answer": "Đáp B"},
        {"id": "fb_3", "rating": "down", "question": "Hỏi C", "answer": "Đáp C", "feedback_reason": "Chưa đủ ý"},
    ]
    input_file.write_text(json.dumps(sample_data, ensure_ascii=False), encoding="utf-8")

    exit_code = main([
        "--input-file", str(input_file),
        "--output", str(output_file),
        "--date", "20261123",
    ])
    assert exit_code == 0
    assert output_file.exists()

    with open(output_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert len(data["cases"]) == 2
    assert data["cases"][0]["id"] == "draft_20261123_001"
    assert data["cases"][1]["id"] == "draft_20261123_002"
