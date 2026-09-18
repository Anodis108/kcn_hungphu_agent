# agent_ATIN

Chatbot thống kê sự kiện VMS (phương tiện, vùng cấm, khuôn mặt, ẩu đả, đám
đông, leo trèo, cháy khói, mực nước) — dùng **spec-driven development**.
Toàn bộ 8 phase trong `specs/implementation-plan.md` đã hoàn thành (xem
`specs/change-log.md` để biết chi tiết từng bước). Xem:

- [`specs/product-spec.md`](specs/product-spec.md) — mục tiêu, phạm vi, acceptance criteria
- [`specs/implementation-plan.md`](specs/implementation-plan.md) — checklist từng phase
- [`specs/test-plan.md`](specs/test-plan.md) — cách test
- [`specs/change-log.md`](specs/change-log.md) — lịch sử thay đổi
- [`AGENTS.md`](AGENTS.md) — quy tắc cho coding agent khi triển khai
- [`agent-canvas.md`](agent-canvas.md) — tổng hợp & phân tích Agent Canvas (harness VMS, model deploy, bên thứ 3)

> **Còn treo (chưa có phase kế hoạch):** Prompt Registry — xem mục "Ghi
> chú" cuối [`specs/implementation-plan.md`](specs/implementation-plan.md).

## Tính năng agent phục vụ được

Hỏi bằng tiếng Việt tự nhiên qua UI chat hoặc API, agent trả lời thống kê
dựa trên dữ liệu Postgres thật cho **8 domain sự kiện**:

| Domain | Ví dụ câu hỏi |
|---|---|
| Phương tiện (PLATE) | "Hôm nay có bao nhiêu lượt xe vào?", truy vết biển số, thống kê theo hãng xe |
| Vùng cấm / hàng rào ảo (ZONE) | "Khung giờ nào xâm nhập khu vực nhiều nhất hôm nay?" |
| Nhận diện khuôn mặt (FACE) | "Hôm nay có bao nhiêu lượt nhận diện khuôn mặt?" |
| Ẩu đả (FIGHT) | "Hôm nay có vụ ẩu đả nào không?" |
| Đám đông (CROWD) | "Hôm nay có cảnh báo đám đông không?" |
| Leo trèo (INTRUSION) | "Hôm nay có phát hiện leo trèo không?" |
| Cháy khói (FIRE) | "Hôm nay có cảnh báo cháy hoặc khói không?" |
| Mực nước (WATER_LEVEL) | "Mực nước hôm nay có vượt ngưỡng cảnh báo không?" |

Ngoài ra: guardrail chặn prompt injection/câu hỏi ngoài phạm vi (xem mục
"Kiến trúc"), và quan sát nội bộ (không phải tính năng người dùng cuối)
qua Langfuse tự host — xem mục "Chạy Langfuse (tuỳ chọn)".

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
- Postgres đang chạy, có sẵn 5 DB nguồn (`its`, `virtual_fence`,
  `smart_face`, `firesmoke`, `anomaly` — hoặc tên khác, cấu hình qua
  `.env`) — xem mục "Tạo DB role read-only" bên dưới
- 1 API key OpenAI (hoặc Ollama chạy local — xem mục "Chuyển sang model local")
- (Tuỳ chọn) Docker + Docker Compose — chỉ cần nếu muốn bật quan sát nội
  bộ qua Langfuse tự host, xem mục "Chạy Langfuse (tuỳ chọn)"

## Cài đặt

Không có frontend/backend tách riêng — `static/index.html` (UI chat, HTML/JS
thuần) được chính FastAPI phục vụ:

```bash
pip install -r requirements.txt
cp .env.example .env   # điền OPENAI_API_KEYS + DB_HOST/DB_USER/DB_PASSWORD
pytest                 # 12 passed — test offline, không cần DB/API key thật
```

## Biến môi trường

Xem đầy đủ + giải thích từng biến trong [`.env.example`](.env.example).
Tóm tắt các nhóm chính:

