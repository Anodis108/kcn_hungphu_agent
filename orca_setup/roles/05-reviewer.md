# Role 05 — Reviewer (2 vòng)

**SESSION TITLE (exact):** `06 Reviewer-5a (Cursor) / 07 Reviewer-5b (Claude)`


Tuân `ORCA-AGENT-SETUP.md` §18 và `_VERIFY.md`.

## 5a — Cursor (round 1)

| Field | Value |
|-------|-------|
| **Agent** | Preferred `cursor` — fallback **antigravity** nếu hết token |
| **Token** | Vừa |
| **Focus** | Requirements, edge cases, missing tests vs `specs/product-spec.md` |

### Cách làm
1. Xác nhận tool đã chạy (đọc report Implementer/`pytest`); nếu chưa có bằng chứng tool → **Blocked** hoặc tự chạy rồi mới review.
2. Review **đối kháng**: tìm lỗi correctness / acceptance; không khen chung.
3. Mỗi finding = bằng chứng (test, lệnh, path/code). Không rewrite lớn.

### Done when
- Report: Critical / Important / Minor + `Approved` hoặc `Blocked`
- File inbox + `worker_done` (`_REPORT_BACK.md`)

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
