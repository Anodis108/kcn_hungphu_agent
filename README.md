# agent_ATIN (kcn_hungphu_agent)

Trợ lý AI hỏi-đáp thống kê toàn bộ sự kiện VMS (phương tiện, vùng cấm, khuôn mặt, ẩu đả, đám đông, leo trèo, cháy khói, giám sát mực nước) dựa trên **spec-driven development**.

Toàn bộ **9 phase** trong [`specs/implementation-plan.md`](specs/implementation-plan.md) nay đã hoàn thành 100% (bao gồm 8 domain sự kiện VMS, Langfuse Observability self-host và Git-based Prompt Registry).

Tham khảo tài liệu dự án:
- [`specs/product-spec.md`](specs/product-spec.md) — mục tiêu, đối tượng sử dụng, tính năng in/out scope & acceptance criteria
- [`specs/implementation-plan.md`](specs/implementation-plan.md) — kế hoạch 9 phase với đầy đủ checklist items
- [`specs/test-plan.md`](specs/test-plan.md) — kịch bản kiểm thử offline, kiểm thử thật & prompt registry
- [`specs/change-log.md`](specs/change-log.md) — nhật ký chi tiết tất cả các đợt phát triển & review
- [`AGENTS.md`](AGENTS.md) — quy tắc phát triển cho coding agent

---

## Tính năng Phục vụ (Features Can Serve)

Agent cho phép người vận hành hỏi-đáp bằng tiếng Việt tự nhiên qua giao diện Web UI hoặc API RESTful, tự động chọn đúng tool truy vấn dữ liệu Postgres thật và trả lời ngắn gọn:

### 1. Phủ 8 Domain Sự kiện VMS
| Domain sự kiện | Bảng dữ liệu | Ví dụ câu hỏi |
|---|---|---|
| **Giám sát phương tiện** (`PLATE`) | `its.plate_event` | "Hôm nay có bao nhiêu lượt xe vào?", "Thống kê xe theo hãng", truy vết biển số XXXX |
| **Giám sát vùng cấm** (`ZONE`) | `virtual_fence.zone_event` | "Khung thời gian nào xảy ra xâm nhập khu vực nhiều nhất hôm nay?" |
| **Nhận diện khuôn mặt** (`FACE`) | `smart_face.smf_face_events` | "Hôm nay có bao nhiêu lượt nhận diện khuôn mặt?" |
| **Phát hiện ẩu đả** (`FIGHT`) | `anomaly.anomaly_event` | "Hôm nay có vụ ẩu đả nào không?" |
| **Phát hiện đám đông** (`CROWD`) | `anomaly.anomaly_event` | "Hôm nay có cảnh báo đám đông ở khu vực nào không?" |
| **Phát hiện leo trèo** (`INTRUSION`) | `anomaly.anomaly_event` | "Hôm nay có phát hiện leo trèo không?" (phân biệt rõ với vùng cấm) |
| **Phát hiện cháy khói** (`FIRE`) | `firesmoke.fire_smoke_event` | "Hôm nay có cảnh báo cháy hoặc khói không?" |
| **Giám sát mực nước** (`WATER_LEVEL`) | `anomaly.anomaly_event` | "Mực nước hôm nay có vượt ngưỡng cảnh báo không?" |

### 2. An toàn & Guardrails (Bằng Code thuần, không qua LLM)
- **Input Guardrail**: Chặn prompt injection độc hại, từ chối lịch sự câu hỏi ngoài phạm vi thống kê VMS.
- **Output Guardrail**: Che giấu thông tin cá nhân (PII), đối chiếu kết quả với dữ liệu thật từ DB, giới hạn độ dài câu trả lời.

### 3. Git-based Prompt Registry (LLMOps)
- Toàn bộ prompt được quản lý trong thư mục `prompts/` dạng YAML kèm tệp pointer `production.txt`.
- Đổi phiên bản prompt production hoặc rollback chỉ bằng cách sửa `production.txt` (hoặc git revert commit) mà **không cần sửa hay deploy lại code Python**.
- Tự động validate biến truyền vào template: raise lỗi `ValueError` rõ ràng nếu thiếu biến bắt buộc.