| Nhóm | Biến | Ghi chú |
|---|---|---|
| LLM backend | `LLM_BACKEND`, `LLM_BASE_URL`, `OPENAI_API_KEYS`, `LLM_MODEL` | `openai` hoặc `ollama`, đổi backend chỉ qua `.env` |
| Answer | `ANSWER_USE_LLM` | `false` = luôn dùng template, không chờ LLM |
| Database | `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME_ITS`, `DB_NAME_FENCE`, `DB_NAME_FACE`, `DB_NAME_FIRE`, `DB_NAME_ANOMALY` | Dùng role **read-only**, không phải admin. 3 biến `DB_NAME_*` cuối là domain mới (khuôn mặt, cháy khói, ẩu đả/đám đông/leo trèo/mực nước) — xem mục "Tạo DB role read-only" |
| Guardrail | `GUARDRAILS_MIN_ANSWER_LEN`, `GUARDRAILS_MAX_ANSWER_LEN` | Giới hạn độ dài câu trả lời |
| Observability | `MONITORING_ENABLED`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | Mặc định `MONITORING_ENABLED=false` — không cần chạy Langfuse để dùng phần còn lại của app. Bật `true` + điền key thật để xem trace từng lượt `/ask`, xem mục "Chạy Langfuse (tuỳ chọn)" |

### Tạo DB role read-only

**Không dùng user admin/superuser cho agent.** Tạo 1 role riêng chỉ có
`SELECT` trên đúng các DB cần dùng:

```sql
CREATE ROLE agent_readonly WITH LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB PASSWORD '...';

-- Chạy trên từng DB (its, virtual_fence):
GRANT CONNECT ON DATABASE its TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;
```

3 DB domain mới (`smart_face`, `firesmoke`, `anomaly`) — cùng pattern,
CHỈ đổi tên DB, tái dùng đúng role `agent_readonly` đã tạo ở trên (không
cần tạo role mới):

```sql
-- Chạy trên từng DB (smart_face, firesmoke, anomaly):
GRANT CONNECT ON DATABASE smart_face TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;

GRANT CONNECT ON DATABASE firesmoke TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;

GRANT CONNECT ON DATABASE anomaly TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;
```

Mỗi lệnh `GRANT`/`ALTER DEFAULT PRIVILEGES` phải chạy khi đang **kết nối
tới đúng DB đó** (`psql -d <dbname>`) — `GRANT ... ON DATABASE` chạy từ
bất kỳ đâu, nhưng `GRANT USAGE ON SCHEMA`/`GRANT SELECT ON ALL TABLES`/
`ALTER DEFAULT PRIVILEGES` áp dụng cho schema/bảng của DB đang kết nối,
không phải DB đích trong câu lệnh.

Lưu ý: Postgres cấp `CONNECT` mặc định cho `PUBLIC` ở cluster — role này vẫn
"connect" được vào DB khác trên cùng server, nhưng **không đọc được dữ liệu**
nếu không có `GRANT SELECT` tường minh ở DB đó. Ứng dụng có thêm 1 lớp chặn
ở code (`src/db/connection.py`) chỉ cho phép kết nối tới đúng 5 DB đã cấu
hình trong `.env`, không phụ thuộc hoàn toàn vào quyền Postgres.

## Chạy local — 1 lệnh duy nhất (frontend + backend chung service)

**Không có bước "chạy frontend" và "chạy backend" riêng biệt.**
`static/index.html` (UI chat, HTML/JS thuần — vai trò "frontend") được
chính FastAPI (vai trò "backend") phục vụ tại cùng 1 cổng, và gọi
`fetch("/ask", ...)` bằng **relative path** (cùng origin), không hardcode
host/port nào — nên chỉ cần:

```bash
uvicorn src.main:app --reload --port 8000
```

### Local URLs

