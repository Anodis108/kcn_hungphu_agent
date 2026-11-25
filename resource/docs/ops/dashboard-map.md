# Bản đồ Dashboard Vận hành (Ops Dashboard Map) — G16 MVP

Tài liệu này định nghĩa 7 widget giám sát cốt lõi cho hệ thống AI Agent `dong` (MVP wave v20), trỏ hoàn toàn vào các nguồn dữ liệu và endpoint sẵn có trong repo (`Langfuse`, application logs, `/ready`, `/api/feedback`).

---

## Danh mục 7 Widget Giám sát

| STT | Tên Widget | Nguồn dữ liệu | Chỉ số / Phép đo | Ngưỡng Cảnh báo (Alert Threshold) | Sổ tay xử lý liên quan |
|:---:|---|---|---|---|---|
| **1** | **Request & Latency P95** | Langfuse Traces | Latency (s) P50, P95, P99 | P95 first token > 3s hoặc E2E > 15s | [`latency-spike.md`](playbooks/latency-spike.md) |
| **2** | **Tỷ lệ lỗi (Error Rate)** | Langfuse + `agent_audit` | Tỷ lệ span lỗi / tổng trace | Error rate > 5% trong 5 phút | [`llm-down.md`](playbooks/llm-down.md) / [`bad-deploy-rollback.md`](playbooks/bad-deploy-rollback.md) |
| **3** | **Chi phí LLM / Ngày vs Ngân sách** | Langfuse Model Usage | Tổng USD / ngày theo model | Cảnh báo 50% ($2.5), 80% ($4.0), 100% ($5.0) | [`llm-down.md`](playbooks/llm-down.md) |
| **4** | **Token tiêu thụ / Lượt (P95)** | Langfuse Usage Metadata | Input / Output token P95 | Input P95 > 8k hoặc Output P95 > 1.5k | [`latency-spike.md`](playbooks/latency-spike.md) |
| **5** | **Supervisor Hops / Lượt** | Langfuse Trace Metadata | `metadata.supervisor_hops` | Hops > 3 (alert 50%), hops > 5 (80%), hops ≥ 6 (100%) | [`latency-spike.md`](playbooks/latency-spike.md) |
| **6** | **LLM Fallback & Circuit Breaker** | App Logs stdout | `llm_fallback_used`, `circuit_open` | `circuit_open` ≥ 1 lần hoặc fallback > 3 lần/10m | [`llm-down.md`](playbooks/llm-down.md) / [`db-down.md`](playbooks/db-down.md) |
| **7** | **Độ sẵn sàng `/ready` & Thumbs-down** | HTTP `/ready` + `/api/feedback` | Probe uptime & % rating == "negative" | `/ready` 503 > 2 lần liên tiếp; Thumbs-down > 15%/ngày | [`db-down.md`](playbooks/db-down.md) / [`bad-deploy-rollback.md`](playbooks/bad-deploy-rollback.md) |

---

## Chi tiết Cấu hình từng Widget

### Widget 1: Request & Latency P95 (Langfuse)
- **Mục tiêu**: Theo dõi thông lượng yêu cầu và độ trễ phản hồi theo thời gian thực.
- **Nguồn dữ liệu**: Langfuse Traces (`src/domain/observability/tracing.py`, trace roots mặc định `trace_name="chat"` trong `agent_turn.py` và `main.py`).
- **Bộ lọc & Truy vấn (Query/Filter)**:
  - Trace names: `name == "chat"` (hoặc wildcard `*` bao trùm toàn bộ các trace root nếu có override).
  - Metric: `duration` (giây) tính theo Percentile 50, 95, 99 theo cửa sổ trượt 5 phút (`time_window = 5m`).
- **Ngưỡng cảnh báo (product-spec §5.1)**:
  - **Warning**: P95 độ trễ hoàn tất toàn bộ lượt > 10.0 giây.
  - **Critical**: P95 first-token SSE > 3.0 giây hoặc E2E lượt > 15.0 giây.
