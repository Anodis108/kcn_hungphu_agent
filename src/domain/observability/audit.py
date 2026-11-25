"""Agent tool audit logging — JSON 1 dòng/tool call (Phase 19.5 / G7).

Không log secrets, credentials hoặc full PII.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.domain.observability.redaction import redact_text

logger = logging.getLogger("agent_audit")

MAX_ARGS_LEN = 200


def truncate_and_redact_args(args: Any) -> str:
    """Rút gọn và ẩn PII trong tham số gọi tool."""
    raw = json.dumps(args, ensure_ascii=False, default=str) if not isinstance(args, str) else args
    cleaned = redact_text(raw)
    if len(cleaned) > MAX_ARGS_LEN:
        return cleaned[: MAX_ARGS_LEN - 3] + "..."
    return cleaned


def log_agent_audit(
    *,
    tool: str,
    args: Any,
    duration_ms: float,
    status: str,
    rows: int = 0,
    user_id: str = "default",
    session_id: str = "default",
    error: str | None = None,
) -> dict[str, Any]:
    """Ghi một dòng JSON audit log vào logger `agent_audit`."""
    record = {
        "event": "agent_audit",
        "ts": time.time(),
        "user_id": (user_id or "default").strip(),
        "session_id": (session_id or "default").strip(),
        "tool": tool,
        "args": truncate_and_redact_args(args),
        "duration_ms": round(duration_ms, 2),
        "status": status,
        "rows": int(rows),
    }
    if error:
        record["error"] = redact_text(str(error)[:150])

    logger.info(json.dumps(record, ensure_ascii=False))
    return record
