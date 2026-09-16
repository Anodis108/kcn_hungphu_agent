# agent_ATIN

Chatbot thống kê xe ra/vào & xâm nhập khu vực — bản viết lại đơn giản nhất
có thể của `atin/` (project trước, đã chạy được và verify với Postgres
thật), dùng **spec-driven development**.

## Trạng thái hiện tại

Đang ở giai đoạn spec — **chưa code cho luồng mới**. Xem:

- [`specs/product-spec.md`](specs/product-spec.md) — mục tiêu, phạm vi, acceptance criteria
- [`specs/implementation-plan.md`](specs/implementation-plan.md) — checklist từng phase
- [`specs/test-plan.md`](specs/test-plan.md) — cách test
- [`specs/change-log.md`](specs/change-log.md) — lịch sử thay đổi
- [`AGENTS.md`](AGENTS.md) — quy tắc cho coding agent khi triển khai

Code cũ trong `src/`/`main.py` (viết dở, dựa theo Module II của
`llm-engineer-demo`) hiện được giữ nguyên, chưa xoá — sẽ xử lý ở Phase 1
implementation-plan.

## Cài đặt & chạy local

_(Sẽ cập nhật khi Phase 1 implementation-plan hoàn thành.)_

## Demo với ngrok

_(Sẽ cập nhật ở Phase 9 implementation-plan.)_
