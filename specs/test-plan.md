# Test Plan — agent dong v9: Unified Memory & Context Engineering System (Postgres-backed)

**Trạng thái:** Spec only — Chuẩn bị thực hiện.  
**Mục tiêu:** Kiểm thử toàn diện hệ thống Memory 3 tầng (Short-Term, Long-Term, TTL Cache) lưu trữ trên PostgreSQL và Context Engineering Engine (`context.py`), đảm bảo tính bền vững, cách ly dữ liệu, quản lý cửa sổ ngữ cảnh tối ưu và không làm đứt gãy các luồng nghiệp vụ hiện tại.

---

## 1. Phạm vi kiểm thử

| Nhóm tính năng | Mục tiêu kiểm thử | Phương thức |
|----------------|-------------------|-------------|
| **PostgreSQL Long-Term Storage** | Lưu trữ và truy vấn facts người dùng vào bảng `user_memories` trong PostgreSQL. Dữ liệu không bị mất khi restart server. | Unit test + DB check |
| **User Data Isolation** | Tuyệt đối không rò rỉ facts giữa các `user_id` khác nhau. | Unit test tự động |
| **In-Memory Fallback** | Khi ngắt kết nối PostgreSQL hoặc cấu hình DB rỗng, hệ thống tự động fallback in-memory, không crash. | Unit test tự động |
| **Context Engineering Engine** | Kiểm thử 5 kỹ thuật: Sliding Window, 40-60% Compaction rule, Summarization hội thoại cũ, Tool output compression, và Re-injecting instructions. | Unit test tự động |
| **Short-Term Checkpointer** | Khởi tạo checkpointer bền vững trên PostgreSQL (fallback `MemorySaver` khi chạy local/test). | Unit test tự động |
| **TTL Response Cache** | Cache Hit phản hồi nhanh < 10ms; hết hạn TTL tự động miss; thread-safe khi nhiều request đồng thời. | Unit test tự động |
| **Smart Fact Extraction** | Nhận diện chính xác tên, vai trò, sở thích; lọc bỏ không lưu số liệu giao thông/realtime tạm bợ. | Unit test tự động |
| **End-to-End Regression** | Đảm bảo 100% các tính năng cũ (Text-to-SQL, 10 camera, Human Feedback, Streaming) tiếp tục hoạt động trơn tru. | Chạy toàn bộ pytest suite |
| **Nested Langfuse trace (v13)** | Mọi node graph có substeps `trace_step` theo design; batch SQL trace từng câu. | pytest + manual Langfuse |

---

## 1.1 Observability — nested trace (v13)

**AC:** `product-spec.md` AC-9.

| ID | Kiểm thử | Kỳ vọng |
|----|---------|---------|
| **AC-T1** | Mock `trace_step`, invoke node tối thiểu (`guardrail_input`, `recall`, `rewrite`, `classify`) | Danh sách tên span con khớp bảng design §3 |
| **AC-T2** | `execute_sql_node` với `sql_batch` ≥ 2 (offline/mock DB) | ≥ 2 substeps `postgres_query` (hoặc validate tương đương per item) |
| **AC-T3** | `pytest tests/integration_db/test_observability_db.py -q` | Pass; không regression test graph hành vi |

**Manual:** Xem checklist chi tiết tại [`resource/docs/ops/langfuse-nested-trace-manual.md`](../resource/docs/ops/langfuse-nested-trace-manual.md). Một lượt chat với `MONITORING_ENABLED=true` → Langfuse trace `chat` hiển thị cây substeps dưới `rewrite`, `recall`, `execute_sql` (và SQL batch ≥ 2 substeps per query).

---

## 2. Kế hoạch kiểm thử tự động (Unit Tests)