### 4. Observability — Langfuse Tracing Self-hosted
- Tự động trace từng lượt `/ask` (cây span: `ask` → `chon_tool` → `chay_tool` → `dien_giai`).
- Mặc định tắt (`MONITORING_ENABLED=false`). Chạy self-hosted qua Docker Compose trên chính máy này, không gửi dữ liệu ra bên ngoài.

---

## Prerequisites (Yêu cầu Tiền đề)

1. **Python**: Môi trường Python ≥ 3.11 (hoặc Conda / venv).
2. **Database Postgres**: Có sẵn 5 Database nguồn:
   - `its` (Giám sát phương tiện)
   - `virtual_fence` (Vùng cấm)
   - `smart_face` (Nhận diện khuôn mặt)
   - `firesmoke` (Cháy khói)
   - `anomaly` (Ẩu đả, đám đông, leo trèo, mực nước)
3. **LLM Provider**:
   - Lựa chọn A: **OpenAI API Key** (`gpt-4o-mini` hoặc tương đương).
   - Lựa chọn B: **Ollama Local** (`qwen2.5:3b-instruct` chạy local cho GPU 4GB VRAM).
4. **(Tuỳ chọn) Docker & Docker Compose**: Nếu cần bật hạ tầng Langfuse tracing quan sát nội bộ.

---

## Install Commands (Cài đặt)

```bash
# 1. Clone repository & chuyển vào thư mục dự án
cd /home/atin/dong/dong/KCNHungPhu/kcn_hungphu_agent

# 2. Cài đặt các thư viện Python cần thiết
pip install -r requirements.txt

# 3. Tạo tệp cấu hình môi trường từ mẫu
cp .env.example .env

# 4. Điền các thông tin kết nối Database và LLM Key vào tệp .env

# 5. Chạy bộ test offline để xác nhận môi trường đã sẵn sàng
pytest -v
# Kết quả kỳ vọng: 21 passed (100% passed)
```

---

## Environment Variables (Biến Môi trường)

Cấu hình trong tệp `.env` (xem giải thích chi tiết tại [`.env.example`](.env.example)):

| Nhóm | Biến | Mặc định | Giải thích |
|---|---|---|---|
| **LLM Backend** | `LLM_BACKEND` | `openai` | `openai` hoặc `ollama` |
| | `OPENAI_API_KEYS` | (cần điền) | Danh sách API key (phân cách bằng dấu phẩy) |
| | `LLM_BASE_URL` | (để trống) | Đổi endpoint nếu dùng Ollama (`http://localhost:11434/v1`) |
| | `LLM_MODEL` | `gpt-4o-mini` | Tên model LLM sử dụng |
| **Answer Mode** | `ANSWER_USE_LLM` | `true` | `false` = trả về câu template ngay lập tức (dùng khi GPU yếu) |
| **Databases** | `DB_HOST` | `192.168.1.250` | IP/Host server Postgres |
| | `DB_PORT` | `5432` | Cổng Postgres |
| | `DB_USER` | `agent_readonly` | User Postgres (bắt buộc role READ-ONLY) |
| | `DB_PASSWORD` | (cần điền) | Mật khẩu user read-only |
| | `DB_NAME_ITS` | `its` | Tên DB giám sát phương tiện |
| | `DB_NAME_FENCE` | `virtual_fence` | Tên DB vùng cấm |
| | `DB_NAME_FACE` | `smart_face` | Tên DB khuôn mặt |
| | `DB_NAME_FIRE` | `firesmoke` | Tên DB cháy khói |
| | `DB_NAME_ANOMALY` | `anomaly` | Tên DB sự kiện bất thường |
| | `DB_ORGANIZATION_ID`| `106` | ID tổ chức cần lọc số liệu |
| **Guardrails** | `GUARDRAILS_MIN_ANSWER_LEN` | `5` | Độ dài tối thiểu câu trả lời hợp lệ |
| | `GUARDRAILS_MAX_ANSWER_LEN` | `2000` | Độ dài tối đa câu trả lời |
| **Observability** | `MONITORING_ENABLED` | `false` | `true` = bật gửi trace sang Langfuse self-hosted |
| | `LANGFUSE_PUBLIC_KEY` | (cần điền) | Public key Langfuse |
| | `LANGFUSE_SECRET_KEY` | (cần điền) | Secret key Langfuse |
| | `LANGFUSE_HOST` | `http://localhost:3000` | URL server Langfuse |

