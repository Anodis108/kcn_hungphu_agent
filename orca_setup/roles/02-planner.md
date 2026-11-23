# Role 02 — Planner

**SESSION TITLE (exact):** `03 Planner (Claude)`


| Field | Value |
|-------|-------|
| **Agent** | Preferred `claude` — fallback **cursor → antigravity** nếu hết token |
| **Token** | Nhẹ (light) |
| **Worktree** | `current` |
| **Mode** | Plan mode — không implement code |

## Input
- `REPO_DIGEST.md`
- Vài file then chốt (paths do user / coordinator chỉ trong brief)
- Yêu cầu tính năng / bug của user
- Guide: `Spec Driven Development Guide - Vietnamese.md` (nếu có trên máy)

## Output (bắt buộc) — layout guide VN
- `specs/product-spec.md` — goal, users, in/out scope, acceptance
- `specs/implementation-plan.md` — phase nhỏ + checklist
- `specs/test-plan.md` khi cần
- `specs/change-log.md` (khởi tạo / stub nếu chưa có)
- Alias cũ `SPEC.md`/`PLAN.md` chỉ dùng nếu repo chưa chuyển sang `specs/`

## Done when
- Spec/plan rõ, MVP-focused, checklist kiểm chứng được.
- Không chỉnh sửa code production.

## Claude lifecycle
- **Trước launch:** `claude-session start`
- **Sau worker_done:** `claude-session stop` (logout managed Claude)

## Prompt skeleton

```text
You are Planner (Claude, plan mode only). Read REPO_DIGEST.md, the brief,
and Spec Driven Development Guide - Vietnamese.md if present.
Write/update specs/product-spec.md and specs/implementation-plan.md
(+ test-plan.md if needed). Keep MVP-focused. Do not write production code.
```

## Report back (bắt buộc)
Xem `_REPORT_BACK.md`. Không bỏ qua file inbox + worker_done.
