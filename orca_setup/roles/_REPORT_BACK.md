# Báo cáo bắt buộc về Coordinator (mọi role)

Áp dụng **mọi** agent (Explorer, Planner, Implementer, Test writer, Reviewer-5a/5b).

Task **chưa xong** nếu chỉ in kết quả trong pane mà **không** làm đủ 2 bước dưới.

## 1) Ghi file inbox (bền, luôn có)

```bash
mkdir -p specs/agent-reports
REPORT="specs/agent-reports/$(date +%Y%m%d-%H%M%S)-<role>.md"
```

Nội dung tối thiểu:

```markdown
# Report — <role>
- dispatch: <dispatchId nếu có>
- task: <taskId nếu có>
- outcome: succeeded | failed
- summary: <3–10 bullet>
- artifacts: <paths thật trên đĩa>
- next_hint: <gợi ý role/việc tiếp theo cho Coordinator>
```

Cập nhật thêm dòng trong `specs/session-handoff.md` mục **Hoàn thành gần nhất**.

## 2) `worker_done` (đánh thức Coordinator)

Khi được launch bằng `orchestration worker-start` (có Task/Dispatch ID trong preamble):

```bash
orca orchestration send --type worker_done --outcome succeeded \
  --subject "<role> done" \
  --body "$(cat "$REPORT")" \
  --task-id <taskId> --dispatch-id <dispatchId>
```

Thất bại → `--outcome failed` + lý do trong body.

Nếu **không** có Task/Dispatch (chỉ `agent launch` / chat thủ công): vẫn **bắt buộc** bước 1 (file inbox); thêm một dòng rõ `READY for coordinator` ở cuối pane.

## 3) Coordinator — nhận tín hiệu & phản hồi (bắt buộc)

**Trước / ngay sau `worker-start`:** bật auto-wake (Cursor pane không tự wake):

```bash
orca-coord-watch --run <runId> --terminal term_<coordinator> --workdir <project>
```

**Khi nhận `[ORCA auto-wake]` hoặc thấy report mới:**

1. `orca-coord-drain --run <runId> --workdir <project>` (hoặc đọc inbox + `specs/agent-reports/` mới nhất).
2. Tóm tắt cho user (không chờ user nhắc / paste ảnh).
3. Chọn hướng đi tiếp / dispatch role kế (§15b, cổng SDD §6c) — không bỏ lửng.
4. Cập nhật `specs/session-handoff.md`; `task-update --status completed|failed` khi đã settle.
