# Product Spec

## App Name
agent_stat_v2 (agent_ATIN) — Trợ lý hỏi-đáp thống kê toàn bộ sự kiện VMS

## Goal
Cho người vận hành khu công nghiệp hỏi bằng tiếng Việt tự nhiên và nhận câu
trả lời thống kê dựa trên dữ liệu camera AI thật (Postgres), không cần biết
SQL — bao quát cả 8 loại sự kiện hiện có trên web VMS:

1. Nhận diện khuôn mặt
2. Giám sát phương tiện (đã có ở v1)
3. Giám sát vùng cấm / hàng rào ảo (đã có ở v1)
4. Phát hiện ẩu đả
5. Phát hiện đám đông
6. Phát hiện leo trèo
7. Phát hiện cháy khói
8. Giám sát mực nước

Nguồn dữ liệu chính xác cho từng sự kiện (bảng Postgres, cột, giả định cần
xác nhận) nằm ở `specs/implementation-plan.md` mục Phase 2 — spec này chỉ
nêu MỤC TIÊU sản phẩm, không lặp lại chi tiết kỹ thuật.

Ngoài tính năng hỏi-đáp, bản v2 còn thêm 2 phần hạ tầng vận hành (người
dùng cuối không thấy trực tiếp): **observability** (Langfuse tracing,
self-host) và **Prompt Registry** (quản lý prompt như code).

> Ghi chú quy trình: v1 (xe ra/vào + vùng cấm) là bản viết lại đơn giản
> nhất của `atin/` (đã chạy được, verify với Postgres thật). v2 (spec này)
> MỞ RỘNG phạm vi sự kiện + thêm observability/prompt registry, nhưng GIỮ
> NGUYÊN các quyết định kiến trúc đã kiểm chứng ở v1 (1 FastAPI service,
> function-calling cố định — không Text-to-SQL tự do, tối đa 2 LLM call/
> câu hỏi, đọc-only DB qua role riêng, đổi LLM backend chỉ qua `.env`).

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
(an toàn + chính xác hơn với model nhỏ). Tool phủ đủ 8 domain sự kiện ở
mục Goal (2 domain đầu — phương tiện, vùng cấm — đã có ở v1; 5 domain còn
lại là Phase 2-3-5, xem implementation-plan.md), cộng 1 tool SQL đọc-only dự
phòng cho câu hỏi không khớp tool nào, và 1 tool liệt kê camera/khu vực
hợp lệ (tránh agent đoán sai giá trị lọc).

**Guardrail** — input: chặn prompt injection/nội dung độc hại, và từ chối
lịch sự câu hỏi ngoài phạm vi thống kê (không gọi agent). Output: đối chiếu
số liệu trong câu trả lời với số liệu tool trả về (thuần code, không LLM),
giới hạn độ dài, redact PII cơ bản.

**Hạ tầng** — đọc-only Postgres qua role riêng (không phải user admin) trên
mọi DB nguồn cần dùng. Đổi LLM backend (OpenAI Cloud / Ollama local) chỉ
qua `.env`, không sửa code — vì mục tiêu cuối là chạy trên máy 4GB VRAM.

**UI** — 1 trang web tĩnh đơn giản (HTML/JS thuần, không framework) làm UI
chat.

**Golden dataset** — bộ 30 câu hỏi mẫu (`eval/datasets/agent_stat`) phủ đủ
8 domain sự kiện, dùng làm thước đo mỗi khi sửa agent/prompt. Chi tiết
phân bổ case theo domain: xem implementation-plan.md Phase 2.

**Observability** — Langfuse tự host trên máy này, trace mỗi lượt `/ask`
(input/output/latency/lỗi). Mặc định TẮT (`MONITORING_ENABLED=false`) —
không ai bắt buộc phải chạy Langfuse để dùng phần còn lại của app.

**Prompt Registry** — prompt sống trong file YAML riêng (`prompts/`),
không hardcode trong code. Đổi version production = sửa 1 file, không cần
sửa code; rollback = revert lại file đó. Git-based (không dùng dịch vụ
hosted ngoài).

## Features Out of Scope (bản MVP này)
- Multi-agent / nhiều sub-agent chuyên biệt theo phòng ban.
- Visualization Agent (vẽ chart) — để phase sau.
- HITL (human-in-the-loop), connection pooling đa người dùng.
- Long-term memory, tool retrieval qua embedding, MCP server/client.
- LLM-based injection check (chỉ dùng regex — nhanh, đủ cho MVP).
- Authentication, phân quyền theo user/phòng ban.
- Materialized views / mart riêng — luôn query trực tiếp bảng raw.
- Test UI tự động (chấp nhận test tay qua trình duyệt), load test nhiều
  người dùng đồng thời.
- Production cloud deployment (chỉ cần chạy local + demo qua ngrok).
- Phân tích ảnh/video bằng LLM — agent chỉ đọc số liệu đã được AI pipeline
  khác trích xuất sẵn vào Postgres, không tự chấm điểm ảnh/video.
- Cảnh báo real-time / push notification — agent trả lời khi được hỏi,
  không tự động đẩy tin khi có sự kiện mới.
- Langfuse Cloud, Prompt Registry hosted (LangSmith/PromptLayer) — chọn
  nhánh tự-host/git-based rẻ nhất, đúng tinh thần MVP.
- A/B testing prompt tự động trên traffic thật — Prompt Registry (chưa có
  phase kế hoạch cụ thể, xem ghi chú cuối `implementation-plan.md`) chỉ
  làm registry + versioning, chưa làm traffic splitting.

## Acceptance Criteria
- Chạy được local bằng 1 lệnh (`uvicorn` hoặc tương đương).
- User thấy trạng thái rõ ràng trên UI: đang xử lý / trả lời thành công /
  lỗi (không im lặng, không crash trắng trang).
- Trả lời đúng, có số liệu thật, cho ít nhất 1 câu hỏi mẫu mỗi domain
  (8 domain ở mục Goal).
- Câu hỏi ngoài phạm vi (vd. hỏi thời tiết) → bị từ chối lịch sự, không gọi
  tool/DB.
- Câu hỏi chứa prompt injection rõ ràng → bị chặn, trả lỗi rõ ràng (không
  crash).
- Đổi `LLM_BACKEND=ollama` trong `.env` và không cần sửa code để chạy với
  model local.
- Có thể demo qua ngrok (expose 1 cổng duy nhất — FastAPI phục vụ cả API và
  static UI).
- `eval/datasets/agent_stat` có đủ 30 case phủ 8 domain, chạy được bằng
  `eval/run.py`, in được tỷ lệ pass/fail theo slice.
- Langfuse chạy self-host trên máy này, xem được trace của 1 lượt `/ask`
  thật (input/output/latency, không lộ secrets). Tắt monitoring thì app
  chạy y hệt v1, `pytest` offline không bị ảnh hưởng.
- Đổi file production của 1 prompt (không sửa code) làm hành vi agent đổi
  theo, revert lại file thì hành vi quay về như cũ.