### Test Suite 1: Context Engineering Engine (`tests/integration_db/test_memory_db.py`)
- **Các ca kiểm thử**:
  1. `test_sliding_window_preserves_system_and_recent`:
     - Tạo danh sách 25 message (gồm 1 system message ở đầu và 24 turn qua lại).
     - Gọi `sliding_window(messages, max_messages=10)`.
     - Kỳ vọng: Trả về danh sách gồm 11 message (1 system message gốc + 10 message gần nhất), không bị lặp system message.
  2. `test_estimate_tokens_and_context_usage`:
     - Gọi `estimate_tokens` trên danh sách message mẫu.
     - Kiểm tra `context_usage` với `window_tokens=4000`.
     - Kỳ vọng: Giá trị trả về nằm trong khoảng [0.0, 1.0].
  3. `test_should_compact_activates_at_40_percent`:
     - Giả lập danh sách message chiếm 20% dung lượng window -> `should_compact` trả về `False`.
     - Giả lập danh sách message chiếm 45% dung lượng window (vượt ngưỡng 40%) -> `should_compact` trả về `True`.
  4. `test_summarize_old_messages_creates_summary_message`:
     - Tạo danh sách 15 message.
     - Gọi `summarize_old_messages(messages, keep_recent=4)`.
     - Kỳ vọng: Kết quả trả về 5 message gồm 1 system message mang tiền tố `[Tóm tắt hội thoại trước]: ...` và 4 message mới nhất.
  5. `test_compress_tool_result_skips_short_output`:
     - Kết quả tool ngắn (< 300 token * 4 ký tự): hàm `compress_tool_result` trả về nguyên bản chuỗi gốc mà không gọi LLM nén.
  6. `test_compress_tool_result_compresses_long_output`:
     - Kết quả tool dài (chuỗi bảng số liệu > 2000 ký tự): hàm `compress_tool_result` kích hoạt LLM nén và trả về đoạn trích xuất cô đọng.
  7. `test_reinject_instructions_appends_to_end`:
     - Gọi `reinject_instructions(messages, "Quy tắc an toàn VMS KCN")`.
     - Kỳ vọng: Tin nhắn cuối cùng trong danh sách trả về là system message mang tiền tố `[Nhắc lại chỉ dẫn]: ...`.
  8. `test_latest_human_query_scans_backwards`:
     - Quét ngược qua chuỗi tin nhắn có xen kẽ tool call và tool result.
     - Kỳ vọng: Trả về chính xác nội dung câu hỏi gần nhất của người dùng (`role in ('human', 'user')`).
  9. `test_detect_repetition_detects_infinite_loop`:
     - Giả lập 4 tool call liên tiếp giống hệt nhau (`window=4`).
     - Kỳ vọng: Trả về `True` kích hoạt cảnh báo `REPETITION_WARNING` ngắt vòng lặp vô tận.
  10. `test_create_compaction_diff_persists_to_state`:
      - Gọi `create_compaction_diff(messages, keep_recent=4)`.
      - Kỳ vọng: Trả về diff gồm danh sách `RemoveMessage(id)` cho các message cũ và 1 `SystemMessage` mang tiền tố `[Tóm tắt hội thoại trước]: ...` để mutate trực tiếp vào LangGraph state.
  11. `test_should_compact_route_conditional_edge`:
      - Kiểm tra routing của conditional edge: vượt 40% window trả về `"compact"`, ngược lại trả về `"continue"`.

### Test Suite 2: Long-Term Memory & PostgreSQL Persistence (`tests/hermetic/test_memory.py`)
- **Các ca kiểm thử**:
  1. `test_init_memory_db_creates_table_safely`:
     - Chạy hàm `init_memory_db()`.
     - Xác nhận bảng `user_memories` và index được tạo thành công nếu có DB, hoặc log warning an toàn nếu không có DB.
  2. `test_save_and_recall_long_term_postgres`:
     - Gọi `save_to_long_term("user_123", "Tôi thích giám sát camera cổng số 1")`.
     - Gọi `recall_long_term("user_123", "hôm nay xem camera cổng 1 nhé")`.
     - Kỳ vọng: Kết quả trả về danh sách chứa fact đã lưu.
  3. `test_user_isolation_strictly_enforced`:
     - Lưu fact cho `user_A`: *"Tôi tên là Nguyễn Văn An"*.
     - Lưu fact cho `user_B`: *"Tôi tên là Trần Thị Bình"*.
     - Gọi `recall_long_term("user_A", "tôi tên là gì")` -> Chỉ thấy fact của `user_A`, tuyệt đối không có `user_B`.
  4. `test_fallback_to_in_memory_when_db_down`:
     - Giả lập lỗi kết nối PostgreSQL (mock exception).
     - Gọi `save_to_long_term` và `recall_long_term`.
     - Kỳ vọng: Không ném ngoại lệ; dữ liệu được lưu tạm và đọc ra từ in-memory fallback store.
  5. `test_clear_long_term_by_user`:
     - Gọi `clear_long_term("user_123")`.
     - Xác nhận fact của `user_123` bị xóa, facts của user khác vẫn giữ nguyên.

