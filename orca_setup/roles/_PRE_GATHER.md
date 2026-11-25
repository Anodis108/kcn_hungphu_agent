# Pre-gather (Antigravity) — trước Reviewer-5a

**Mục tiêu:** nén evidence thô → artifact ngắn để **Cursor 5a** review đỡ tốn token.  
**Cấm:** AG **không** đưa `Approved`/`Blocked`, không phán logic/security thay Reviewer.

## Khi nào Coord bật (bắt buộc cân nhắc)

| Quy mô | Pre-gather AG? |
|--------|----------------|
| Fix-only / diff ~2–5 file nhỏ, không log dài | **Không** — 5a Cursor làm thẳng (tránh chậm hop) |
| Phase lớn / nhiều file mới / workflow CI-CD / docker+smoke / log dài / ảnh·vision | **Có** — AG trước → rồi 5a |

## Ba việc chân tay (chỉ factual)

1. **Diff / files đã lọc**  
   - `git diff` / hunk đúng `touches` của task (hoặc theo `specs/task-delta.md` mới nhất).  
   - Không dump cả file trăm dòng nếu chỉ đổi vài hàm — trích hunk + path.

2. **Test / smoke — sanitized log**  
   - Chạy lệnh acceptance của plan (pytest / `deploy/smoke.py` / yaml check…).  
   - Artifact chỉ giữ: exit code, PASS/FAIL 1 dòng, **stack/failure** nếu fail (không nguyên docker pull / pip noise).

3. **Checklist máy (regex / static)**  
   - Ví dụ: còn `dong-app`? YAML parse? thiếu mục `task-delta`?  
   - Ghi `[PASS]` / `[FAIL]` / `[EVIDENCE] …` — **không** viết verdict review.

## Output artifact (bắt buộc)

```bash
mkdir -p specs/agent-reports
DIGEST="specs/agent-reports/$(date +%Y%m%d-%H%M%S)-pre-gather.md"
```

Nội dung tối thiểu:

```markdown
# Pre-gather — <phase/task>
- dispatch / task ids
- scope: paths from task-delta / plan
- filtered_diff: <tóm tắt hoặc path artifact phụ>
- commands_run: <cmd> → exit N ; PASS|FAIL (+ 5–30 dòng failure nếu có)
- mechanical_checks:
  - [PASS|FAIL] …
- next_hint: Reviewer-5a Cursor — review digest này (không re-dump raw log trừ khi nghi ngờ)
```

`worker_done` + `_REPORT_BACK.md`. `next_hint` **luôn** = Reviewer-5a (Cursor).

## Reviewer-5a dùng digest thế nào

- Đọc digest + `task-delta` + product-spec/test-plan.  
- **Được** tin commands_run nếu exit + snippet rõ; **phải** re-run nếu nghi ngờ / thiếu evidence / Finding Critical.  
- Verdict chỉ từ 5a (hoặc 5b) — không copy phán của AG.
