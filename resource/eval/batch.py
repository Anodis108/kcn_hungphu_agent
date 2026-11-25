"""Offline Batch API runner for LLM evaluation and judge scoring (Phase 19.7 - G11).

Chức năng:
1. Đọc golden dataset (YAML) hoặc evaluation results.
2. Build JSONL request (OpenAI Batch API format: /v1/chat/completions) cho golden eval hoặc judge scoring.
3. Submit batch job tới provider (lấy config từ config/models.yaml).
4. Poll trạng thái batch job cho tới khi hoàn tất.
5. Tải về và ghi kết quả vào resource/eval/results/batch-<id>.jsonl / .json.
6. Hỗ trợ --dry-run: chỉ build file JSONL trên đĩa, kiểm tra cú pháp và thoát mà không gọi mạng.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.shared.models_config import ModelTarget, load_models_config

logger = logging.getLogger(__name__)

DEFAULT_DATASET = Path("resource/eval/datasets/agent_stat/v1.yaml")
DEFAULT_RESULTS_DIR = Path("resource/eval/results")

_JUDGE_SYSTEM_PROMPT = """Bạn là chuyên gia giám khảo (LLM as a Judge) đánh giá chất lượng phản hồi của trợ lý AI giám sát camera VMS KCN Hưng Phú.

Nhiệm vụ: Chấm điểm câu trả lời của AI trên thang điểm 1 đến 5 và giải thích lý do ngắn gọn.
Bạn bắt buộc phải trả về DUY NHẤT một đối tượng JSON hợp lệ:
{"score": <số nguyên từ 1 đến 5>, "reason": "<lý do ngắn gọn bằng tiếng Việt>"}"""


def build_batch_requests_from_dataset(
    dataset_path: Path,
    model: str = "gpt-4o-mini",
    *,
    is_judge: bool = False,
) -> list[dict[str, Any]]:
    """Tạo danh sách request lines theo format OpenAI Batch API từ dataset YAML."""
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset file không tồn tại: {dataset_path}")

    raw_data = yaml.safe_load(dataset_path.read_text(encoding="utf-8")) or {}
    cases = raw_data.get("cases", [])
    requests: list[dict[str, Any]] = []

    for case in cases:
        case_id = case.get("id", f"case_{len(requests)}")
        question = case.get("question", "")
        expected = case.get("expected", "")

        if is_judge:
            # Build prompt cho LLM-as-a-judge
            user_content = f"Câu hỏi:\n{question}\n\nKỳ vọng:\n{expected}\n"
            messages = [
                {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
        else:
            # Direct prompt cho model eval
            messages = [
                {"role": "system", "content": "Bạn là trợ lý AI giám sát camera và thống kê xe KCN Hưng Phú."},
                {"role": "user", "content": question},
            ]

        req_line = {
            "custom_id": str(case_id),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": 1024,
            },
        }
        requests.append(req_line)

    return requests


def write_jsonl(requests: list[dict[str, Any]], output_path: Path) -> Path:
    """Ghi danh sách requests thành file JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return output_path


def get_batch_client(target: ModelTarget | None = None) -> Any:
    """Khởi tạo OpenAI client từ cấu hình ModelTarget."""
    from openai import OpenAI

    cfg = target or load_models_config().primary
    api_key = cfg.api_key
    base_url = cfg.base_url

    client_kwargs: dict[str, Any] = {"api_key": api_key, "timeout": cfg.timeout}
    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAI(**client_kwargs)


def submit_and_poll_batch(
    jsonl_file: Path,
    output_dir: Path = DEFAULT_RESULTS_DIR,
    target: ModelTarget | None = None,
    poll_interval_s: float = 2.0,
    max_wait_s: float = 300.0,
    client: Any | None = None,
) -> Path:
    """Submit JSONL file lên Batch API, poll trạng thái và lưu kết quả."""
    if client is None:
        client = get_batch_client(target)

    # 1. Upload file
    with jsonl_file.open("rb") as f:
        batch_input_file = client.files.create(file=f, purpose="batch")
    file_id = batch_input_file.id
    logger.info("Uploaded batch file ID: %s", file_id)

    # 2. Tạo batch
    batch = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch_id = batch.id
    logger.info("Created batch ID: %s (status: %s)", batch_id, batch.status)

    # 3. Poll
    start_time = time.time()
    while True:
        status_obj = client.batches.retrieve(batch_id)
        current_status = status_obj.status
        logger.info("Batch %s status: %s", batch_id, current_status)

        if current_status == "completed":
            output_file_id = status_obj.output_file_id
            content_resp = client.files.content(output_file_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / f"batch-{batch_id}.jsonl"
            out_path.write_bytes(content_resp.read() if hasattr(content_resp, "read") else content_resp.content)
            logger.info("Saved batch results to %s", out_path)
            return out_path
        elif current_status in ("failed", "expired", "cancelled"):
            error_details = getattr(status_obj, "errors", "unknown error")
            raise RuntimeError(f"Batch {batch_id} kết thúc thất bại: {current_status} - {error_details}")

        if time.time() - start_time > max_wait_s:
            raise TimeoutError(f"Hết thời gian chờ ({max_wait_s}s) cho batch {batch_id}")

        time.sleep(poll_interval_s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline Batch API runner (Phase 19.7 - G11)")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Đường dẫn file YAML dataset (mặc định: resource/eval/datasets/agent_stat/v1.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Thư mục lưu kết quả (mặc định: resource/eval/results)",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Build prompt cho LLM as a Judge thay vì prompt hỏi agent thông thường",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ build file JSONL trên đĩa, không thực hiện gọi API mạng",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Tên model (nếu bỏ trống sẽ lấy từ config/models.yaml)",
    )

    args = parser.parse_args(argv)

    cfg = load_models_config().primary
    model_name = args.model or cfg.model

    print(f"Building batch requests from dataset: {args.dataset}")
    requests = build_batch_requests_from_dataset(args.dataset, model=model_name, is_judge=args.judge)
    print(f"Total requests generated: {len(requests)}")

    # Ghi file JSONL request
    jsonl_filename = f"batch-input-{int(time.time())}.jsonl"
    jsonl_path = args.output_dir / jsonl_filename
    write_jsonl(requests, jsonl_path)
    print(f"Đã lưu request file: {jsonl_path}")

    if args.dry_run:
        print("✅ [--dry-run]: Build JSONL thành công. Không gửi yêu cầu tới API.")
        return 0

    print("Submitting batch request to API...")
    try:
        out_file = submit_and_poll_batch(jsonl_path, output_dir=args.output_dir, target=cfg)
        print(f"✅ Hoàn tất! Kết quả đã được lưu tại: {out_file}")
        return 0
    except Exception as exc:
        print(f"❌ Lỗi khi thực hiện batch API: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
