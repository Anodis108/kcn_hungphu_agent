# Sổ tay sự cố: LLM Down / Gián đoạn dịch vụ mô hình ngôn ngữ

> Thuộc bộ Ops Playbooks (`resource/docs/ops/playbooks/`) — Chuẩn quy trình vận hành sự cố (G16).

---

## 1. Triệu chứng (Symptoms)

- Người dùng nhận thông báo lỗi khi chat: *"Hệ thống đang quá tải hoặc gặp sự cố kết nối tới mô hình AI"* hoặc stream SSE bị đứt đoạn giữa chừng.
- Yêu cầu xử lý ngôn ngữ bị timeout sau 15–30 giây (mặc định timeout của client).
- Endpoint sẵn sàng trả về mã lỗi **HTTP 503 Service Unavailable**:
  - `GET /ready` hoặc `GET /api/ready` có `checks.llm = "failed"`.
- Endpoint kiểm tra kết nối mô hình trả về lỗi:
  - `GET /api/llm/ping` trả về mã lỗi **HTTP 503 Service Unavailable** (kèm `{"detail": "..."}`).

---

## 2. Phát hiện (Detection: Log & Metric)

### 2.1. Log Fallback từ backend
Kiểm tra log container `ai_backend` để phát hiện cảnh báo chuyển sang mô hình fallback:
```bash
docker compose logs --tail=200 ai_backend | grep "llm_fallback_used"
```
*Dấu hiệu nhận diện:*
```text
WARNING:root:llm_fallback_used: primary=gpt-4o-mini failed with ...; trying fallback=Qwen/Qwen2.5-7B-Instruct
```

### 2.2. Kiểm tra Ready Endpoint
```bash
curl -s http://localhost:8000/ready | jq .
```
Nếu LLM gặp sự cố, phản hồi sẽ có dạng:
```json
{
  "ready": false,
  "checks": {
    "postgres": "ok",
    "qdrant": "ok",
    "llm": "failed"
  },
  "details": {
    "llm": "Connection error / Timeout"
  }
}
```

### 2.3. Ping trực tiếp LLM qua endpoint quản trị
```bash
curl -s http://localhost:8000/api/llm/ping | jq .
```

### 2.4. Langfuse Latency & Errors
Truy cập dashboard Langfuse (`http://localhost:3001` hoặc URL cấu hình qua `LANGFUSE_HOST`):
- Kiểm tra các trace có status `ERROR`.
- Quan sát độ trễ các span `llm_completion` hoặc `chat_stream` tăng vọt hoặc kết thúc bằng exception.

### 2.5. Kiểm tra log kiểm toán tool calls (`agent_audit`)
```bash
docker compose logs --tail=200 ai_backend | grep "agent_audit" | grep '"status": "error"'
```
*(Ghi chú: Trong code, logger `agent_audit` ghi nhận `status="error"` khi có lỗi; có thể dùng `grep -E '"status": "(error|failed)"'` để bao quát cả hai định dạng).*

---

## 3. Xử lý từng bước (Step-by-step Resolution)

### Bước 1: Kiểm tra cấu hình và tình trạng nhà cung cấp hiện tại
Đọc cấu hình định tuyến mô hình trong repo:
```bash
cat config/models.yaml
```
Kiểm tra biến môi trường liên quan đến API key và base URL:
```bash
grep -E "LLM_|MODEL_|OPENAI_" .env
```

### Bước 2: Kiểm tra kết nối mạng tới Provider
- **Với LLM Self-hosted (vLLM / Bonsai / Qwen):**
  ```bash
  curl -I "${MODEL_BASE_URL:-http://192.168.1.198:18083/v1}/models"
  ```
- **Với Cloud Provider (OpenAI):**
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
  ```

### Bước 3: Đổi cấu hình Primary / Fallback trong `config/models.yaml`
Nếu nhà cung cấp primary (ví dụ OpenAI) bị sập hoặc cạn quota, chuyển model từ danh sách `fallbacks` lên làm `primary`:
```yaml
# config/models.yaml
primary:
  provider: self_hosted
  model: Qwen/Qwen2.5-7B-Instruct
  base_url_env: MODEL_BASE_URL
  api_key_env: MODEL_API_KEY
  timeout: 15.0

fallbacks:
  - provider: openai
    model: gpt-4o-mini
    base_url_env: LLM_BASE_URL
    api_key_env: OPENAI_API_KEYS
    timeout: 15.0
```

### Bước 4: Khởi động lại service backend hoặc cập nhật biến môi trường
Nếu cần chuyển hẳn sang chế độ backend khác qua `.env`:
```bash
# Cập nhật backend trong .env nếu cần
sed -i 's/LLM_BACKEND=.*/LLM_BACKEND=self_hosted/' .env

# Tải lại container ai_backend
docker compose up -d --no-deps ai_backend
```
Hoặc restart nhanh container:
```bash
docker compose restart ai_backend
```

---

## 4. Xác nhận phục hồi (Recovery Verification)

### Bước 1: Kiểm tra readiness probe
```bash
curl -f http://localhost:8000/ready
```
*Kỳ vọng:* HTTP 200, `"ready": true`, `"checks": {"llm": "ok", ...}`.

### Bước 2: Kiểm tra ping LLM
```bash
curl -f http://localhost:8000/api/llm/ping
```
*Kỳ vọng:* HTTP 200 kèm `{"status": "ok", "backend": ..., "model": ...}`.

### Bước 3: Gửi tin nhắn kiểm thử E2E
Gửi một lượt chat thử nghiệm qua API stream:
```bash
curl -X POST http://localhost:8000/api/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Xin chào, phản hồi nhanh nếu bạn đang hoạt động", "user_id": "ops_verify", "session_id": "ping_llm"}'
```
*Kỳ vọng:* Nhận được phản hồi câu trả lời hợp lệ mà không có lỗi fallback.

### Bước 4: Giám sát log sau phục hồi
```bash
docker compose logs --tail=50 ai_backend
```
Đảm bảo không còn log `llm_fallback_used` liên tục do lỗi kết nối.

---

## 5. Hậu kiểm (Post-mortem & Follow-up)

1. **Ghi nhận sự cố:**
   - Thời gian bắt đầu và kết thúc sự cố (downtime / degraded period).
   - Tỷ lệ yêu cầu bị ảnh hưởng và số lượt kích hoạt fallback.
2. **Xác định nguyên nhân gốc (RCA):**
   - Hết quota thanh toán, rate limit từ nhà cung cấp bên thứ ba, hay sự cố mạng nội bộ tới GPU cluster.
3. **Biện pháp phòng ngừa:**
   - Thiết lập cảnh báo hạn mức ngân sách và số dư API key trước khi cạn kiệt.
   - Kiểm tra ngưỡng timeout trong `config/models.yaml` (15s) có phù hợp với tải thực tế không.
   - Sau khi nhà cung cấp chính ổn định, lên lịch chuyển lại cấu hình `primary` chuẩn và lưu nhật ký vào `specs/change-log.md`.
