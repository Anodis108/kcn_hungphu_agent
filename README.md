# agent_ATIN

Chatbot thống kê xe ra/vào & xâm nhập khu vực — bản viết lại đơn giản nhất
có thể của `atin/` (project trước, đã chạy được và verify với Postgres
thật), dùng **spec-driven development**. Xem:

- [`specs/product-spec.md`](specs/product-spec.md) — mục tiêu, phạm vi, acceptance criteria
- [`specs/implementation-plan.md`](specs/implementation-plan.md) — checklist từng phase
- [`specs/test-plan.md`](specs/test-plan.md) — cách test
- [`specs/change-log.md`](specs/change-log.md) — lịch sử thay đổi
- [`AGENTS.md`](AGENTS.md) — quy tắc cho coding agent khi triển khai
- [`agent-canvas.md`](agent-canvas.md) — tổng hợp & phân tích Agent Canvas (harness VMS, model deploy, bên thứ 3)

## Lộ trình mở rộng (v2 — CHƯA triển khai)

Mọi mục `[ ]` trong [`specs/implementation-plan.md`](specs/implementation-plan.md)
**chỉ mới ở specs, chưa có code** (xem `specs/change-log.md` mục
2026-09-17). Phần "Kiến trúc"/"Cài đặt & chạy local" bên dưới mô tả đúng
những gì ĐANG CHẠY THẬT (mục `v1 — đã xong` trong từng phase).

- **Phase 2** — mở rộng agent trả lời đủ 8 loại sự kiện VMS (nhận diện
  khuôn mặt, phương tiện, vùng cấm, ẩu đả, đám đông, leo trèo, cháy khói,
  mực nước) thay vì chỉ xe/vùng cấm như hiện tại + golden dataset 30 case
  phủ đủ 8 domain + eval runner.
- **Phase 3, 5, 6** — hiện thực hoá domain mới (DB queries, tool, guardrail,
  test) dựa trên Phase 2.
- **Phase 4** — Langfuse tracing, self-host trên chính máy này.
- **Phase 8** — demo Langfuse + demo golden dataset.
- **Prompt Registry** (git-based, versioning + rollback qua file) chưa có
  phase kế hoạch cụ thể — xem ghi chú cuối `implementation-plan.md`.

