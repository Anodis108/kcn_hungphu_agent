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
- Nếu task gắn G0–G17: cập nhật hàng tương ứng trong `specs/gap-analysis-quy-trinh-product-agent.md` (§0 Protocol) — hoặc ghi rõ sẽ cập nhật sau Reviewer `Approved`
- Test/lint xanh theo tiêu chí trong plan
- `next_hint` trong report: **chờ Reviewer-5a** (không tự đề xuất task kế)

## Done when
- Đúng một task/phase được hoàn thành và tick
- `pytest` / lệnh test của repo pass (ghi command + output tóm tắt)
- Không mở rộng scope / đổi kiến trúc trừ khi spec đã sửa trước
- **Không** bắt đầu unchecked task tiếp theo trong cùng lượt — cổng §6c (SDD loop)

## Khi Reviewer `Blocked`
- Chỉ **fix** lỗi của task hiện tại; cập nhật `change-log`; báo lại để review. Không mở task mới.

## Prompt skeleton

```text
You are Implementer (Antigravity) on an isolated worktree.
Read AGENTS.md and specs/. Implement ONLY the one unchecked task named
in the brief (or the first unchecked if none named). Before coding:
summarize what/files/how-test. After: tick checklist, update
specs/change-log.md, and if the task maps to G0–G17 update
specs/gap-analysis-quy-trinh-product-agent.md (or note pending until
Approved). STOP — do not start the next task; next_hint must be
Reviewer-5a. If Fix-only: fix only listed issues for the same task.
```

## Report back (bắt buộc)
Xem `_REPORT_BACK.md` + `_VERIFY.md`. Không bỏ qua file inbox + worker_done.