### Test Suite 3: TTL Cache & Expiration (`tests/integration_db/test_ttl_cache_db.py`)
- **Các ca kiểm thử**:
  1. `test_ttl_cache_hit_and_miss`:
     - Set cache cho key `q_hash`.
     - Lấy lại khi chưa hết hạn -> Cache Hit (trả về data nguyên vẹn).
     - Query key khác -> Cache Miss (trả về `None`).
  2. `test_ttl_cache_expires_after_ttl`:
     - Set cache với `ttl=1` giây.
     - Đợi 1.1 giây.
     - Gọi `get_ttl_cached` -> Kỳ vọng trả về `None` và tự xóa key hết hạn khỏi bộ nhớ.
  3. `test_make_cache_key_normalization`:
     - Hai chuỗi khác hoa thường hoặc khoảng trắng đầu cuối (ví dụ: `"  Lưu lượng xe? "` và `"lưu lượng xe?"`) phải sinh ra cùng một `make_cache_key`.

### Test Suite 4: Smart Extraction & Realtime Filtering
- **File**: `tests/integration_db/test_memory_db.py`
- **Các ca kiểm thử**:
  1. `test_heuristic_extract_name_and_role`:
     - Input: *"Chào bạn, tôi tên là Hùng, tôi phụ trách an ninh KCN Hưng Phú"*.
     - Kỳ vọng: Trích xuất được fact tên và vai trò.
  2. `test_extraction_ignores_realtime_traffic_stats`:
     - Input: *"Hôm nay có 150 lượt xe tải vào cổng"* và câu trả lời thống kê.
     - Với `detail="query_data"`, hàm `extract_memories` không được lưu số liệu thống kê realtime vào long-term memory.

---

## 3. Kịch bản kiểm thử thủ công (Manual / Smoke Checklist)

| STT | Thao tác trên giao diện Web | Kỳ vọng quan sát được |
|:---:|------------------------------|------------------------|
| 1 | Mở web chat (`http://localhost:8080`), gửi: *"Chào bạn, tôi tên là Tuấn, tôi phụ trách giám sát an ninh ca đêm"* | Trợ lý phản hồi chào lịch sự, ghi nhận danh tính. Server trích xuất và lưu fact vào PostgreSQL (`user_memories`). |
| 2 | Gửi câu hỏi tiếp theo trong cùng phiên: *"Khu vực tôi phụ trách là gì?"* | Trợ lý nhớ và trả lời: *"Bạn phụ trách giám sát an ninh ca đêm"*. (Kiểm tra Short-Term & Long-Term memory hoạt động). |
| 3 | Mở tab ẩn danh mới hoặc bấm tạo phiên mới với cùng `user_id`: *"Tôi là ai?"* | Trợ lý vẫn trả lời đúng: *"Bạn là Tuấn, phụ trách an ninh ca đêm"* (chứng minh Long-Term memory đã được lưu bền vững vào PostgreSQL và nạp lại thành công). |
| 4 | Trò chuyện liên tục qua hơn 10 câu hỏi nghiệp vụ | Trợ lý phản hồi nhanh, không bị lag hoặc đơ do tràn context; các chỉ dẫn quy tắc an toàn VMS vẫn được tuân thủ nghiêm ngặt (chứng minh Sliding Window & Instruction Re-injection hoạt động tốt). |
| 5 | Gửi câu hỏi thống kê: *"Hôm nay có bao nhiêu lượt xe vào KCN?"* | Trợ lý truy vấn SQL và trả về số liệu chính xác kèm biểu đồ. Nếu bảng dữ liệu dài, kết quả được nén súc tích trước khi tổng hợp câu trả lời. |
| 6 | Gửi lại ngay lập tức câu hỏi y hệt: *"Hôm nay có bao nhiêu lượt xe vào KCN?"* | Trợ lý trả về kết quả gần như ngay lập tức (< 50ms) do TTL Cache Hit, không thấy log query SQL hay gọi lại LLM trên console. |
| 7 | Tạm dừng database PostgreSQL hoặc đổi cấu hình `DB_HOST=invalid` rồi gửi câu hỏi chat | Ứng dụng vẫn hoạt động bình thường, ghi nhận log warning nhẹ và tự động chuyển sang in-memory fallback mà không báo lỗi 500 ra giao diện. |

---

