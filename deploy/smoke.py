"""Smoke test after local deploy (Phase 21.3).

Default path (cheap, no LLM call for the ask step):
    GET /api/health → 200
    GET /ready      → 200

Optional deeper check (needs a live agent stack):
    python deploy/smoke.py --url http://localhost:8000 --ask

Exit code ≠ 0 on any failure (for release.sh / cd.yml).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import httpx

# Golden out-of-scope case agent_stat_025 — deterministic refuse, no SQL.
KNOWN_QUESTION = "Thời tiết Hà Nội hôm nay thế nào?"
MUST_INCLUDE = ["ngoài phạm vi"]


class SmokeFailure(Exception):
    """One smoke step failed."""


def _fail(step: str, detail: str) -> None:
    print(f"::error::smoke/{step}: {detail}")
    raise SmokeFailure(f"{step}: {detail}")


def check_health(client: httpx.Client) -> None:
    t0 = time.perf_counter()
    r = client.get("/api/health")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code != 200:
        _fail("health", f"HTTP {r.status_code} (expected 200)")
    print(f"  ✓ /api/health        200  ({ms:.0f}ms)")


def check_ready(client: httpx.Client) -> None:
    t0 = time.perf_counter()
    r = client.get("/ready")
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code != 200:
        body = (r.text or "")[:200]
        _fail("ready", f"HTTP {r.status_code} (expected 200): {body}")
    payload: dict[str, Any] = {}
    try:
        payload = r.json()
    except Exception:
        pass
    if payload and payload.get("ready") is False:
        _fail("ready", f"ready=false checks={payload.get('checks')}")
    print(f"  ✓ /ready             200  ({ms:.0f}ms)")


def _sse_answer_text(raw: str) -> str:
    """Collect answer fragments from SSE `data:` lines."""
    parts: list[str] = []
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            parts.append(chunk)
            continue
        if isinstance(obj, dict):
            ans = obj.get("answer") or obj.get("output") or ""
            if ans:
                parts.append(str(ans))
        elif isinstance(obj, str):
            parts.append(obj)
    return "\n".join(parts)


def check_ask(
    client: httpx.Client,
    question: str,
    must_include: list[str],
    *,
    bearer_token: str | None = None,
) -> None:
    t0 = time.perf_counter()
    headers = {}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    r = client.post(
        "/api/agent/stream",
        json={
            "question": question,
            "session_id": "smoke-deploy",
            "user_id": "smoke",
            "stream_tokens": False,
        },
        headers=headers,
        timeout=120.0,
    )
    ms = (time.perf_counter() - t0) * 1000
    if r.status_code != 200:
        _fail("ask", f"HTTP {r.status_code}: {(r.text or '')[:200]}")

    answer = _sse_answer_text(r.text).strip()
    if not answer:
        _fail("ask", "empty answer from SSE stream")

    missing = [kw for kw in must_include if kw.lower() not in answer.lower()]
    if missing:
        _fail(
            "ask",
            f"answer missing {missing} — got: {answer[:200]!r}",
        )
    print(f"  ✓ /api/agent/stream  keywords {must_include}  ({ms:.0f}ms)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Smoke test after deploy")
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--timeout", type=float, default=15.0, help="timeout for health/ready")
    ap.add_argument(
        "--ask",
        action="store_true",
        help="also POST one golden out-of-scope question and check keywords",
    )
    ap.add_argument("--question", default=KNOWN_QUESTION)
    ap.add_argument(
        "--must-include",
        default=",".join(MUST_INCLUDE),
        help="required keywords, comma-separated",
    )
    ap.add_argument(
        "--token",
        default="",
        help="Bearer token when IAM_REQUIRED=true (or env SMOKE_BEARER_TOKEN)",
    )
    args = ap.parse_args()

    print(f"Smoke test: {args.url}")
    must_include = [k.strip() for k in args.must_include.split(",") if k.strip()]
    token = (args.token or __import__("os").environ.get("SMOKE_BEARER_TOKEN") or "").strip() or None

    try:
        with httpx.Client(base_url=args.url, timeout=args.timeout) as client:
            check_health(client)
            check_ready(client)
            if args.ask:
                check_ask(client, args.question, must_include, bearer_token=token)
    except SmokeFailure:
        print("\nSMOKE FAIL — do not promote this build.")
        sys.exit(1)
    except httpx.HTTPError as exc:
        print(f"::error::smoke/connect: cannot reach {args.url}: {exc}")
        print("\nSMOKE FAIL — do not promote this build.")
        sys.exit(1)

    print("\nSMOKE PASS.")


if __name__ == "__main__":
    main()
