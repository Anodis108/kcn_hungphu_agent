# Role 05 — Reviewer (2 vòng)

**SESSION TITLE (exact):** `06 Reviewer-5a (Cursor) / 07 Reviewer-5b (Claude)`


Tuân `ORCA-AGENT-SETUP.md` §18 và `_VERIFY.md`.

## 5a — Cursor (round 1)

| Field | Value |
|-------|-------|
| **Agent** | Preferred **`cursor`** — fallback `antigravity` nếu hết token |
| **Token** | Vừa |
| **Focus** | Requirements, edge cases, missing tests vs `specs/product-spec.md` |
| **Skills** | `using-superpowers` + `verification-before-completion`; AG overflow: `ponytail-review` |

### Pre-gather (Antigravity) — tiết kiệm token 5a

Chi tiết: [`_PRE_GATHER.md`](_PRE_GATHER.md).

- **Phase lớn / log·diff·ảnh nặng:** Coord dispatch **AG pre-gather trước** (diff lọc, smoke/test sanitized, checklist máy) → artifact `*-pre-gather.md` → **5a Cursor** chỉ đọc digest + phán `Approved`|`Blocked`.
- **Fix-only nhỏ (2–5 file):** bỏ qua AG — 5a tự chạy tool.
- AG **không** thay cổng review; 5a được tin evidence AG nhưng **re-run** nếu nghi / Critical.

### Cách làm (guide VN bước 7 — cổng §6c)
1. Nếu có `*-pre-gather.md` mới: đọc digest trước. Xác nhận tool/evidence (Implementer report / pytest / digest); thiếu bằng chứng → **Blocked** hoặc tự chạy rồi mới review.
2. So feature vừa làm với `specs/product-spec.md` + `specs/test-plan.md`: **what passes / what fails / what is missing**.
3. Kiểm tra mục mới nhất `specs/task-delta.md`: **Task** đọc được mục đích (không chỉ số phase) · khớp artifacts · mỗi chỗ sửa có link `#L…` **và click nhảy đúng dòng đã đổi** (không chấp nhận toàn bộ link chỉ `#L1` trên file đã edit / file dài trừ khi thay đổi thật sự bắt đầu ở L1 và ghi chú). Thiếu mô tả / thiếu `#L` / `#L` lệch / lẫn file task khác → **Blocked** (hoặc Important nếu nhẹ). File deleted được ghi “(deleted)” là đủ.
4. Review **đối kháng**: chỉ lỗi correctness / acceptance; không khen chung.
5. Mỗi finding = bằng chứng (test, lệnh, path/code). Không rewrite lớn.
6. `next_hint`: nếu `Blocked` → Implementer/Test **Fix-only cùng task**; nếu `Approved` → Coordinator mới được dispatch task `[ ]` kế (hoặc 5b nếu cần).
7. Nếu `Approved` và task gắn G\*: kiểm tra / bổ sung cập nhật `specs/gap-analysis-quy-trinh-product-agent.md` (hàng G\* + §5 lịch sử). Thiếu cập nhật → ghi Important hoặc tự sửa tracker trước khi Approved.

### Done when
- Report: pass/fail/missing + Critical / Important / Minor + `Approved` hoặc `Blocked`
- File inbox + `worker_done` (`_REPORT_BACK.md`)
- Gap tracker đã khớp trạng thái G\* khi Approved (hoặc N/A nếu task không map G)
- **Không** bảo “sang task kế” khi còn `Blocked`

## 5b — Claude (round 2)

| Field | Value |
|-------|-------|
| **Agent** | Preferred `claude` — fallback **cursor → antigravity** |
| **Token** | Nhẹ |
| **Focus** | Filtered diff + logic nhạy cảm thôi |

### Claude lifecycle
- **Trước launch:** `claude-session start`
- **Sau worker_done:** `claude-session stop`

### Cách làm
- Chỉ filtered diff + acceptance. Đối kháng + bằng chứng như 5a.
- Không drive-by refactor. Không thay lint/test bằng “đọc diff”.

### Prompt skeleton (5b)

```text
You are Reviewer 5b (Claude). Adversarial review of filtered diff vs product-spec.
Only correctness-critical issues. Cite evidence (hunks / commands).
Do not replace pytest/linters. Return Critical/Important/Minor and Approved|Blocked.
Then write specs/agent-reports/… and worker_done (_REPORT_BACK.md + _VERIFY.md).
```

## Report back (bắt buộc)
`_REPORT_BACK.md` + `_VERIFY.md`.
