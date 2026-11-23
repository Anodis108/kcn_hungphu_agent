# Role 03 — Implementer

**SESSION TITLE (exact):** `04 Implementer (Antigravity)`


| Field | Value |
|-------|-------|
| **Agent** | `antigravity` |
| **Token** | Nặng nhất (heaviest) |
| **Worktree** | `new-child` (worktree riêng) |
| **Parallel** | Có thể song song với Test writer |

## Input
- `specs/product-spec.md`, `specs/implementation-plan.md` (alias `SPEC.md`/`PLAN.md` nếu còn)
- `REPO_DIGEST.md` (tham chiếu)
- `AGENTS.md` nếu có

## Output
- Code + commits theo **một** unchecked task/phase trong `implementation-plan.md`
- Tick checklist + cập nhật `specs/change-log.md` + lệnh test
- Test/lint xanh theo tiêu chí trong plan

## Done when
- Đúng một task/phase được hoàn thành và tick
- `pytest` / lệnh test của repo pass (ghi command + output tóm tắt)
- Không mở rộng scope / đổi kiến trúc trừ khi spec đã sửa trước

## Prompt skeleton

```text
You are Implementer (Antigravity) on an isolated worktree.
Read AGENTS.md and specs/. Implement ONLY the next unchecked task in
specs/implementation-plan.md. After: tick the checklist, update
specs/change-log.md, and report how to test. Do not expand scope.
```

## Report back (bắt buộc)
Xem `_REPORT_BACK.md`. Không bỏ qua file inbox + worker_done.