- **Hành động**: Xem [`latency-spike.md`](playbooks/latency-spike.md), kiểm tra model throughput hoặc điều chỉnh `TRACE_SAMPLE_RATE`.

---

### Widget 2: Tỷ lệ lỗi (Error Rate — Langfuse & `agent_audit`)
- **Mục tiêu**: Phát hiện sớm sự cố sập logic, ngoại lệ chưa xử lý hoặc tool thất bại hàng loạt.
- **Nguồn dữ liệu**:
  - Langfuse Traces: Trace/Span có `level = "ERROR"` (gán tại `trace_answer` khi bắt exception).
  - Logger `agent_audit`: logger hệ thống (`src/domain/observability/audit.py`) phát log dòng JSON có `"status": "error"`.
- **Bộ lọc & Truy vấn (Query/Filter)**:
  - Langfuse: `count(traces where level == "ERROR") / count(total_traces) * 100` (cửa sổ 5 phút).
  - Log metric: `rate(container_log_lines{message=~'.*"status": "error".*'}[5m])`.
- **Ngưỡng cảnh báo**:
  - **Warning**: Error rate > 2% trong 5 phút.
  - **Critical**: Error rate > 5% trong 5 phút hoặc > 3 lỗi liên tiếp trong 1 phút.
- **Hành động**: Tra cứu `error` trong Langfuse span và kiểm tra log Uvicorn theo [`bad-deploy-rollback.md`](playbooks/bad-deploy-rollback.md).

---

### Widget 3: Chi phí LLM / Ngày vs Ngân sách (Langfuse)
- **Mục tiêu**: Giữ chi phí inference hàng ngày nằm trong giới hạn ngân sách $5/ngày theo đặc tả §5.1.
- **Nguồn dữ liệu**: Langfuse Model Usage & Cost Dashboard (`total_cost` tính theo bảng giá OpenAI/vLLM).
- **Bộ lọc & Truy vấn (Query/Filter)**:
  - Group by: `date(timestamp)`
  - Metric: `sum(calculated_total_cost)` (USD).
- **Ngưỡng cảnh báo (product-spec §5.1)**:
  - **Notice (50%)**: Tổng chi phí trong ngày đạt $2.50.
  - **Warning (80%)**: Tổng chi phí trong ngày đạt $4.00.
  - **Critical (100%)**: Tổng chi phí trong ngày đạt $5.00 (phát alert; chưa chặn runtime cứng).
- **Hành động**: Đổi primary model sang model rẻ hơn hoặc bật model fallback qua `config/models.yaml` theo [`llm-down.md`](playbooks/llm-down.md).

---

### Widget 4: Token tiêu thụ / Lượt (P95 — Langfuse Usage)
- **Mục tiêu**: Kiểm soát kích thước context window, tránh phình to prompt do Memory hoặc tool schema quá nặng.
- **Nguồn dữ liệu**: Langfuse Trace Usage metadata (`prompt_tokens`, `completion_tokens`, `total_tokens` được cập nhật tại `src/domain/observability/tracing.py`).
- **Bộ lọc & Truy vấn (Query/Filter)**:
  - Metric: P95 của `usage.prompt_tokens` (input) và `usage.completion_tokens` (output).
- **Ngưỡng cảnh báo (product-spec §5.1)**:
  - **Input tokens**: P95 > 8,000 tokens (ngưỡng 50%: 4.7k, 80%: 7.6k).
  - **Output tokens**: P95 > 1,500 tokens.
- **Hành động**: Rà soát cấu hình nén context (`AGENT_DECOMPOSE_MIN_CHARS`, Sliding Window, Summarization).

---