### Thiết lập DB Role Read-Only trên Postgres

Ứng dụng bắt buộc dùng user đọc-only để đảm bảo an toàn tuyệt đối cho Database:

```sql
-- 1. Tạo role read-only trên server Postgres (chạy 1 lần):
CREATE ROLE agent_readonly WITH LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB PASSWORD 'your_password_here';

-- 2. Cấp quyền kết nối & đọc bảng trên CẢ 5 Database (chạy khi connect vào từng DB):
-- Thực hiện lần lượt cho từng DB: its, virtual_fence, smart_face, firesmoke, anomaly
GRANT CONNECT ON DATABASE <dbname> TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;
```

---

## Local Run Instructions (Chạy Ứng dụng Local)

### 1. Kiến trúc Đơn cổng (Single Service Architecture)
Ứng dụng sử dụng **1 FastAPI Service duy nhất** phục vụ cả Backend API lẫn Frontend UI tệp tĩnh (`static/index.html`).
- **Không có backend và frontend tách rời**: Frontend giao tiếp với Backend thông qua đường dẫn tương đối `/ask`, không gặp lỗi CORS hay khác biệt Origin.
- **Do đó, KHÔNG CẦN câu lệnh chạy frontend và backend riêng biệt.**

### 2. Backend & Frontend Run Command
Chạy ứng dụng bằng 1 lệnh duy nhất từ thư mục gốc của dự án:

```bash
uvicorn src.main:app --reload --port 8000
```

Nếu muốn lắng nghe kết nối từ bên ngoài (hoặc expose qua ngrok):
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## Local URLs (Đường dẫn Địa phương)

Sau khi khởi chạy `uvicorn`, các địa chỉ truy cập trên máy cục bộ bao gồm:

