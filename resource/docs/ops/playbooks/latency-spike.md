# Sổ tay sự cố: Latency Spike / Tăng đột biến độ trễ phản hồi

> Thuộc bộ Ops Playbooks (`resource/docs/ops/playbooks/`) — Chuẩn quy trình vận hành sự cố (G16).

---

## 1. Triệu chứng (Symptoms)

- Người dùng phản ánh hệ thống phản hồi rất chậm (> 15–30 giây cho mỗi lượt trả lời).
- SSE stream quay vòng chờ đợi lâu trước khi token đầu tiên xuất hiện (Time to First Token - TTFT cao).
- Tỷ lệ client bị timeout hoặc chủ động hủy kết nối (SSE disconnect) tăng cao.
- Langfuse dashboard ghi nhận độ trễ P95/P99 vượt ngưỡng bình thường (> 5.0 giây).
- Tải CPU hoặc tiêu hao bộ nhớ của container `ai_backend` tăng cao đột biến.

---

## 2. Phát hiện (Detection: Log & Metric)

### 2.1. Phân tích qua Langfuse Dashboard
Truy cập giao diện Langfuse (`http://localhost:3001` hoặc biến `LANGFUSE_HOST`):
- Mở mục **Traces**, sắp xếp theo cột **Duration (giảm dần)**.
- Kiểm tra span cụ thể nào chiếm phần lớn thời gian:
  - `llm_completion` / `chat_stream`: Tắc nghẽn do mô hình ngôn ngữ phản hồi chậm.
  - `sql_agent` / `execute_sql`: Tắc nghẽn do truy vấn cơ sở dữ liệu nặng.
  - `docs_agent` / `search_knowledge`: Tắc nghẽn do tìm kiếm embedding hoặc Qdrant.
  - `supervisor` / `orchestrator_multi_active`: Tắc nghẽn do phân rã câu hỏi thành quá nhiều câu hỏi con chạy tuần tự.

### 2.2. Kiểm tra log kiểm toán độ trễ (`agent_audit`)
Trích xuất các lệnh tool call có thời gian xử lý (`duration_ms`) cao nhất từ log container:
```bash
docker compose logs --tail=500 ai_backend | grep "agent_audit" | sed -E 's/^[^{]*//' | jq -r '[.tool, .duration_ms, .status] | @tsv' | sort -k2 -n -r | head -n 10
```

### 2.3. Kiểm tra trạng thái tài nguyên container
```bash
docker stats --no-stream
```
Quan sát các cột `CPU %` và `MEM USAGE / LIMIT` của container `kcn_hungphu_backend`.

### 2.4. Kiểm tra các câu truy vấn SQL đang chạy lâu trong PostgreSQL
```bash
docker compose exec -T agent_postgres psql -U atin -d kcn_agent -c "
SELECT pid, now() - query_start AS duration, state, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC
LIMIT 5;
"
```

---

## 3. Xử lý từng bước (Step-by-step Resolution)

### Bước 1: Phân loại điểm nghẽn chính
Dựa trên thông tin ở phần 2, xác định nguyên nhân:

#### Nhánh A: Nghẽn do LLM Provider phản hồi chậm
1. Kiểm tra cấu hình timeout trong `config/models.yaml`:
   ```bash
   cat config/models.yaml
   ```
2. Nếu model primary (ví dụ Cloud) đang bị suy giảm hiệu năng (degraded performance), chuyển sang model có throughput cao hơn hoặc chuyển sang fallback:
   Sửa `config/models.yaml` hoặc cấu hình biến môi trường:
   ```bash
   # Giảm số lượng câu hỏi con phân rã để giảm số turn gọi LLM
   sed -i 's/AGENT_MAX_SUB_QUESTIONS=.*/AGENT_MAX_SUB_QUESTIONS=2/' .env
   sed -i 's/AGENT_DECOMPOSE_MIN_CHARS=.*/AGENT_DECOMPOSE_MIN_CHARS=60/' .env
   ```

#### Nhánh B: Nghẽn do câu truy vấn cơ sở dữ liệu bị treo (Long-running Query)
1. Hủy (kill) truy vấn bị treo quá lâu:
   ```bash
   docker compose exec -T agent_postgres psql -U atin -d kcn_agent -c "SELECT pg_cancel_backend(<pid_tu_buoc_2>);"
   ```
2. Nếu truy vấn vẫn không kết thúc, cưỡng chế ngắt:
   ```bash
   docker compose exec -T agent_postgres psql -U atin -d kcn_agent -c "SELECT pg_terminate_backend(<pid_tu_buoc_2>);"
   ```

#### Nhánh C: Nghẽn do Telemetry/Tracing quá tải
1. Điều chỉnh giảm tần suất sampling trace (`TRACE_SAMPLE_RATE` — cấu hình thuộc Phase 20.5):
   ```bash
   # Giảm tỷ lệ lấy mẫu trace xuống 20% (khi Phase 20.5 đã triển khai)
   echo "TRACE_SAMPLE_RATE=0.2" >> .env
   ```

### Bước 2: Khởi động lại hoặc reload backend container
Áp dụng cấu hình và giải phóng tài nguyên bị giữ:
```bash
docker compose up -d --no-deps ai_backend
```
Hoặc restart:
```bash
docker compose restart ai_backend
```

---

## 4. Xác nhận phục hồi (Recovery Verification)

### Bước 1: Đo thời gian phản hồi của endpoint agent stream
Chạy kiểm tra đo lường thời gian đáp ứng (latency probe):
```bash
time curl -s -X POST http://localhost:8000/api/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Kiểm tra độ trễ hệ thống", "user_id": "ops_bench", "session_id": "latency_test"}' \
  -o /dev/null
```
*Kỳ vọng:* Thời gian hoàn thành (real time) giảm xuống mức bình thường (< 5.0 giây).

### Bước 2: Kiểm tra độ trễ tool calls trong `agent_audit`
```bash
docker compose logs --tail=50 ai_backend | grep "agent_audit"
```
*Kỳ vọng:* Giá trị `duration_ms` trở về ngưỡng an toàn (< 1500ms cho các tác vụ nội bộ).

### Bước 3: Quan sát biểu đồ thời gian thực trên Langfuse
Kiểm tra các trace mới nhất trên Langfuse để xác nhận không còn hiện tượng span kéo dài bất thường.

---

## 5. Hậu kiểm (Post-mortem & Follow-up)

1. **Ghi nhận số liệu hiệu năng:**
   - Đỉnh điểm latency P95/P99 trong thời gian sự cố so với mức nền (baseline).
2. **Đánh giá câu hỏi người dùng & mẫu truy vấn:**
   - Xem xét câu hỏi nào kích hoạt phân rã câu hỏi con phức tạp hoặc câu lệnh SQL quét qua nhiều bảng lớn.
3. **Cải tiến phòng ngừa:**
   - Áp dụng Tool Output Compression (AC-7) để giảm số token nạp vào LLM.
   - Bổ sung chỉ mục (Index) cho các cột thường xuyên được lọc trong PostgreSQL.
   - Điều chỉnh cấu hình `AGENT_MAX_SUB_QUESTIONS` và `MEMORY_TTL_SECONDS` phù hợp với tải thực tế.
