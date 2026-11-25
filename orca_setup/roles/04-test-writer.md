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
- Prepend `specs/task-delta.md` nếu tạo/sửa file test (**Task** nói rõ test này cover gì + links **chỉ** file test + `#L…`)

## Done when
- Tests phản ánh acceptance của **task đang làm**; chạy được (hoặc RED đúng lý do nếu code chưa có).
- Không rewrite thuật toán ngoài phạm vi test.
- Không nhảy sang acceptance của task kế khi task hiện tại chưa `Approved` (§6c).

## Prompt skeleton

```text
You are Test writer (Cursor). Write tests for the current task's
acceptance in specs/product-spec.md (and specs/test-plan.md).
Prefer behavior tests. Do not implement product features.
Report which acceptance items each test covers. Update
specs/change-log.md and prepend specs/task-delta.md (test paths + #L line links)
if needed. next_hint: wait for Reviewer-5a
(or Fix-only if already in a review loop).
```

## Report back (bắt buộc)
Xem `_REPORT_BACK.md` + `_VERIFY.md`. Không bỏ qua file inbox + worker_done.