| URL | Vai trò |
|---|---|
| [http://localhost:8000/](http://localhost:8000/) | UI chat (frontend) |
| `POST http://localhost:8000/ask` | API hỏi-đáp (backend) |
| [http://localhost:8000/health](http://localhost:8000/health) | Kiểm tra nhanh trạng thái backend/DB |
| [http://localhost:8000/docs](http://localhost:8000/docs) | API docs tương tác (Swagger) |

Đổi cổng (vd. máy đã dùng 8000) chỉ cần đổi `--port` khi chạy `uvicorn` —
`static/index.html` vẫn hoạt động đúng vì gọi relative path, không cần sửa
gì trong code hay `.env`.

## Chuyển sang model local (4GB VRAM)

Không sửa code — chỉ đổi `.env`:

```bash
LLM_BACKEND=ollama
LLM_MODEL=qwen2.5:3b-instruct-q4_K_M   # hoặc model 3-4B khác vừa VRAM
# LLM_BASE_URL để trống -> tự dùng http://localhost:11434/v1
```

`src/llm.py` dùng chung 1 client (`ChatOpenAI` trỏ `base_url` khác) cho cả
2 backend — xem `_BACKENDS` trong file đó.

## Chạy Langfuse (tuỳ chọn — quan sát nội bộ, không bắt buộc)

Tự host bằng Docker Compose chính thức của Langfuse — không dùng Langfuse
Cloud:

```bash
cd langfuse
docker compose up -d          # lần đầu: tự tạo project + API key qua LANGFUSE_INIT_*
docker compose ps             # xác nhận đủ 6 container Up/healthy
```

- UI: [http://localhost:3000](http://localhost:3000) — đăng nhập bằng
  `LANGFUSE_INIT_USER_EMAIL`/`LANGFUSE_INIT_USER_PASSWORD` trong
  `langfuse/.env` (file tự sinh, không commit).
- Lấy `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` từ
  `LANGFUSE_INIT_PROJECT_PUBLIC_KEY`/`_SECRET_KEY` trong `langfuse/.env`,
  điền vào `.env` của app (mục "Biến môi trường" ở trên) + đặt
  `MONITORING_ENABLED=true`.
- Dừng: `docker compose down` (giữ data) / thêm `-v` để xoá sạch data.

## Test

```bash
pytest -v
```

12 test case offline (`tests/test_offline.py` + `tests/
test_db_guardrail_new_dbs.py`, tự `skip` phần cần DB thật nếu `.env` chưa
cấu hình) — xem chi tiết ở [`specs/test-plan.md`](specs/test-plan.md).
Không có `OPENAI_API_KEYS` (hoặc chạy dưới `pytest`) → agent tự chạy chế
độ offline, giả 1 tool_call thay vì gọi OpenAI thật.

Test thật (5 câu hỏi mẫu PLATE/ZONE gốc + 6 câu hỏi mẫu domain mới, cần
`.env` đầy đủ): xem bảng trong `specs/test-plan.md` mục "Test thật".

Chạy full golden dataset (30 case, 8 domain, cần `.env` đầy đủ):

```bash
python eval/run.py
```

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
| `pytest` báo lỗi kết nối DB | Test offline không nên chạm DB thật — nếu lỗi, kiểm tra có đang chạy nhầm test thật (không có trong `tests/`) | Chỉ `tests/test_offline.py` là test chính thức không cần DB; `tests/test_db_guardrail_new_dbs.py` tự `skip` nếu `.env` chưa cấu hình |
| Agent trả lời sai domain (vd. hỏi mực nước ra kết quả cháy/khói) | Model chọn nhầm tool khi 2 câu hỏi dùng chung từ khoá (vd. "cảnh báo") | Đã có ghi chú loại trừ tường minh trong docstring từng tool (`src/agent/tools.py`) — nếu vẫn gặp câu hỏi mới bị nhầm domain, thêm ghi chú loại trừ tương tự ở ĐẦU docstring 2 tool dễ nhầm |
| `pip install openai` lấy bản mới bị lỗi `httpx2` khi gọi LLM thật | `openai` không ghim version, bản mới phụ thuộc `httpx2` có bug tương thích | Đã ghim `openai==2.45.0` trong `requirements.txt` — chạy lại `pip install -r requirements.txt` |
| `docker compose up` (Langfuse) báo lỗi bind port | Cổng `3000`/`9190`/`5432`/`6379`/`8123`/`9000` đã bị service khác trên máy dùng | Đổi port mapping trong `langfuse/docker-compose.yml` (giữ nguyên port bên phải dấu `:`, chỉ đổi port host bên trái) |
| Langfuse không nhận trace / UI trống | `MONITORING_ENABLED=false` (mặc định) hoặc key sai | Đặt `MONITORING_ENABLED=true` + đúng `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY` từ `langfuse/.env`; nếu Langfuse service down, `/ask` vẫn trả lời bình thường (chỉ chậm thêm vài giây), không lộ lỗi ra response |