### Widget 5: Supervisor Hops / Lượt (Langfuse Metadata)
- **Mục tiêu**: Theo dõi số bước điều phối giữa các agent con, phòng tránh lặp vòng vô tận (loop protection).
- **Nguồn dữ liệu**: Langfuse trace metadata `supervisor_hops` (được inject trong `src/domain/agents/graph.py` và `src/domain/agents/nodes/supervisor.py`).
- **Bộ lọc & Truy vấn (Query/Filter)**:
  - Histogram / Max: `metadata.supervisor_hops` trên từng trace hoàn tất.
- **Ngưỡng cảnh báo (product-spec §5.1 & Phase 19.3)**:
  - **Notice (50%)**: `supervisor_hops > 3`.
  - **Warning (80%)**: `supervisor_hops > 5`.
  - **Critical (100%)**: `supervisor_hops >= 6` (chạm trần `SUPERVISOR_MAX_HOPS = 6`, `recursion_limit = 25`).
- **Hành động**: Kiểm tra độ phức tạp câu hỏi người dùng hoặc kiểm tra routing logic tại supervisor node.

---

### Widget 6: LLM Fallback & Circuit Breaker (Application Logs)
- **Mục tiêu**: Giám sát sức khỏe hạ tầng upstream LLM và cơ chế tự phục hồi / fail-fast của hệ thống.
- **Nguồn dữ liệu**: Application stdout log (Uvicorn / Docker container).
- **Bộ lọc & Truy vấn (Query/Filter)**:
  - Log grep / regex:
    - `"llm_fallback_used"` (từ `src/infra/llm/completion.py` và `src/infra/llm/structured.py`).
    - `"circuit_open"` (từ `src/infra/resilience/breaker.py`).
- **Ngưỡng cảnh báo**:
  - **Warning (P2)**: `"llm_fallback_used"` xuất hiện > 3 lần trong cửa sổ 10 phút.
  - **Critical (P1)**: `"circuit_open"` xuất hiện ≥ 1 lần (đã vượt ngưỡng 5 lỗi liên tiếp, chuyển sang ngắt mạch bảo vệ).
- **Hành động**: Kích hoạt quy trình xử lý sự cố upstream provider theo [`llm-down.md`](playbooks/llm-down.md) hoặc [`db-down.md`](playbooks/db-down.md).

---

### Widget 7: Độ sẵn sàng `/ready` & Tỷ lệ Thumbs-down (HTTP Endpoints)
- **Mục tiêu**: Đảm bảo SLA liveness/readiness của backend và phản hồi chất lượng thực tế từ người dùng cuối.
- **Nguồn dữ liệu**:
  - Endpoint kiểm tra phụ thuộc: `GET /ready` (hoặc `GET /api/ready` tại `src/api/routers/web_backend/routes_meta.py`, kiểm tra Postgres, Qdrant, LLM).
  - Endpoint phản hồi người dùng: `GET /api/feedback` (tại `src/api/routers/web_backend/routes_feedback.py`, schema rating: `"positive"` hoặc `"negative"`).
- **Bộ lọc & Truy vấn (Query/Filter)**:
  - Uptime Probe: `http_probe_status_code == 200` (đạt 200 là Healthy, 503 là Unhealthy).
  - Tỷ lệ Thumbs-down: `count(feedback where rating == "negative") / count(total_feedback) * 100` tính theo ngày.
- **Ngưỡng cảnh báo**:
  - **Readiness**: `/ready` trả HTTP 503 > 2 lần thăm dò liên tiếp (Uptime < 99.5%).
  - **User Sentiment**: Tỷ lệ thumbs-down trong ngày > 15% (với tối thiểu 10 phản hồi).
- **Hành động**:
  - Lỗi `/ready`: Xem log nguyên nhân (`status_details`) theo [`db-down.md`](playbooks/db-down.md).
  - Thumbs-down tăng: Chạy `scripts/feedback_to_golden.py` trích xuất golden draft để thẩm định theo Phụ lục C [`AUDIT-CHECKLIST.md`](../../eval/AUDIT-CHECKLIST.md).
