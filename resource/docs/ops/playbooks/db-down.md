# Sổ tay sự cố: Database Down / Gián đoạn cơ sở dữ liệu (PostgreSQL / Qdrant)

> Thuộc bộ Ops Playbooks (`resource/docs/ops/playbooks/`) — Chuẩn quy trình vận hành sự cố (G16).

---

## 1. Triệu chứng (Symptoms)

- Người dùng gửi yêu cầu nhưng nhận thông báo: *"Dữ liệu tạm thời không khả dụng"* hoặc *"Lỗi truy vấn cơ sở dữ liệu"*.
- Lịch sử hội thoại và bộ nhớ người dùng (Short-term / Long-term Memory) không thể ghi nhận hoặc trích xuất từ bảng `user_memories`.
- Endpoint kiểm tra sức khỏe và sẵn sàng trả về mã lỗi **HTTP 503 Service Unavailable**:
  - `GET /ready` hoặc `GET /api/ready` có `checks.postgres = "failed"` hoặc `checks.qdrant = "failed"`.
- Log ứng dụng ghi nhận ngoại lệ liên quan đến kết nối:
  - `psycopg2.OperationalError: could not connect to server` hoặc `connection refused`.
  - `qdrant_client.http.exceptions.ResponseHandlingException`.

---

## 2. Phát hiện (Detection: Log & Metric)

### 2.1. Kiểm tra trạng thái Ready Endpoint
```bash
curl -s http://localhost:8000/ready | jq .
```
*Dấu hiệu nhận diện:*
```json
{
  "ready": false,
  "checks": {
    "postgres": "failed",
    "qdrant": "ok",
    "llm": "ok"
  },
  "details": {
    "postgres": "could not connect to server: Connection refused"
  }
}
```

### 2.2. Kiểm tra trạng thái các container cơ sở dữ liệu
```bash
docker compose ps agent_postgres qdrant
```
Quan sát cột `STATUS` xem container có đang ở trạng thái `Restarting` hoặc `Exited` không.

### 2.3. Xem log dịch vụ PostgreSQL
```bash
docker compose logs --tail=100 agent_postgres
```
Tìm kiếm các lỗi phổ biến: `FATAL: remaining connection slots are reserved`, `PANIC: could not locate a valid checkpoint record`, hoặc lỗi cấp phát bộ nhớ.

### 2.4. Xem log dịch vụ Qdrant
```bash
docker compose logs --tail=100 qdrant
```

### 2.5. Kiểm tra log kiểm toán (`agent_audit`)
```bash
docker compose logs --tail=200 ai_backend | grep "agent_audit" | grep "execute_sql"
```
Quan sát các tool call liên quan đến SQL bị lỗi hoặc có thời gian phản hồi bất thường.

---

## 3. Xử lý từng bước (Step-by-step Resolution)

### Bước 1: Kiểm tra tài nguyên máy chủ host
Cơ sở dữ liệu thường bị dừng đột ngột do thiếu dung lượng đĩa hoặc RAM:
```bash
# Kiểm tra dung lượng đĩa mount dữ liệu ./resource/db/agent/data/
df -h

# Kiểm tra dung lượng bộ nhớ RAM
free -m
```
*Lưu ý:* Nếu đĩa đầy (>95%), tiến hành dọn dẹp các file log cũ trong `orca_setup/logs/` hoặc docker prune trước khi khởi động lại DB.

### Bước 2: Kiểm tra lệnh pg_isready nội bộ
```bash
docker compose exec -T agent_postgres pg_isready -U atin -d kcn_agent
```
Hoặc dùng biến môi trường cấu hình:
```bash
docker compose exec -T agent_postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

### Bước 3: Khởi động lại container cơ sở dữ liệu
Nếu container bị dừng:
```bash
docker compose start agent_postgres qdrant
```
Nếu container bị treo hoặc lỗi kết nối:
```bash
docker compose restart agent_postgres
docker compose restart qdrant
```

### Bước 4: Kiểm tra kết nối mạng nội bộ giữa các container trong mạng `kcn_network`
Kiểm tra kết nối port 5432 (Postgres) và 6333 (Qdrant) từ container `ai_backend`:
```bash
docker compose exec -T ai_backend python -c "
import socket
for host, port in [('agent_postgres', 5432), ('qdrant', 6333)]:
    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect((host, port))
        print(f'{host}:{port} -> CONNECTED')
    except Exception as e:
        print(f'{host}:{port} -> FAILED: {e}')
    finally:
        s.close()
"
```

### Bước 5: Khởi động lại backend để làm mới connection pool
Sau khi cơ sở dữ liệu hoạt động trở lại, khởi động lại `ai_backend` để đặt lại các kết nối pool bị hỏng:
```bash
docker compose restart ai_backend
```

---

## 4. Xác nhận phục hồi (Recovery Verification)

### Bước 1: Kiểm tra lại endpoint `/ready`
```bash
curl -f http://localhost:8000/ready
```
*Kỳ vọng:* HTTP 200, `"ready": true`, `"checks": {"postgres": "ok", "qdrant": "ok", ...}`.

### Bước 2: Thực thi truy vấn kiểm tra dữ liệu thật
Kiểm tra truy vấn bảng bộ nhớ và số liệu:
```bash
docker compose exec -T agent_postgres psql -U atin -d kcn_agent -c "SELECT count(*) FROM user_memories;"
```
*Kỳ vọng:* Trả về số dòng hợp lệ mà không có lỗi kết nối.

### Bước 3: Kiểm thử endpoint Stream có sử dụng SQL tool
```bash
curl -X POST http://localhost:8000/api/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Cho tôi biết tổng diện tích khu công nghiệp?", "user_id": "ops_verify", "session_id": "ping_db"}'
```
*Kỳ vọng:* Nhận kết quả phân tích số liệu thành công mà không bị ngắt kết nối.

---

## 5. Hậu kiểm (Post-mortem & Follow-up)

1. **Phân tích nguyên nhân gốc rễ (RCA):**
   - Sự cố do OOM Killer của hệ điều hành, kết nối quá giới hạn `max_connections`, hay phân vùng đĩa lưu trữ `pgdata` bị đầy.
2. **Kiểm tra tính toàn vẹn dữ liệu:**
   - Đối chiếu dữ liệu gần nhất trong bảng `user_memories` và kiểm tra file khởi tạo `resource/db/agent/init.sql`.
3. **Cải tiến phòng ngừa:**
   - Bổ sung cấu hình circuit breaker (20.4) cho kết nối cơ sở dữ liệu để fail-fast, tránh treo thread worker.
   - Thiết lập cảnh báo dung lượng đĩa cho thư mục `./resource/db/agent/data/pgdata`.
   - Lập lịch backup định kỳ cho cơ sở dữ liệu PostgreSQL.