## 4. v19 Gap wave — acceptance (AC-13)

Mỗi task 19.x có mục **Test** riêng trong `specs/implementation-plan.md` § v19. Tối thiểu:

| Task | Test tự động | Smoke |
|---|---|---|
| 19.2 | `tests/test_product_ready_sse.py` (200/503, disconnect dừng stream) | `curl :8000/ready`; đóng tab giữa stream → log `sse_client_disconnected` |
| 19.3 | supervisor lặp → dừng ≤ max hops; `GraphRecursionError` không 500 | Langfuse có `supervisor_hops` |
| 19.4 | primary fail → fallback | `/api/models` OK |
| 19.5 | DML bị chặn; timeout; audit JSON | log `agent_audit` |
| 19.6 | gate exit 0/1 theo baseline | `python resource/eval/run.py --gate` |
| 19.7 | JSONL build + `--dry-run` | — |
| 19.8 | filters → `ui_navigate` whitelist | nút "Mở trang" trên web |
| 19.9 | ~~gRPC~~ superseded by 22.2 (SSE only) | — |
| 19.10 | thumbs-down → draft YAML | đọc `AUDIT-CHECKLIST.md` |

Hồi quy chung: `PYTHONPATH=. pytest -q` xanh sau mỗi task.

---

## 5. v20 Ops wave — acceptance (AC-14)

| Task | Kiểm tra | Pass khi |
|---|---|---|
| 20.1 | `docker build` + run + `curl /ready`, `id -u` | build OK, 10001, health 200, compose vẫn chạy |
| 20.2 | Actions trên PR | xanh; assert hỏng → đỏ |
| 20.3 | review 4 playbook | đủ 5 mục; lệnh/endpoint tồn tại |
| 20.4 | unit breaker (open/half-open/close, LLM→fallback, SQL fail-fast) | pass |
| 20.5 | unit sample rate | pass |
| 20.6 | review dashboard-map + gap | 7 widget có nguồn thật |

Hồi quy: `PYTHONPATH=. pytest -q` xanh sau mỗi task.

---

## 6. v21 CI/CD local-first — acceptance (AC-15)

| Task | Kiểm tra | Pass khi |
|---|---|---|
| 21.1 | `ruff check .`, prompt lint; Actions | 2 job, `tests` needs `checks`; lỗi lint → tests skip |
| 21.2 | `run.py --offline --gate` local + PR path | exit 0/1 đúng baseline; chỉ chạy khi đụng path |
| 21.3 | `release.sh build/deploy/smoke/rollback/status` | smoke OK; rollback về `.lkg` |
| 21.4 | `cd` sau CI xanh (hoặc dispatch) | build+smoke xanh không secret; `deploy` skipped |

Không cần GCP project/secret cloud để nghiệm thu.

---

## 7. v22 Test layout hermetic / integration_db / live — acceptance

Phân bổ test suite theo 3 thư mục chuyên biệt:

1. **`tests/hermetic/`** (24 test files `test_*.py` + 1 helper; 25 khi còn gRPC): Bộ kiểm thử unit hermetic offline hoàn toàn không phụ thuộc live services (DB, Qdrant, LLM API keys). Chạy trên CI:
   ```bash
   PYTHONPATH=. pytest tests/hermetic -q
   ```
2. **`tests/integration_db/`** (24 test files): Bộ kiểm thử tích hợp yêu cầu cơ sở dữ liệu thật (PostgreSQL, ClickHouse, Qdrant, LLM live). Giữ nguyên vẹn cho môi trường tích hợp:
   ```bash
   PYTHONPATH=. pytest tests/integration_db -q
   ```
3. **`tests/live/`** (`test_v18_iam_live.py`): Bộ kiểm thử live IAM với tài khoản thật. Yêu cầu `IAM_LIVE=1`, `IAM_TEST_PASSWORD`, `IAM_BASE_URL`:
   ```bash
   IAM_LIVE=1 IAM_TEST_PASSWORD=... IAM_BASE_URL=... PYTHONPATH=. pytest tests/live -q
   ```

Acceptance criteria:
- CI job `tests` trong `.github/workflows/ci.yml` chạy `pytest tests/hermetic -q` (bỏ danh sách `--ignore`).
- `PYTHONPATH=. pytest tests/hermetic -q` kết thúc với **exit code 0** (182 passed sau khi gỡ gRPC 22.2; 188 passed khi còn test_product_grpc.py tại 22.1).
- Các suite DB/ops trong `tests/integration_db/` được bảo toàn nguyên vẹn.