Mục tiêu sản phẩm: [`specs/product-spec.md`](specs/product-spec.md). Bảng
ánh xạ sự kiện → DB, giả định cần xác nhận, thiết kế tool/test:
[`specs/implementation-plan.md`](specs/implementation-plan.md#phase-2-mở-rộng-5-domain-sự-kiện-vms-mới).

## Kiến trúc

1 FastAPI service duy nhất phục vụ cả API và static UI (không tách
frontend/backend):

```
POST /ask → guardrail_input → agent (LangGraph ReAct) → guardrail_output → answer
```

`agent` (`src/agent/graph.py`):

```
seed → agent (LLM #1: chọn tool + tham số) ⇄ tools → pack → answer (LLM #2, tuỳ chọn)
```

Tối đa **2 lời gọi LLM/câu hỏi**: LLM #1 chọn tool có sẵn + điền tham số
(function-calling, KHÔNG Text-to-SQL tự do — an toàn + chính xác hơn với
model nhỏ), LLM #2 (`src/agent/answer.py`) diễn giải số liệu thành câu
tiếng Việt, có thể tắt qua `ANSWER_USE_LLM=false` để trả lời tức thời bằng
template dựng sẵn.

Guardrail (`src/guardrails.py`) thuần regex/code, không LLM: chặn prompt
injection/nội dung độc hại, từ chối câu hỏi ngoài phạm vi, đối chiếu số
liệu output + redact PII + giới hạn độ dài.

## Prerequisites

- Python ≥ 3.11
- Postgres đang chạy, có sẵn 2 DB `its` và `virtual_fence` (hoặc tên khác,
  cấu hình qua `.env`) — xem mục "Tạo DB role read-only" bên dưới
- 1 API key OpenAI (hoặc Ollama chạy local — xem mục "Chuyển sang model local")

## Cài đặt & chạy local

Không có frontend/backend tách riêng — `static/index.html` (UI chat, HTML/JS
thuần) được chính FastAPI phục vụ, nên chỉ có 1 lệnh chạy duy nhất, không
cần chạy dev server frontend riêng (vd. `npm run dev`):

```bash
pip install -r requirements.txt
cp .env.example .env   # điền OPENAI_API_KEYS + DB_HOST/DB_USER/DB_PASSWORD
pytest                 # 5 passed — test offline, không cần DB/API key thật
uvicorn src.main:app --reload
```

Mở [http://localhost:8000](http://localhost:8000) (UI chat) hoặc
[http://localhost:8000/docs](http://localhost:8000/docs) (API tương tác).
`GET /health` để kiểm tra nhanh trạng thái backend/DB.

## Biến môi trường

Xem đầy đủ + giải thích từng biến trong [`.env.example`](.env.example).
Tóm tắt các nhóm chính:

| Nhóm | Biến | Ghi chú |
|---|---|---|
| LLM backend | `LLM_BACKEND`, `LLM_BASE_URL`, `OPENAI_API_KEYS`, `LLM_MODEL` | `openai` hoặc `ollama`, đổi backend chỉ qua `.env` |
| Answer | `ANSWER_USE_LLM` | `false` = luôn dùng template, không chờ LLM |
| Database | `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME_ITS`, `DB_NAME_FENCE` | Dùng role **read-only**, không phải admin |
| Guardrail | `GUARDRAILS_MIN_ANSWER_LEN`, `GUARDRAILS_MAX_ANSWER_LEN` | Giới hạn độ dài câu trả lời |

### Tạo DB role read-only

**Không dùng user admin/superuser cho agent.** Tạo 1 role riêng chỉ có
`SELECT` trên đúng 2 DB cần dùng:

```sql
CREATE ROLE agent_readonly WITH LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB PASSWORD '...';

-- Chạy trên từng DB (its, virtual_fence):
GRANT CONNECT ON DATABASE its TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;
```

Lưu ý: Postgres cấp `CONNECT` mặc định cho `PUBLIC` ở cluster — role này vẫn
"connect" được vào DB khác trên cùng server, nhưng **không đọc được dữ liệu**
nếu không có `GRANT SELECT` tường minh ở DB đó. Ứng dụng có thêm 1 lớp chặn
ở code (`src/db/connection.py`) chỉ cho phép kết nối tới đúng 2 DB đã cấu
hình trong `.env`, không phụ thuộc hoàn toàn vào quyền Postgres.

## Chuyển sang model local (4GB VRAM)

Không sửa code — chỉ đổi `.env`:

```bash
LLM_BACKEND=ollama
LLM_MODEL=qwen2.5:3b-instruct-q4_K_M   # hoặc model 3-4B khác vừa VRAM
# LLM_BASE_URL để trống -> tự dùng http://localhost:11434/v1
```

`src/llm.py` dùng chung 1 client (`ChatOpenAI` trỏ `base_url` khác) cho cả
2 backend — xem `_BACKENDS` trong file đó.

## Test

```bash
pytest -v
```

5 test case offline (`tests/test_offline.py`), không cần Postgres/API key
thật — xem chi tiết ở [`specs/test-plan.md`](specs/test-plan.md). Không có
`OPENAI_API_KEYS` (hoặc chạy dưới `pytest`) → agent tự chạy chế độ offline,
giả 1 tool_call thay vì gọi OpenAI thật.

Test thật (5 câu hỏi mẫu, cần `.env` đầy đủ): xem bảng trong
`specs/test-plan.md` mục "Test thật".

## Demo với local

Không có frontend/backend tách riêng (xem mục "Kiến trúc") nên **chỉ 1 lệnh,
1 cổng duy nhất** — không có bước "start frontend" và "start backend" riêng
biệt, và không có bước cấu hình API base URL cho frontend, vì
`static/index.html` gọi thẳng `fetch("/ask", ...)` bằng **relative path**
(cùng origin với chính trang đang mở), không hardcode host/port nào:

```bash
uvicorn src.main:app --reload --port 8000
```

- **UI (frontend)**: [http://localhost:8000/](http://localhost:8000/)
- **API (backend)**: cùng địa chỉ, cổng 8000 — `POST http://localhost:8000/ask`,
  `GET http://localhost:8000/health`, docs tương tác tại
  [http://localhost:8000/docs](http://localhost:8000/docs)

Đổi cổng (vd. máy đã dùng 8000) chỉ cần đổi `--port` khi chạy `uvicorn` —
`static/index.html` vẫn hoạt động đúng vì gọi relative path, không cần sửa
gì trong code hay `.env`.

## Demo với ngrok

App chỉ có 1 cổng duy nhất (FastAPI phục vụ cả API và static UI), nên demo
qua ngrok không cần cấu hình gì thêm:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
ngrok http 8000
```

Dùng URL `https://xxxx.ngrok-free.app` ngrok cấp — trỏ thẳng tới UI chat
(`/`) hoặc API (`/ask`, `/docs`).

## Troubleshooting

| Vấn đề | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `GET /` trả 404 | `static/index.html` không tồn tại (chưa `pip install` đủ hoặc chạy sai thư mục) | Kiểm tra file tồn tại, chạy `uvicorn` đúng từ thư mục gốc project |
| `POST /ask` trả `503` | DB/LLM lỗi kết nối (sai `.env`, Postgres chưa chạy, hết API key) | Kiểm tra `GET /health`, xem `db_configured`; kiểm tra `DB_HOST`/`OPENAI_API_KEYS` trong `.env` |
| Mọi câu hỏi đều bị từ chối "ngoài phạm vi" | Câu hỏi không chứa từ khoá nhận diện (`STAT_KEYWORDS` trong `src/guardrails.py`) | Hỏi cụ thể hơn, vd. "Hôm nay có bao nhiêu lượt xe vào?" thay vì câu quá chung chung |
| Câu trả lời chậm | Model local (Ollama) chạy trên máy yếu, hoặc `ANSWER_USE_LLM=true` chờ thêm 1 lời gọi LLM | Đặt `ANSWER_USE_LLM=false` để trả lời tức thời bằng template |
| `pytest` báo lỗi kết nối DB | Test offline không nên chạm DB thật — nếu lỗi, kiểm tra có đang chạy nhầm test thật (không có trong `tests/`) | Chỉ `tests/test_offline.py` là test chính thức, không kết nối DB thật |
