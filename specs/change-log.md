# Change Log

## 2026-09-16

### Added
- Tạo bộ spec ban đầu (`specs/product-spec.md`, `specs/implementation-plan.md`,
  `specs/test-plan.md`, `specs/change-log.md`) và `AGENTS.md` theo Spec-Driven
  Development. Chưa viết code cho luồng mới.
- Thêm mục "Tham khảo llm-engineer-demo/" vào `AGENTS.md` — bảng liệt kê kỹ
  thuật có trong Module II (`agent_m2/`) nhưng KHÔNG dùng ở MVP này (memory,
  tool retrieval, MCP, HITL, tracing/eval, multi-agent, LLM-based injection
  check) kèm lý do, để tránh drift scope khi code.

### Changed
- Review `specs/product-spec.md`: tách phần "ghi chú quy trình" khỏi Goal,
  nhóm lại Features In Scope theo 4 hạng mục (Agent & tool / Guardrail / Hạ
  tầng / UI) thay vì 1 list phẳng, thêm acceptance criterion về UI-state
  (loading/success/error) còn thiếu.
- Bổ sung `specs/implementation-plan.md` Phase 2/4/5 với file nguồn cụ thể
  trong `llm-engineer-demo/` nên tham khảo cho từng phần (llm/backends.py,
  llm/resilience.py, agent_m2/nodes.py, guardrails/injection.py, guardrails/pii.py).
- Viết lại `specs/implementation-plan.md` từ 9 phase rời rạc thành 6 phase
  chuẩn theo khung Spec-Driven Development (Project setup → Config & LLM
  client → Core backend/data logic → Agent → Validation and error states →
  Local run instructions). Gộp Guardrails + Testing cũ vào "Validation and
  error states"; gộp API/UI vào "Agent"; gộp local run + ngrok vào "Local
  run instructions". Không cắt tính năng nào, chỉ tổ chức lại checklist.
- Bổ sung `specs/product-spec.md` Out of Scope: liệt kê tường minh
  long-term memory/tool retrieval/MCP, LLM-based injection check, test UI
  tự động/load test — trước đây chỉ nhắc trong AGENTS.md/test-plan.md, giờ
  cũng có trong product-spec để nhất quán.

### Fixed
- (chưa có)

### Changed (tiếp)
- Viết lại `AGENTS.md` cho ngắn gọn, bám sát mẫu chuẩn trong "Spec Driven
  Development Guide" (7 quy tắc + Coding Style + Testing, bỏ phần "Ràng
  buộc riêng" và bảng "kỹ thuật không dùng" đã làm file phình to). Nội dung
  đó thuộc về `specs/product-spec.md` (scope) và
  `specs/implementation-plan.md` (chi tiết kỹ thuật từng phase), không phải
  `AGENTS.md` (chỉ nói cách hành xử khi code) — đã có sẵn ở 2 file kia nên
  không mất thông tin, chỉ sửa 1 link tham chiếu hỏng trong product-spec.md
  (trỏ sang implementation-plan.md thay vì AGENTS.md).

### Notes
- Bản spec này viết lại đơn giản hơn `atin/` (project trước, đã chạy được
  và verify với Postgres thật) — xem `atin/README.md` để biết các quyết
  định kiến trúc đã kiểm chứng (function-calling thay Text-to-SQL, tối đa
  2 lời gọi LLM/câu hỏi, mart `plate_dashboard` không dùng vì lỗi thời).
- Code cũ hiện có trong `agent_ATIN/src/` (viết dở, dựa theo Module II phức
  tạp hơn của `llm-engineer-demo`) được GIỮ LẠI theo yêu cầu, chưa xoá —
  quyết định xoá/tái cấu trúc sẽ làm ở Phase 1 implementation-plan khi thực
  sự bắt đầu code.
