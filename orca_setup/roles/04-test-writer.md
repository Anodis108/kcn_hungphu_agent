# Role 04 — Test writer

**SESSION TITLE (exact):** `05 Test writer (Cursor)`


| Field | Value |
|-------|-------|
| **Agent** | Preferred `cursor` — fallback **antigravity** nếu hết token |
| **Token** | Vừa (medium) |
| **Worktree** | `current` hoặc cùng child với Implementer (coordinator chọn) |
| **Parallel** | Song song Implementer khi độc lập |

## Input
- `specs/product-spec.md` (+ `specs/test-plan.md` nếu có)
- `specs/implementation-plan.md` (behaviors / acceptance)
- Không phụ thuộc code nửa vời của Implementer nếu có thể viết từ spec

## Output
- File test theo convention repo
- Map acceptance → test cases trong report ngắn
- Cập nhật `specs/change-log.md` nếu thêm/sửa test đáng kể

## Done when
- Tests phản ánh acceptance; chạy được (hoặc RED đúng lý do nếu code chưa có).
- Không rewrite thuật toán ngoài phạm vi test.

## Prompt skeleton

```text
You are Test writer (Cursor). Write tests from specs/product-spec.md
acceptance (and specs/test-plan.md if present). Prefer behavior tests.
Do not implement product features. Report which acceptance items each
test covers. Update specs/change-log.md if needed.
```

## Report back (bắt buộc)
Xem `_REPORT_BACK.md`. Không bỏ qua file inbox + worker_done.