---

## 8. v23 Capability Collapse — Test file mapping

Bảng đối chiếu gom nhóm các test file cũ sang cấu trúc capability tối giản:

### Nhóm Memory & TTL Cache (Phase 23.3)

| File cũ | File mới sau Phase 23.3 | Loại | Số test |
|---|---|:---:|:---:|
| `tests/hermetic/test_product_memory_postgres.py` | `tests/hermetic/test_memory.py` | Hermetic | 3 |
| `tests/hermetic/test_product_memory_ttl_cache.py` | `tests/hermetic/test_memory.py` | Hermetic | 11 |
| **Tổng Hermetic Memory** | `tests/hermetic/test_memory.py` | | **14** |
| `tests/integration_db/test_product_memory_api.py` | `tests/integration_db/test_memory_db.py` | Integration DB | 8 |
| `tests/integration_db/test_product_memory_context.py` | `tests/integration_db/test_memory_db.py` | Integration DB | 11 |
| `tests/integration_db/test_product_memory_extract.py` | `tests/integration_db/test_memory_db.py` | Integration DB | 10 |
| `tests/integration_db/test_product_memory_shortterm.py` | `tests/integration_db/test_memory_db.py` | Integration DB | 10 |
| `tests/integration_db/test_product_graph_memory.py` | `tests/integration_db/test_memory_db.py` | Integration DB | 9 |
| `tests/integration_db/test_frontend_memory_connect.py` | `tests/integration_db/test_memory_db.py` | Integration DB | 7 |
| `tests/integration_db/test_product_user_isolation.py` | `tests/integration_db/test_memory_db.py` | Integration DB | 5 |
| **Tổng Core Memory DB** | `tests/integration_db/test_memory_db.py` | | **60** |
| `tests/integration_db/test_product_memory_cache.py` | `tests/integration_db/test_ttl_cache_db.py` | Integration DB | 47 |
| `tests/integration_db/test_product_router_ttl_cache.py` | `tests/integration_db/test_ttl_cache_db.py` | Integration DB | 9 |
| `tests/integration_db/test_product_ttl_cache_expiration.py` | `tests/integration_db/test_ttl_cache_db.py` | Integration DB | 6 |
| **Tổng TTL Cache DB** | `tests/integration_db/test_ttl_cache_db.py` | | **62** |

### Nhóm Hermetic Capability (Phase 23.5)

| File cũ | File mới sau Phase 23.5 | Loại | Số test |
|---|---|:---:|:---:|
| `tests/hermetic/test_product_ready_sse.py` | `tests/hermetic/test_ready_sse.py` | Hermetic | 7 |
| `tests/hermetic/test_product_guardrails_safety.py` | `tests/hermetic/test_guardrails.py` | Hermetic | 63 |
| `tests/hermetic/test_product_loop_protection.py` | `tests/hermetic/test_loop.py` | Hermetic | 6 |
| `tests/hermetic/test_product_models_fallback.py` | `tests/hermetic/test_models_fallback.py` | Hermetic | 5 |
| `tests/hermetic/test_product_circuit_breaker.py` | `tests/hermetic/test_circuit_breaker.py` | Hermetic | 5 |
| `tests/hermetic/test_product_sandbox_audit.py` | `tests/hermetic/test_sandbox_audit.py` | Hermetic | 7 |
| `tests/hermetic/test_product_eval_gate.py` | `tests/hermetic/test_eval_gate.py` | Hermetic | 5 |
| `tests/hermetic/test_product_eval_batch.py` | `tests/hermetic/test_eval_batch.py` | Hermetic | 5 |
| `tests/hermetic/test_product_ui_navigate.py` | `tests/hermetic/test_ui_navigate.py` | Hermetic | 7 |
| `tests/hermetic/test_v18_access_rbac.py` | `tests/hermetic/test_rbac.py` | Hermetic | 16 |
| `tests/hermetic/test_v16_agent_turn_sse.py` | `tests/hermetic/test_agent_turn_sse.py` | Hermetic | 2 |
| `tests/hermetic/test_trace_payload.py` | `tests/hermetic/test_trace.py` | Hermetic | 5 |
| `tests/hermetic/test_trace_sampling.py` | `tests/hermetic/test_trace.py` | Hermetic | 6 |
| `tests/hermetic/test_infra_llm_gateway.py` | `tests/hermetic/test_llm_gateway.py` | Hermetic | 3 |
| `tests/hermetic/test_product_llm_params.py` | `tests/hermetic/test_llm_gateway.py` | Hermetic | 3 |
| `tests/hermetic/test_v16_hierarchy_skeleton.py` | `tests/hermetic/test_hierarchy.py` | Hermetic | 5 |
| `tests/hermetic/test_v16_analytics_subgraph.py` | `tests/hermetic/test_hierarchy.py` | Hermetic | 1 |
| `tests/hermetic/test_v16_knowledge_subgraph.py` | `tests/hermetic/test_hierarchy.py` | Hermetic | 1 |
| `tests/hermetic/test_inline_respond.py` | `tests/hermetic/test_inline_rewrite.py` | Hermetic | 8 |
| `tests/hermetic/test_rewrite_chart_followup.py` | `tests/hermetic/test_inline_rewrite.py` | Hermetic | 3 |
| `tests/hermetic/test_minio_charts.py` | `tests/hermetic/test_minio_charts.py` (giữ) | Hermetic | 2 |
| `tests/hermetic/test_feedback_to_golden.py` | `tests/hermetic/test_feedback_to_golden.py` (giữ) | Hermetic | 3 |
| `tests/hermetic/test_memory.py` | `tests/hermetic/test_memory.py` (23.3, giữ) | Hermetic | 14 |
| **Tổng Hermetic Suite** | **18 files** | | **182** |

