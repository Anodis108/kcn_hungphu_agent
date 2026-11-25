# Design — v23: Langfuse manual (13.5) + tối giản tests + dọn test-only src

**Status:** grill + brainstorming **Approved** 2026-11-25  
**Plan owner:** 03 Planner (2026-11-25) — phases chi tiết/touches khóa tại `implementation-plan.md` § v23 (23.1–23.5); bảng Phases dưới đây chỉ là tóm tắt.  
**Skills:** grill-me · brainstorming · codebase-design

## Goal

1. Đóng Phase **13.5** — manual doc kiểm tra nested Langfuse (AC-9).
2. Gom `tests/` theo **capability** (~25–30), giảm file rời (hiện 49).
3. Tách **seam** cache/production khỏi re-export “for tests” trên `src/main.py`; helpers test vào **module sâu** `tests/support/`.

## Non-goals

- Không đổi graph / SSE / kiến trúc agent.
- Không xóa heuristic offline `plan.py` (prod fallback).
- Không gộp hết test trong một phase / một PR khổng lồ.
- Không bỏ `integration_db` / `live`.

## Decisions (locked)

| # | Decision |
|---|----------|
| Scope | 13.5 → support+src seam → gom test (tuần tự) |
| 13.5 artifact | `resource/docs/ops/langfuse-nested-trace-manual.md` (checklist ngắn; link AC-9 / AC-T1–T3) |
| Granularity | 1 product capability ≈ 1 file stem; ~25–30 caps |
| Folders | Giữ `hermetic/` · `integration_db/` · `live/`; tối đa 2 file/cap (`test_<cap>.py` + `test_<cap>_db.py`) |
| Src cleanup | Move production cache API off test-shaped `main` re-exports; tests import modules trực tiếp; `clear_*` test → support hoặc API rõ tên |
| Helpers | `tests/support/` deep package; bỏ shim trùng |
| Agents | Implement **Antigravity** (reuse `04a`/`04b`); Review **06a** Cursor |

## Architecture (depth)

- **Capability test file** = shallow surface (nhiều cases, một concern).
- **`tests/support/`** = deep module: app client, cache reset, SSE parse — callers chỉ học vài entry points.
- **Cache** = production module (`ttl_cache` / `cache_helpers`); `main` không phải test seam giả.

## Capability inventory (target stems)

Ready/SSE · Guardrails · Loop · Models fallback · Circuit breaker · Sandbox/audit · Eval gate · Eval batch · Feedback→golden · UI navigate · Trace sampling · Trace payload · LLM gateway/params · IAM/RBAC · Agent turn SSE · Hierarchy/subgraphs · Inline/rewrite · MinIO charts · **Memory** · **API gateway** · Graph/orchestrator · SQL · Knowledge RAG · Chart viz · Observability/errors · Compaction · Graceful degradation · Feedback API · Camera · LLM prompts

(Memory/API được gom mạnh từ nhiều file phase cũ.)

## Phases

| Task | Deliverable |
|:--:|---|
| **23.1** | 13.5 manual doc + tick plan 13.5 + change-log + task-delta |
| **23.2** | `tests/support/` + src cache/`main` seam; CI hermetic vẫn xanh |
| **23.3** | Gom Memory |
| **23.4** | Gom API/serving DB (∥ 23.5) |
| **23.5** | Đổi tên/gộp hermetic theo capability (∥ 23.4) |

## Verification

- 23.1: file doc tồn tại; checklist đủ bước Manual §1.1 test-plan.
- 23.2: `pytest tests/hermetic -q` exit 0; không `from src.main import _cache` trong tests.
- 23.3+: số file `test_*.py` giảm rõ; CI unchanged path; DB suites còn trong `integration_db`.

## Spec self-review

- Không TBD về chỗ đặt doc / folder / agent.
- Không mâu thuẫn v22 (giữ 3 folder + CI hermetic).
- Scope 23.3+ cố ý mở “Memory trước” — chi tiết map file ghi trong plan task khi dispatch từng slice.
