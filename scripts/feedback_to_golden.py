"""Script trích xuất thumbs-down (negative human feedback) thành draft golden YAML (G17).

Đọc các bản ghi phản hồi tiêu cực từ storage feedback (Postgres / local SQLite / JSON)
hoặc từ file input được chỉ định, lọc các case thumbs-down (rating == 'negative'),
và tạo file draft golden YAML: `resource/eval/datasets/agent_stat/draft-<date>.yaml`
với trạng thái `review: pending`, `slice` để trống cho kiểm toán viên/reviewer
đối chiếu theo `resource/eval/AUDIT-CHECKLIST.md` trước khi merge vào golden set v+1.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any

import yaml

# Root của project
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_DEFAULT_OUTPUT_DIR = _ROOT / "resource" / "eval" / "datasets" / "agent_stat"

logger = logging.getLogger(__name__)


def extract_negative_feedback(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lọc các bản ghi feedback có rating là 'negative' (thumbs-down)."""
    negative_records = []
    for r in records:
        rating = str(r.get("rating", "")).strip().lower()
        if rating in ("negative", "down", "thumbs_down", "dislike"):
            negative_records.append(r)
    return negative_records


def convert_feedback_to_draft_cases(
    negative_records: list[dict[str, Any]], date_str: str
) -> list[dict[str, Any]]:
    """Chuyển đổi danh sách bản ghi thumbs-down thành các case nháp cho golden dataset."""
    cases = []
    for idx, rec in enumerate(negative_records, start=1):
        case_id = f"draft_{date_str}_{idx:03d}"
        cases.append(
            {
                "id": case_id,
                "feedback_id": rec.get("id") or f"fb_unknown_{idx}",
                "timestamp": rec.get("timestamp") or "",
                "question": rec.get("question", ""),
                "expected": "",  # Để trống cho reviewer điền ground truth
                "observed_answer": rec.get("answer", ""),
                "feedback_reason": rec.get("feedback_reason", ""),
                "review": "pending",
                "slice": {
                    "type": "",  # lookup | comparison | out_of_scope | injection | rbac
                    "difficulty": "",  # easy | medium | hard
                    "multihop": None,
                    "out_of_scope": None,
                },
                "must_include_tool": [],
            }
        )
    return cases


def generate_draft_golden_yaml(
    feedback_records: list[dict[str, Any]] | None = None,
    output_path: Path | str | None = None,
    date_str: str | None = None,
) -> tuple[Path, int]:
    """Tạo file draft golden YAML từ các bản ghi feedback thumbs-down.

    Returns:
        tuple[Path, int]: (đường dẫn file draft đã tạo, số lượng case thumbs-down được trích xuất)
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    if output_path is None:
        target_path = _DEFAULT_OUTPUT_DIR / f"draft-{date_str}.yaml"
    else:
        target_path = Path(output_path)

    target_path.parent.mkdir(parents=True, exist_ok=True)

    if feedback_records is None:
        from src.domain.observability.feedback import get_all_feedback

        feedback_records = get_all_feedback()

    negatives = extract_negative_feedback(feedback_records)
    cases = convert_feedback_to_draft_cases(negatives, date_str)

    data = {
        "dataset": "agent_stat",
        "version": f"draft-{date_str}",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "review": "pending",
        "source": "thumbs_down_feedback",
        "total_cases": len(cases),
        "audit_checklist": "resource/eval/AUDIT-CHECKLIST.md",
        "cases": cases,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    return target_path, len(cases)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract thumbs-down feedback into draft golden YAML (G17)."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to output YAML file (default: resource/eval/datasets/agent_stat/draft-<date>.yaml)",
    )
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        default=None,
        help="Date string to use in version/id (e.g. 20261123, defaults to today)",
    )
    parser.add_argument(
        "--input-file",
        "-i",
        type=str,
        default=None,
        help="Optional path to a JSON file containing feedback records instead of default storage",
    )

    args = parser.parse_args(argv)

    records = None
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: Input file {input_path} does not exist.", file=sys.stderr)
            return 1
        with open(input_path, "r", encoding="utf-8") as f:
            records = json.load(f)

    out_file, count = generate_draft_golden_yaml(
        feedback_records=records,
        output_path=args.output,
        date_str=args.date,
    )
    print(f"Generated draft golden YAML at: {out_file} ({count} thumbs-down cases extracted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