### Nhóm API Gateway, Serving & Phân hệ chức năng (Phase 23.4)

| File cũ | File mới sau Phase 23.4 | Loại | Số test |
|---|---|:---:|:---:|
| `tests/integration_db/test_product_api_gateway.py` | `tests/integration_db/test_api_gateway_db.py` | Integration DB | 61 |
| `tests/integration_db/test_api_hardening.py` | `tests/integration_db/test_api_gateway_db.py` | Integration DB | 4 |
| `tests/integration_db/test_product_deployment_smoke.py` | `tests/integration_db/test_api_gateway_db.py` | Integration DB | 16 |
| `tests/integration_db/test_product_graceful_degradation.py` | `tests/integration_db/test_api_gateway_db.py` | Integration DB | 8 |
| **Tổng API Gateway DB** | `tests/integration_db/test_api_gateway_db.py` | | **89** |
| `tests/integration_db/test_feedback_api.py` | `tests/integration_db/test_feedback_db.py` | Integration DB | 9 |
| **Tổng Feedback DB** | `tests/integration_db/test_feedback_db.py` | | **9** |
| `tests/integration_db/test_product_graph_orchestrator.py` | `tests/integration_db/test_graph_db.py` | Integration DB | 89 |
| **Tổng Graph Orchestrator DB** | `tests/integration_db/test_graph_db.py` | | **89** |
| `tests/integration_db/test_product_sql_agent.py` | `tests/integration_db/test_sql_db.py` | Integration DB | 123 |
| `tests/integration_db/test_sql_batch.py` | `tests/integration_db/test_sql_db.py` | Integration DB | 3 |
| **Tổng SQL DB** | `tests/integration_db/test_sql_db.py` | | **126** |
| `tests/integration_db/test_product_knowledge_rag.py` | `tests/integration_db/test_knowledge_rag_db.py` | Integration DB | 60 |
| `tests/integration_db/test_product_chart_visualization.py` | `tests/integration_db/test_chart_viz_db.py` | Integration DB | 90 |
| `tests/integration_db/test_product_observability_errors.py` | `tests/integration_db/test_observability_db.py` | Integration DB | 45 |
| `tests/integration_db/test_product_compaction_and_tool_compression.py` | `tests/integration_db/test_compaction_db.py` | Integration DB | 8 |
| `tests/integration_db/test_product_llm_prompts.py` | `tests/integration_db/test_llm_prompts_db.py` | Integration DB | 58 |
| `tests/integration_db/test_camera_registry.py` | `tests/integration_db/test_camera_db.py` | Integration DB | 9 |
| **Tổng các phân hệ còn lại DB** | 6 files DB | Integration DB | **270** |
| **Tổng kiểm thử Integration DB (Phase 23.4)** | 10 files mới (cùng 2 file memory = 12 files) | | **583 (toàn bộ suite DB = 705)** |

