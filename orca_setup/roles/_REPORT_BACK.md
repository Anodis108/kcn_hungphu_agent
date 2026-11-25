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

**Implementer / Test writer (khi đụng code/test):** prepend **một mục** vào `specs/task-delta.md` (newest first): **Task** = id + 1–2 câu **làm gì / mục đích gì** (cấm chỉ ghi `21.4`) · đổi gì (kỹ thuật ngắn) · chỗ sửa dạng link `#L…` `[\`path:42\`](../path#L42)` — **click phải nhảy đúng dòng đã sửa** (cấm lazy `#L1` cho file đã edit / file dài; file mới + đổi từ L1 thì được nếu ghi chú; file xóa → “(deleted)”) · **không** dán before/after · lệnh test · link report. Đồng bộ `orca_setup/` nếu đổi quy ước. Thiếu mô tả / thiếu `#L` / `#L` lệch = **chưa xong**.

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
3. **Dispatch ngay** bước tiếp — đúng role (§15b), cổng SDD (§6c), vòng đến hết mission (§15f), lane song song nếu đủ điều kiện (§15g). Không bỏ lửng; không tự làm việc của Planner/Implementer/…
4. Cập nhật `specs/session-handoff.md`; `task-update --status completed|failed` khi đã settle.
5. Wake trùng (cùng msg/report đã xử lý) → không dispatch lại; nêu worker đang chạy.
6. **Đúng agent quy ước:** task nào role canonical làm được → **bắt buộc** dispatch đúng agent trong `SESSION-TITLES` / roles (`Implementer`→**Antigravity/agy**, `Reviewer-5a`→Cursor trên pane `06a`/`06b`, `Planner`/`5b`→Claude, …). Không thay bằng agent “thông minh hơn” nếu role quy ước còn khả dụng. Ngoại lệ chỉ khi user **nói rõ** hoặc agent quy ước không launch được (ghi lý do trong handoff).
7. **Reuse pane role — cấm Coord “tự mở Cursor mới” thay role:** khi tab canonical còn sống (`04a`/`04b` AGY, `06a`/`06b` Cursor Reviewer, …) → `worker-start --terminal term_<pane đó>` (hoặc tương đương), **không** tạo worker Cursor one-shot mới khiến giống Spec/Coord tự làm. Brief để trong `specs/agent-reports/_briefs/` (hoặc ngoài inbox) — **không** để `_brief-*.md` cạnh report thật gây file-inbox wake nhiễu.
8. **Đóng worker sau settle:** nếu Dispatch dùng agent **ngoài role quy ước** hoặc pane one-shot không thuộc canonical `01`…`06b`, sau `worker_done` + đã đọc report → `orca orchestration worker-release --dispatch <dispatchId>` (không chờ hết `autoReleaseAt`). Pane canonical: giữ tab theo SESSION-TITLES.

**Worker `next_hint`:** gợi ý role/task kế (vd. `Reviewer-5a` sau Implement; `Implementer 19.2` sau Planner). Coordinator vẫn phải khớp §15b/§6c.