| Trang / Endpoint | URL | Mô tả |
|---|---|---|
| **Frontend UI Chat** | [http://localhost:8000/](http://localhost:8000/) | Giao diện Chat trực quan (HTML/JS thuần) |
| **Backend API Ask** | `POST http://localhost:8000/ask` | Endpoint nhận câu hỏi `{"question": "..."}` và trả về câu trả lời |
| **Health Check API** | [http://localhost:8000/health](http://localhost:8000/health) | Kiểm tra trạng thái service và kết nối DB |
| **API Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Tài liệu API tương tác tự động |
---

## Demo with local

Section này hướng dẫn chi tiết cách khởi chạy ứng dụng local và expose ra internet để demo bằng `ngrok`:

### 1. Start Frontend & Backend Locally
Dự án được thiết kế theo kiến trúc **Single Service** (1 ứng dụng FastAPI duy nhất phục vụ cả Backend API lẫn tệp tĩnh Frontend UI `static/index.html` tại cùng 1 origin):
- **Khởi chạy Backend & Frontend chung**:
  ```bash
  uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Cổng sử dụng thực tế (Actual Ports)**:
  - **Backend API & Frontend UI**: Cổng **`8000`** (`http://localhost:8000/` cho UI Chat và `http://localhost:8000/ask` cho API Endpoint).
  - **Observability UI** (Langfuse, nếu bật): Cổng **`3000`** (`http://localhost:3000/`).

### 2. Expose Frontend & Backend
Vì Frontend và Backend phục vụ chung 1 service trên cổng `8000`, bạn **chỉ cần expose duy nhất 1 cổng 8000**:
```bash
ngrok http 8000
```
- Ngrok sẽ cấp 1 URL công khai HTTPS dạng `https://xxxx.ngrok-free.app`.
- **Expose Frontend**: Truy cập `https://xxxx.ngrok-free.app/` trực tiếp trên trình duyệt từ thiết bị ngoài.
- **Expose Backend**: Endpoint API tự động có sẵn tại `https://xxxx.ngrok-free.app/ask` và tài liệu Swagger tại `https://xxxx.ngrok-free.app/docs`.

### 3. Configure Frontend API Base URL to Use Backend URL
- Giao diện UI (`static/index.html`) được lập trình sử dụng **đường dẫn tương đối (relative path)**:
  ```javascript
  const response = await fetch('/ask', { method: 'POST', ... });
  ```
- **Tự động tương thích Origin**: Khi mở UI qua URL local (`http://localhost:8000/`) hay URL ngrok (`https://xxxx.ngrok-free.app/`), trình duyệt tự động gửi các yêu cầu API tới đúng Host/Origin tương ứng của Backend mà **không cần sửa hay cấu hình lại bất kỳ dòng code nào** trong `static/index.html` hoặc tệp `.env`.

---

## Hướng dẫn Quản lý Prompt với Prompt Registry

Bạn có thể chỉnh sửa câu chữ hoặc thay đổi phiên bản Prompt đang chạy production mà **không cần sửa hay khởi động lại ứng dụng**:

1. **Xem prompt hiện tại**: Tệp `prompts/agent_system/production.txt` chứa số `"1"` trỏ tới `prompts/agent_system/v1.yaml`.
2. **Chuyển sang version mới**: Thay đổi nội dung tệp `prompts/agent_system/production.txt` thành `"2"`. Ứng dụng sẽ tự động tải `prompts/agent_system/v2.yaml` ở lượt gọi tiếp theo.
3. **Rollback**: Sửa `production.txt` quay lại `"1"` (hoặc dùng `git checkout prompts/agent_system/production.txt`).

---

## Troubleshooting Notes (Xử lý Lỗi Thường gặp)

| Lỗi / Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `GET /` trả về `404 Not Found` | Thư mục `static/index.html` bị thiếu hoặc chạy `uvicorn` không đúng thư mục gốc dự án | Đảm bảo đang đứng ở `/home/atin/dong/dong/KCNHungPhu/kcn_hungphu_agent` khi chạy `uvicorn` |
| `POST /ask` trả về `503 Service Unavailable` | Lỗi kết nối DB Postgres hoặc chưa cấu hình OpenAI API key / Ollama | Truy cập `http://localhost:8000/health` xem chi tiết trạng thái kết nối `db_configured`. Kiểm tra lại `DB_HOST`, `DB_PASSWORD` hoặc `OPENAI_API_KEYS` trong `.env` |
| Câu hỏi hợp lệ bị báo "Ngoài phạm vi" | Câu hỏi thiếu từ khóa thống kê nhận diện trong `STAT_KEYWORDS` (`src/guardrails.py`) | Sử dụng câu hỏi cụ thể rõ ràng hơn, ví dụ: "Hôm nay có bao nhiêu lượt xe vào?" thay vì "Xe cộ ra sao?" |
| Lỗi `ValueError: Thiếu biến khi render prompt` | Tệp YAML prompt mới định nghĩa biến placeholder (vd. `{context}`) mà code chưa truyền vào | Kiểm tra lại danh sách các biến được định nghĩa trong tệp `prompts/<prompt_name>/vX.yaml` |
| Lỗi `httpx2` khi gọi OpenAI API | Thư viện `openai` bản mới kéo theo gói `httpx2` bị lỗi đệm nén | Đảm bảo đã ghim `openai==2.45.0` trong `requirements.txt` bằng cách chạy `pip install -r requirements.txt` |
| Báo lỗi permission `DELETE/UPDATE` trên DB | User Postgres đang dùng là `agent_readonly` | Đây là tính năng an toàn cố ý của hệ thống. Agent chỉ có quyền `SELECT` đọc dữ liệu |
| Langfuse down khiến API chậm | `MONITORING_ENABLED=true` nhưng container Langfuse bị dừng | API vẫn trả về kết quả bình thường cho người dùng (lỗi tracing được tự động nuốt). Để khắc phục độ trễ, bật lại container Langfuse (`cd langfuse && docker compose up -d`) hoặc đặt `MONITORING_ENABLED=false` |
