# Checklist Kiểm thử Thủ công — Nested Langfuse Trace (v13 / Phase 23.1)

Tài liệu hướng dẫn kiểm thử thủ công phân tầng span cây quan sát (nested traces) trên giao diện web Langfuse nhằm nghiệm thu [AC-9](../../../specs/product-spec.md#L144) và [test-plan §1.1](../../../specs/test-plan.md#L24) (AC-T1–T3).

---

## 1. Mục tiêu kiểm thử

Xác nhận khi bật giám sát (`MONITORING_ENABLED=true`):
- Mọi node LangGraph được bọc bởi span cấp 1 (`_wrap_node`).
- Các tác vụ logic con bên trong node được bọc bởi span cấp 2 (`trace_step`) hiển thị dạng cây phân cấp (tree view) trên Langfuse.
- Nhánh `execute_sql` khi thực thi batch ≥ 2 câu truy vấn phải ghi nhận riêng biệt ≥ 2 substeps tương ứng.
- Không rò rỉ dữ liệu nhạy cảm hay làm ảnh hưởng luồng phản hồi SSE của người dùng.

---

## 2. Điều kiện tiên quyết (Prerequisites)

1. **Hạ tầng Langfuse sẵn sàng**:
   - Dịch vụ Langfuse (Web UI + Server) đang hoạt động (ví dụ qua `docker-compose.observability.yml` tại `http://localhost:3000` hoặc máy chủ dev).
2. **Cấu hình môi trường (.env)**:
   ```env
   MONITORING_ENABLED=true
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=http://localhost:3000
   ```
3. **Backend khởi chạy**:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

---

## 3. Các bước kiểm thử thủ công (Checklist)

### Bước 1: Kiểm thử lượt chat đơn (Single Query)

1. Gửi câu hỏi đơn giản qua Web UI (`http://localhost:8000`) hoặc cURL:
   ```bash
   curl -X POST http://localhost:8000/api/agent/stream \
     -H "Content-Type: application/json" \
     -d '{"question": "Hôm nay có bao nhiêu lượt xe vào?", "session_id": "test-manual-1", "user_id": "tester"}'
   ```
2. Mở Langfuse UI → mục **Traces** → chọn trace có `name="chat"` mới nhất.
3. Kiểm tra cây phân cấp (Tree View):
   - [ ] Span gốc `chat` chứa đầy đủ metadata (session_id, user_id).
   - [ ] Node span ngoài (`_wrap_node`): xuất hiện các span `guardrail_input`, `recall`, `rewrite`, `classify`, `top_supervisor`, `analytics_team`, `execute_sql`, `respond`.
   - [ ] Substeps (`trace_step`):
     - Dưới `guardrail_input`: có substep `check_input`, `redact_pii`.
     - Dưới `recall`: có substep `recall_long_term`.
     - Dưới `rewrite`: có substep `rewrite_query`.
     - Dưới `execute_sql`: có substep `postgres_query` hoặc `clickhouse_query`.

### Bước 2: Kiểm thử SQL batch ≥ 2

1. Gửi câu hỏi phức tạp yêu cầu thực thi nhiều câu SQL đồng thời:
   ```bash
   curl -X POST http://localhost:8000/api/agent/stream \
     -H "Content-Type: application/json" \
     -d '{"question": "So sánh số lượt xe ra và vào hôm nay", "session_id": "test-manual-batch", "user_id": "tester"}'
   ```
2. Trên Langfuse UI, mở trace `chat` vừa sinh ra.
3. Điều hướng vào span `execute_sql`:
   - [ ] Xác nhận có **≥ 2 substeps `postgres_query`** (hoặc từng câu SQL riêng biệt).
   - [ ] Mỗi substep ghi nhận đúng câu lệnh SQL tương ứng, thời gian thực thi (latency), và trạng thái `status="ok"`.

---

## 4. Tiêu chí nghiệm thu (Acceptance Criteria Mapping)

| Mã AC | Tiêu chí | Kết quả mong đợi | Trạng thái |
|-------|----------|-------------------|:----------:|
| **AC-9** | Nested Langfuse substeps | Cây trace hiển thị đúng cấu trúc node cha (`_wrap_node`) và logic con (`trace_step`) | [ ] Đạt |
| **AC-T1** | Span tối thiểu | Node `guardrail_input`, `recall`, `rewrite` có substeps tương ứng | [ ] Đạt |
| **AC-T2** | SQL Batch | `execute_sql` khi có batch ≥ 2 có ≥ 2 substeps per query | [ ] Đạt |
| **AC-T3** | Unit test hồi quy | `pytest tests/integration_db/test_product_observability_errors.py -q` pass | [ ] Đạt |
