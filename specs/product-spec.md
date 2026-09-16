# Product Spec

## App Name
agent_stat_v2 (agent_ATIN) — Chatbot thống kê xe ra/vào & xâm nhập khu vực

## Goal
Cho người vận hành khu công nghiệp hỏi bằng tiếng Việt tự nhiên và nhận câu
trả lời thống kê (số lượt xe ra/vào, phân loại theo loại xe/hãng xe, truy vết
biển số, khung giờ xâm nhập nhiều nhất) — dựa trên dữ liệu camera AI thật
(Postgres), không cần biết SQL.

> Ghi chú quy trình (không phải mục tiêu sản phẩm): bản này viết lại đơn
> giản nhất có thể của `atin/` (project trước, đã chạy được và verify với
> Postgres thật) — giữ đúng quyết định kiến trúc đã kiểm chứng ở đó, bỏ mọi
> phần chưa cần cho MVP.

## Target Users
- Người vận hành/quản lý khu công nghiệp — không biết SQL, cần số liệu nhanh.
- Chỉ phục vụ 1 tổ chức (organization) duy nhất trong bản MVP này.

## Core User Flow
1. User mở trang chat đơn giản (1 ô nhập câu hỏi + lịch sử hội thoại).
2. User gõ câu hỏi thống kê (vd. "Hôm nay có bao nhiêu lượt xe vào?").
3. App kiểm tra câu hỏi có hợp lệ không (không phải nội dung độc hại/lạc đề).
4. App chọn đúng truy vấn cần dùng, lấy số liệu từ database, trả lời bằng
   câu tiếng Việt tự nhiên kèm bảng số liệu thô.
5. User xem câu trả lời, có thể hỏi tiếp câu khác.

## Features In Scope

**Agent & tool** — 1 agent duy nhất (không multi-agent), trả lời bằng
function-calling trên bộ tool tham số hoá cố định — KHÔNG Text-to-SQL tự do
(an toàn + chính xác hơn với model nhỏ, xem `atin/README.md`). Tool đủ để
trả lời 5 câu hỏi mẫu trong tài liệu gốc:
- đếm lượt xe ra/vào theo thời gian, phân loại theo loại xe/hãng xe
- truy vết lịch sử di chuyển theo biển số
- khung giờ xâm nhập khu vực nhiều nhất
- liệt kê camera/khu vực hợp lệ (tránh agent đoán sai giá trị lọc)
- 1 tool SQL đọc-only dự phòng cho câu hỏi không khớp tool nào

**Guardrail** — input: chặn prompt injection/nội dung độc hại, và từ chối
lịch sự câu hỏi ngoài phạm vi thống kê (không gọi agent). Output: đối chiếu
số liệu trong câu trả lời với số liệu tool trả về (thuần code, không LLM),
giới hạn độ dài, redact PII cơ bản.

**Hạ tầng** — đọc-only Postgres qua role riêng (không phải user admin) trên
đúng 2 DB cần dùng (`its`, `virtual_fence`). Đổi LLM backend (OpenAI Cloud /
Ollama local) chỉ qua `.env`, không sửa code — vì mục tiêu cuối là chạy trên
máy 4GB VRAM.

**UI** — 1 trang web tĩnh đơn giản (HTML/JS thuần, không framework) làm UI
chat.

## Features Out of Scope (bản MVP này)
- Multi-agent / nhiều sub-agent chuyên biệt theo phòng ban.
- Visualization Agent (vẽ chart) — để Phase sau.
- HITL (human-in-the-loop), tracing/eval, connection pooling đa người dùng.
- Long-term memory, tool retrieval qua embedding, MCP server/client — chỉ
  cần thiết khi số tool/lượt hội thoại lớn hơn nhiều so với MVP này (xem
  `specs/implementation-plan.md` mục nguồn tham khảo).
- LLM-based injection check (chỉ dùng regex — nhanh, đủ cho MVP).
- Authentication, phân quyền theo user/phòng ban.
- Materialized views / mart riêng (mart thật hiện đang lỗi thời — xem
  `atin/README.md`) — luôn query trực tiếp bảng raw.
- Test UI tự động (chấp nhận test tay qua trình duyệt), load test nhiều
  người dùng đồng thời.
- Production cloud deployment (chỉ cần chạy local + demo qua ngrok).

## Acceptance Criteria
- Chạy được local bằng 1 lệnh (`uvicorn` hoặc tương đương).
- User thấy trạng thái rõ ràng trên UI: đang xử lý / trả lời thành công /
  lỗi (không im lặng, không crash trắng trang).
- Trả lời đúng, có số liệu thật, cho cả 5 câu hỏi mẫu trong tài liệu gốc
  ("Ý tưởng Agent.docx").
- Câu hỏi ngoài phạm vi (vd. hỏi thời tiết) → bị từ chối lịch sự, không gọi
  tool/DB.
- Câu hỏi chứa prompt injection rõ ràng → bị chặn, trả lỗi rõ ràng (không
  crash).
- Đổi `LLM_BACKEND=ollama` trong `.env` và không cần sửa code để chạy với
  model local.
- Có thể demo qua ngrok (expose 1 cổng duy nhất — FastAPI phục vụ cả API và
  static UI).
