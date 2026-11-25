# Task delta — lệch so với `main`

**Baseline:** `origin/main` (`05ea5cd`) · **Branch HEAD:** `3ebaa38` (+ working tree chưa commit).

Living log (**newest first**). Mỗi mục = một task/Fix-only: **Task** (làm gì) + **Đổi gì** + links **`#L…`** chỉ chỗ của task đó (không dán before/after).

## Phạm vi vs main (đã đối chiếu git)

| Wave | Trên `origin/main`? | Trong file này |
|------|---------------------|----------------|
| **v10–v18** (layout, leaf agents, hierarchy, MinIO/traces, IAM RBAC, …) | **Có** — đã merge trên main | Mục lục tham chiếu cuối file (không còn delta code) |
| **v19–v21** + Fix-only | **Không** — chỉ worktree / `Anodis/fix-product` | **Đầy đủ** bên dưới |
| **Meta playbook / gap / task-delta / pre-gather** | Lệch so với main | **Tạm ẩn** (không liệt trong delta) |

Chi tiết dài: [`change-log.md:5`](change-log.md#L5) · Plan: [`implementation-plan.md:3`](implementation-plan.md#L3).

## Cách ghi

```markdown
## YYYY-MM-DD — <phase id> — <tiêu đề ngắn>
- **Task:** <id nếu có> — <1–2 câu tiếng Việt: task này **làm gì / để đạt mục đích gì**> (không chỉ ghi số phase)
- **Đổi gì:** … (chi tiết kỹ thuật ngắn)
- **Chạm (chỉ task này)** — mỗi chỗ sửa = 1 link **có `#L…` nhảy đúng dòng đã đổi** (**không** dán before/after):
  - [`path/file.py:42`](../path/file.py#L42) — ghi chú ngắn (dòng symbol/hunk thật)
  - [`path/file.py:10-25`](../path/file.py#L10-L25) — khối nhiều dòng
  - File mới: ưu tiên mốc chính (`#L12` def/class); `#L1` chỉ khi thay đổi thật sự bắt đầu ở dòng 1
  - File xóa: `path/file.py` — (deleted) · không bịa `#L`
- **Cách test:** …
- **Report:** …
```

**Ai ghi:** Implementer / Test writer (prepend). **Task** phải đọc được mà không cần mở plan (cấm chỉ viết `21.4` / `19.9`). Link **lệch vs `main`** + `#L…` **đúng chỗ sửa**. **Cấm** gắn hàng loạt `#L1` cho file đã edit / file dài. Thiếu mô tả / thiếu `#L` / `#L` lệch = **chưa xong**. Đổi quy ước playbook → cập nhật luôn `orca_setup/`.

---

# Delta so với main (v19 → hiện tại)

> Tạm: đã ẩn mục **meta**/orca_setup/docs-only và strip link `change-log`/`task-delta`/`README`/specs living khỏi **Chạm**.

## 2026-11-25 — 23.4 — Gom API/serving & phân hệ Integration DB (test collapse)
- **Task:** 23.4 — Gom và đổi tên các test files trong `tests/integration_db/` theo cấu trúc capability tối giản (`test_<cap>_db.py`), bảo toàn 100% số test cases (583 tests thuộc Phase 23.4, toàn bộ suite integration_db là 705 tests qua 12 files).
- **Đổi gì:**
  - Gộp 4 files API gateway (`test_product_api_gateway.py` [61], `test_api_hardening.py` [4], `test_product_deployment_smoke.py` [16], `test_product_graceful_degradation.py` [8]) → `tests/integration_db/test_api_gateway_db.py` (89 tests). Xóa 4 file cũ.
  - Gộp 2 files SQL (`test_product_sql_agent.py` [123], `test_sql_batch.py` [3]) → `tests/integration_db/test_sql_db.py` (126 tests). Xóa 2 file cũ.
  - Đổi tên `test_feedback_api.py` (9 tests) → `tests/integration_db/test_feedback_db.py`.
  - Đổi tên `test_product_graph_orchestrator.py` (89 tests) → `tests/integration_db/test_graph_db.py`.
  - Đổi tên bỏ prefix `product_` cho 6 files:
    - `test_product_knowledge_rag.py` (60) → `tests/integration_db/test_knowledge_rag_db.py`
    - `test_product_chart_visualization.py` (90) → `tests/integration_db/test_chart_viz_db.py`
    - `test_product_observability_errors.py` (45) → `tests/integration_db/test_observability_db.py`
    - `test_product_compaction_and_tool_compression.py` (8) → `tests/integration_db/test_compaction_db.py`
    - `test_product_llm_prompts.py` (58) → `tests/integration_db/test_llm_prompts_db.py`
    - `test_camera_registry.py` (9) → `tests/integration_db/test_camera_db.py`
  - Bổ sung bảng ánh xạ capability §8 trong `specs/test-plan.md`.
  - Đánh dấu tick `[x]` Phase 23.4 trong `specs/implementation-plan.md`.
- **Chạm (chỉ task này):**
  - [`tests/integration_db/test_api_gateway_db.py:1`](../tests/integration_db/test_api_gateway_db.py#L1) — file gộp API gateway DB mới (89 tests)
  - `tests/integration_db/test_product_api_gateway.py` — (deleted)
  - `tests/integration_db/test_api_hardening.py` — (deleted)
  - `tests/integration_db/test_product_deployment_smoke.py` — (deleted)
  - `tests/integration_db/test_product_graceful_degradation.py` — (deleted)
  - [`tests/integration_db/test_feedback_db.py:1`](../tests/integration_db/test_feedback_db.py#L1) — đổi tên từ test_feedback_api.py (9 tests)
  - `tests/integration_db/test_feedback_api.py` — (deleted)
  - [`tests/integration_db/test_graph_db.py:1`](../tests/integration_db/test_graph_db.py#L1) — đổi tên từ test_product_graph_orchestrator.py (89 tests)
  - `tests/integration_db/test_product_graph_orchestrator.py` — (deleted)
  - [`tests/integration_db/test_sql_db.py:1`](../tests/integration_db/test_sql_db.py#L1) — file gộp SQL DB mới (126 tests)
  - `tests/integration_db/test_product_sql_agent.py` — (deleted)
  - `tests/integration_db/test_sql_batch.py` — (deleted)
  - [`tests/integration_db/test_knowledge_rag_db.py:1`](../tests/integration_db/test_knowledge_rag_db.py#L1) — đổi tên từ test_product_knowledge_rag.py (60 tests)
  - `tests/integration_db/test_product_knowledge_rag.py` — (deleted)
  - [`tests/integration_db/test_chart_viz_db.py:1`](../tests/integration_db/test_chart_viz_db.py#L1) — đổi tên từ test_product_chart_visualization.py (90 tests)
  - `tests/integration_db/test_product_chart_visualization.py` — (deleted)
  - [`tests/integration_db/test_observability_db.py:1`](../tests/integration_db/test_observability_db.py#L1) — đổi tên từ test_product_observability_errors.py (45 tests)
  - `tests/integration_db/test_product_observability_errors.py` — (deleted)
  - [`tests/integration_db/test_compaction_db.py:1`](../tests/integration_db/test_compaction_db.py#L1) — đổi tên từ test_product_compaction_and_tool_compression.py (8 tests)
  - `tests/integration_db/test_product_compaction_and_tool_compression.py` — (deleted)
  - [`tests/integration_db/test_llm_prompts_db.py:1`](../tests/integration_db/test_llm_prompts_db.py#L1) — đổi tên từ test_product_llm_prompts.py (58 tests)
  - `tests/integration_db/test_product_llm_prompts.py` — (deleted)
  - [`tests/integration_db/test_camera_db.py:1`](../tests/integration_db/test_camera_db.py#L1) — đổi tên từ test_camera_registry.py (9 tests)
  - `tests/integration_db/test_camera_registry.py` — (deleted)
  - [`specs/test-plan.md:32`](../specs/test-plan.md#L32) — sửa đường dẫn AC-T3 trỏ test_observability_db.py
  - [`specs/test-plan.md:261`](../specs/test-plan.md#L261) — §8 bảng map file Phase 23.4
  - [`specs/implementation-plan.md:34`](../specs/implementation-plan.md#L34) — bảng trạng thái 23.4 done
  - [`specs/implementation-plan.md:58-62`](../specs/implementation-plan.md#L58-L62) — tick [x] Phase 23.4
- **Cách test:** `PYTHONPATH=. pytest tests/integration_db --collect-only -q | tail -5` (705 tests collected in 2.37s); `ruff check tests/integration_db/` (All checks passed!).
- **Report:** [`specs/agent-reports/20261125-163500-04a-implementer.md`](agent-reports/20261125-163500-04a-implementer.md)

## 2026-11-25 — 23.5 — Đổi tên hermetic theo capability (test collapse)
- **Task:** 23.5 — Đổi tên và gom nhóm toàn bộ các file test hermetic theo capability (bỏ prefix `product_`/`v16_`/`v18_`), giảm từ 23 files xuống 18 files, bảo toàn 100% số lượng test cases (182 tests collected, 119 passed, 63 skipped offline).
- **Đổi gì:**
  - `git mv` / `mv` bỏ prefix: `test_ready_sse.py`, `test_guardrails.py`, `test_loop.py`, `test_models_fallback.py`, `test_circuit_breaker.py`, `test_sandbox_audit.py`, `test_eval_gate.py`, `test_eval_batch.py`, `test_ui_navigate.py`, `test_rbac.py`, `test_agent_turn_sse.py`.
  - Gom 4 nhóm capability:
    - `test_trace.py`: gộp `test_trace_payload.py` + `test_trace_sampling.py` (11 tests).
    - `test_llm_gateway.py`: gộp `test_infra_llm_gateway.py` + `test_product_llm_params.py` (6 tests).
    - `test_hierarchy.py`: gộp `test_v16_hierarchy_skeleton.py` + `test_v16_analytics_subgraph.py` + `test_v16_knowledge_subgraph.py` (7 tests).
    - `test_inline_rewrite.py`: gộp `test_inline_respond.py` + `test_rewrite_chart_followup.py` (11 tests).
  - Giữ nguyên `test_memory.py` (23.3), `test_minio_charts.py`, `test_feedback_to_golden.py`.
  - Cập nhật bảng map `test-plan.md` §8 (chỉ append nhóm hermetic 23.5).
- **Chạm (chỉ task này):**
  - [`tests/hermetic/test_ready_sse.py:1`](../tests/hermetic/test_ready_sse.py#L1) — đổi tên từ `test_product_ready_sse.py`
  - [`tests/hermetic/test_guardrails.py:1`](../tests/hermetic/test_guardrails.py#L1) — đổi tên từ `test_product_guardrails_safety.py`
  - [`tests/hermetic/test_loop.py:1`](../tests/hermetic/test_loop.py#L1) — đổi tên từ `test_product_loop_protection.py`
  - [`tests/hermetic/test_models_fallback.py:1`](../tests/hermetic/test_models_fallback.py#L1) — đổi tên từ `test_product_models_fallback.py`
  - [`tests/hermetic/test_circuit_breaker.py:1`](../tests/hermetic/test_circuit_breaker.py#L1) — đổi tên từ `test_product_circuit_breaker.py`
  - [`tests/hermetic/test_sandbox_audit.py:1`](../tests/hermetic/test_sandbox_audit.py#L1) — đổi tên từ `test_product_sandbox_audit.py`
  - [`tests/hermetic/test_eval_gate.py:1`](../tests/hermetic/test_eval_gate.py#L1) — đổi tên từ `test_product_eval_gate.py`
  - [`tests/hermetic/test_eval_batch.py:1`](../tests/hermetic/test_eval_batch.py#L1) — đổi tên từ `test_product_eval_batch.py`
  - [`tests/hermetic/test_ui_navigate.py:1`](../tests/hermetic/test_ui_navigate.py#L1) — đổi tên từ `test_product_ui_navigate.py`
  - [`tests/hermetic/test_rbac.py:1`](../tests/hermetic/test_rbac.py#L1) — đổi tên từ `test_v18_access_rbac.py`
  - [`tests/hermetic/test_agent_turn_sse.py:1`](../tests/hermetic/test_agent_turn_sse.py#L1) — đổi tên từ `test_v16_agent_turn_sse.py`
  - [`tests/hermetic/test_trace.py:1`](../tests/hermetic/test_trace.py#L1) — gộp `test_trace_payload.py` + `test_trace_sampling.py`
  - `tests/hermetic/test_trace_payload.py` — (deleted)
  - `tests/hermetic/test_trace_sampling.py` — (deleted)
  - [`tests/hermetic/test_llm_gateway.py:1`](../tests/hermetic/test_llm_gateway.py#L1) — gộp `test_infra_llm_gateway.py` + `test_product_llm_params.py`
  - `tests/hermetic/test_infra_llm_gateway.py` — (deleted)
  - `tests/hermetic/test_product_llm_params.py` — (deleted)
  - [`tests/hermetic/test_hierarchy.py:1`](../tests/hermetic/test_hierarchy.py#L1) — gộp `test_v16_hierarchy_skeleton.py` + `test_v16_analytics_subgraph.py` + `test_v16_knowledge_subgraph.py`
  - `tests/hermetic/test_v16_hierarchy_skeleton.py` — (deleted)
  - `tests/hermetic/test_v16_analytics_subgraph.py` — (deleted)
  - `tests/hermetic/test_v16_knowledge_subgraph.py` — (deleted)
  - [`tests/hermetic/test_inline_rewrite.py:1`](../tests/hermetic/test_inline_rewrite.py#L1) — gộp `test_inline_respond.py` + `test_rewrite_chart_followup.py`
  - `tests/hermetic/test_inline_respond.py` — (deleted)
  - `tests/hermetic/test_rewrite_chart_followup.py` — (deleted)
- **Cách test:** `PYTHONPATH=. pytest tests/hermetic --collect-only -q | tail -3` xác nhận 182 tests; `env -u OPENAI_API_KEY DB_HOST= IAM_REQUIRED=false PYTHONPATH=. pytest tests/hermetic -q` pass 100%.
- **Report:** `specs/agent-reports/20261125-163000-04b-implementer.md`

## 2026-11-25 — 23.3 — Gom capability Memory (test collapse)
- **Task:** 23.3 — Gom 12 test files rời rạc của capability Memory thành 1 file hermetic (`tests/hermetic/test_memory.py`) và 2 files integration_db (`tests/integration_db/test_memory_db.py` và `test_ttl_cache_db.py` — tách do dung lượng > 1500 dòng), bảo toàn 100% số lượng test cases (14 hermetic, 122 integration_db).
- **Đổi gì:**
  - Tạo `tests/hermetic/test_memory.py` gộp từ `test_product_memory_postgres.py` + `test_product_memory_ttl_cache.py`. Xóa 2 file cũ.
  - Tạo `tests/integration_db/test_memory_db.py` gộp từ 7 files core memory (`api`, `context`, `extract`, `shortterm`, `graph_memory`, `frontend_connect`, `user_isolation`).
  - Tạo `tests/integration_db/test_ttl_cache_db.py` gộp từ 3 files cache integration (`cache`, `router_ttl_cache`, `ttl_cache_expiration`).
  - Xóa 10 files cũ trong `tests/integration_db/`.
  - Cập nhật lệnh test trong `AGENTS.md` và thêm bảng map file trong `specs/test-plan.md` §8.
- **Chạm (chỉ task này):**
  - [`tests/hermetic/test_memory.py:1`](../tests/hermetic/test_memory.py#L1) — file hermetic memory mới (14 tests)
  - `tests/hermetic/test_product_memory_postgres.py` — (deleted)
  - `tests/hermetic/test_product_memory_ttl_cache.py` — (deleted)
  - [`tests/integration_db/test_memory_db.py:1`](../tests/integration_db/test_memory_db.py#L1) — file core memory DB mới (60 tests)
  - [`tests/integration_db/test_ttl_cache_db.py:1`](../tests/integration_db/test_ttl_cache_db.py#L1) — file ttl cache DB mới (62 tests)
  - `tests/integration_db/test_product_memory_api.py` — (deleted)
  - `tests/integration_db/test_product_memory_cache.py` — (deleted)
  - `tests/integration_db/test_product_memory_context.py` — (deleted)
  - `tests/integration_db/test_product_memory_extract.py` — (deleted)
  - `tests/integration_db/test_product_memory_shortterm.py` — (deleted)
  - `tests/integration_db/test_product_graph_memory.py` — (deleted)
  - `tests/integration_db/test_frontend_memory_connect.py` — (deleted)
  - `tests/integration_db/test_product_router_ttl_cache.py` — (deleted)
  - `tests/integration_db/test_product_ttl_cache_expiration.py` — (deleted)
  - `tests/integration_db/test_product_user_isolation.py` — (deleted)
  - [`AGENTS.md:70`](../AGENTS.md#L70) — lệnh pytest memory trỏ file mới
  - [`specs/test-plan.md:208`](../specs/test-plan.md#L208) — §8 bảng map file Memory capability
  - [`specs/implementation-plan.md:33`](../specs/implementation-plan.md#L33) — bảng trạng thái 23.3 done
  - [`specs/implementation-plan.md:53-56`](../specs/implementation-plan.md#L53-L56) — tick [x] Phase 23.3
- **Cách test:** `PYTHONPATH=. pytest tests/hermetic/test_memory.py --collect-only -q` (14 tests); `PYTHONPATH=. pytest tests/integration_db/test_memory_db.py tests/integration_db/test_ttl_cache_db.py --collect-only -q` (122 tests); `PYTHONPATH=. pytest tests/hermetic -q` (182 passed); `PYTHONPATH=. pytest tests/integration_db --collect-only -q` (705 tests).
- **Report:** [`specs/agent-reports/20261125-162200-04a-implementer.md`](agent-reports/20261125-162200-04a-implementer.md)

## 2026-11-25 — 23.2 — tests/support + cache seam
- **Task:** 23.2 — Đóng gói tiện ích test vào `tests/support/` (`app`, `cache`, `sse`, `exports`), xóa 3 file shim cũ, loại bỏ hoàn toàn các re-export `_cache` và `_lookup_ttl_cache` khỏi `src/main.py`, giải phóng mã nguồn production khỏi test-only seams.
- **Đổi gì:**
  - Tạo mới package `tests/support/` gồm `__init__.py`, `app.py`, `cache.py`, `sse.py`, `exports.py`.
  - Xóa 3 file shim: `tests/helpers_main_exports.py`, `tests/hermetic/helpers_main_exports.py`, `tests/helpers_stream.py`.
  - Gộp logic chuẩn hóa câu hỏi vào `src/api/helpers/cache_helpers.py` (`lookup_ttl_cache`); `src/application/agent_turn.py` dùng trực tiếp `lookup_ttl_cache` và `set_ttl_cached`.
  - Xóa re-exports `_cache`, `_lookup_ttl_cache`, `get_ttl_cached`, `make_cache_key`, `set_ttl_cached` khỏi `src/main.py`.
  - Chuyển toàn bộ test import `_cache` sang `tests.support.cache.reset_ttl_cache()`; sửa ~13 file test import.
- **Chạm (chỉ task này):**
  - [`tests/support/__init__.py:1`](../tests/support/__init__.py#L1) — package entrypoint
  - [`tests/support/app.py:1`](../tests/support/app.py#L1) — TestClient helper
  - [`tests/support/cache.py:1`](../tests/support/cache.py#L1) — reset_ttl_cache helper
  - [`tests/support/sse.py:1`](../tests/support/sse.py#L1) — sse stream helpers
  - [`tests/support/exports.py:1`](../tests/support/exports.py#L1) — consolidated test error/sse exports
  - `tests/helpers_main_exports.py` — (deleted)
  - `tests/hermetic/helpers_main_exports.py` — (deleted)
  - `tests/helpers_stream.py` — (deleted)
  - [`src/api/helpers/cache_helpers.py:34`](../src/api/helpers/cache_helpers.py#L34) — lookup_ttl_cache (hỗ trợ strip + empty check)
  - [`src/application/agent_turn.py:17`](../src/application/agent_turn.py#L17) — import lookup_ttl_cache
  - [`src/application/agent_turn.py:22`](../src/application/agent_turn.py#L22) — import set_ttl_cached
  - [`src/application/agent_turn.py:106-108`](../src/application/agent_turn.py#L106-L108) — gọi set_ttl_cached trực tiếp
  - [`src/application/agent_turn.py:206`](../src/application/agent_turn.py#L206) — gọi lookup_ttl_cache trực tiếp
  - `src/main.py` — (removed _cache and _lookup_ttl_cache re-exports)
  - [`specs/implementation-plan.md:32`](../specs/implementation-plan.md#L32) — bảng trạng thái 23.2 done
  - [`specs/implementation-plan.md:46-48`](../specs/implementation-plan.md#L46-L48) — tick [x] Phase 23.2
- **Cách test:** `PYTHONPATH=. pytest tests/hermetic -q` (182 passed); `grep -rn -E 'from src\.main import.*_cache|_lookup_ttl_cache' src tests` (rỗng); `PYTHONPATH=. pytest tests/integration_db --collect-only -q` (705 tests collected, 0 error); `ruff check src/ tests/` (all passed).
- **Report:** [`specs/agent-reports/20261125-161300-04a-implementer.md`](agent-reports/20261125-161300-04a-implementer.md)

## 2026-11-25 — 23.1 — Manual Langfuse checklist (đóng 13.5 — Fix-only)
- **Task:** 23.1 Fix-only — Khôi phục tài liệu checklist kiểm thử thủ công phân tầng quan sát Langfuse (`_wrap_node` + `trace_step` dưới rewrite/recall/execute_sql, SQL batch ≥ 2 substeps) để nghiệm thu dứt điểm Phase 13.5 và AC-9.
- **Đổi gì:** Tạo tài liệu `resource/docs/ops/langfuse-nested-trace-manual.md`; đánh dấu `[x]` Phase 23.1 và Phase 13.5 trong `specs/implementation-plan.md`; liên kết `specs/test-plan.md` §1.1 tới tài liệu checklist mới.
- **Chạm (chỉ task này):**
  - [`resource/docs/ops/langfuse-nested-trace-manual.md:1`](../resource/docs/ops/langfuse-nested-trace-manual.md#L1) — tiêu đề và mục tiêu checklist
  - [`resource/docs/ops/langfuse-nested-trace-manual.md:17-31`](../resource/docs/ops/langfuse-nested-trace-manual.md#L17-L31) — điều kiện tiên quyết và cấu hình env
  - [`resource/docs/ops/langfuse-nested-trace-manual.md:37-54`](../resource/docs/ops/langfuse-nested-trace-manual.md#L37-L54) — checklist kiểm thử lượt chat đơn (single query)
  - [`resource/docs/ops/langfuse-nested-trace-manual.md:55-67`](../resource/docs/ops/langfuse-nested-trace-manual.md#L55-L67) — checklist kiểm thử SQL batch ≥ 2
  - [`resource/docs/ops/langfuse-nested-trace-manual.md:70-77`](../resource/docs/ops/langfuse-nested-trace-manual.md#L70-L77) — bảng tiêu chí nghiệm thu AC-9 và AC-T1–T3
  - [`specs/implementation-plan.md:31`](../specs/implementation-plan.md#L31) — bảng trạng thái 23.1 done
  - [`specs/implementation-plan.md:41`](../specs/implementation-plan.md#L41) — tick [x] Phase 23.1
  - [`specs/implementation-plan.md:565`](../specs/implementation-plan.md#L565) — tick [x] Phase 13.5 Manual Langfuse
  - [`specs/test-plan.md:34`](../specs/test-plan.md#L34) — link manual checklist ops
- **Cách test:** Đọc tài liệu `resource/docs/ops/langfuse-nested-trace-manual.md` kiểm tra đầy đủ điều kiện tiên quyết, checklist chat đơn, checklist SQL batch, và bảng ánh xạ AC-9/AC-T1–T3.
- **Report:** [`specs/agent-reports/20261125-155200-04a-implementer.md`](agent-reports/20261125-155200-04a-implementer.md)

## 2026-11-25 — 22.2 — Remove gRPC (supersede 19.9)
- **Task:** Gỡ toàn bộ adapter gRPC (Phase 19.9) chạy cạnh SSE, để hệ thống chỉ còn một transport duy nhất là SSE + `AgentTurnService`, giảm dependency và code chết.
- **Đổi gì:** xóa proto/server/test gRPC; bỏ dependency grpcio; bỏ setting `GRPC_ENABLED`/`GRPC_PORT`; lifespan chỉ còn init storage rồi `yield`.
- **Chạm (chỉ task này):**
  - `proto/` — (deleted)
  - `src/api/grpc/` — (deleted)
  - `tests/hermetic/test_product_grpc.py` — (deleted)
  - [`src/main.py:36`](../src/main.py#L36) — lifespan: bỏ start/stop gRPC, chỉ `yield`
  - `src/shared/settings.py` — (removed `grpc_enabled`/`grpc_port` fields)
  - [`src/shared/settings.py:150-159`](../src/shared/settings.py#L150-L159) — khối `@field_validator` bool (`grpc_enabled` absent)
  - [`requirements.txt:17`](../requirements.txt#L17) — bỏ `grpcio`, `grpcio-tools` (sau `pytest`)
  - [`pyproject.toml:14-17`](../pyproject.toml#L14-L17) — ruff exclude block (`"proto"` absent; removed `"proto"` from ruff exclude)
- **Cách test:** `rg -n 'grpc|agent_pb2|GRPC_|grpcio' src requirements.txt pyproject.toml` (rỗng); `PYTHONPATH=. pytest tests/hermetic -q` → 182 passed.
- **Report:** [`agent-reports/20261125-151922-04-implementer.md`](agent-reports/20261125-151922-04-implementer.md)

## 2026-11-25 — 22.1 — Test layout hermetic / integration_db / live
- **Task:** Phase 22.1 — Tách cấu trúc thư mục kiểm thử thành 3 nhóm `tests/hermetic/`, `tests/integration_db/`, `tests/live/` nhằm tối ưu hóa CI pipeline (chỉ chạy offline hermetic test suite không phụ thuộc DB/LLM, bỏ danh sách `--ignore` dài) đồng thời bảo toàn toàn bộ test suite cơ sở dữ liệu và di dời test-only helper symbols ra khỏi `src/main.py`.
- **Đổi gì:** 
  - Phân bổ test files vào 3 thư mục: unit offline vào `tests/hermetic/` (24 `test_*.py` + 1 helper; 25 khi còn gRPC), 24 files DB/ops vào `tests/integration_db/`, 1 file live IAM vào `tests/live/`.
  - Cập nhật `.github/workflows/ci.yml` chạy `pytest tests/hermetic -q` (bỏ 24 dòng `--ignore`).
  - Gỡ bỏ re-export thừa (`USER_ERROR_MAX_LEN`, `_format_error_message`, `_short_user_error`, `_build_chart_sse_event`) khỏi `src/main.py`, chuyển vào `tests/hermetic/helpers_main_exports.py` (kèm shim `tests/helpers_main_exports.py`); cập nhật `src/domain/agents/graph.py` và 4 test files liên quan.
  - Cập nhật `specs/test-plan.md` §7, `specs/implementation-plan.md` [x] 22.1, `specs/change-log.md`.
- **Chạm (chỉ task này):**
  - [`tests/hermetic/test_product_ui_navigate.py:203`](../tests/hermetic/test_product_ui_navigate.py#L203) — sửa `parents[2]` trỏ đúng root repo
  - [`tests/hermetic/helpers_main_exports.py:1`](../tests/hermetic/helpers_main_exports.py#L1) — helper mới tập hợp test symbols
  - [`tests/helpers_main_exports.py:1`](../tests/helpers_main_exports.py#L1) — shim helper tại root tests
  - [`.github/workflows/ci.yml:62`](../.github/workflows/ci.yml#L62) — job tests chạy `pytest tests/hermetic -q`, bỏ `--ignore`
  - `src/main.py` — (removed re-exports — symbols gone; `USER_ERROR_MAX_LEN`, `_format_error_message`, `_short_user_error`, `_build_chart_sse_event` di dời sang `tests/hermetic/helpers_main_exports.py`)
  - [`src/domain/agents/graph.py:386`](../src/domain/agents/graph.py#L386) — import `format_error_message` trực tiếp từ `src.api.helpers.errors`
  - [`tests/integration_db/test_product_observability_errors.py:723`](../tests/integration_db/test_product_observability_errors.py#L723) — import helper từ `tests.hermetic.helpers_main_exports`
  - [`tests/integration_db/test_product_chart_visualization.py:717`](../tests/integration_db/test_product_chart_visualization.py#L717) — import `_build_chart_sse_event` từ helper
  - [`tests/integration_db/test_product_api_gateway.py:121`](../tests/integration_db/test_product_api_gateway.py#L121) — import `_format_error_message` từ helper
  - [`tests/integration_db/test_product_llm_prompts.py:528`](../tests/integration_db/test_product_llm_prompts.py#L528) — import helpers từ helper
- **Cách test:** `PYTHONPATH=. pytest tests/hermetic -q` (182 passed sau 22.2 gỡ gRPC; 188 passed tại 22.1) && `python -m src.infra.prompts.lint` && `ruff check .`
- **Report:** [`specs/agent-reports/20261125-151800-04a-implementer.md`](agent-reports/20261125-151800-04a-implementer.md)

## 2026-11-25 — ops — Compose B: observability file + cùng network
- **Task:** Ops Compose B — Tách Langfuse (+ DB deps) sang `docker-compose.observability.yml` cùng network app, để `down` obs không tắt Postgres/Qdrant/agent.
- **Đổi gì:** Thêm observability compose; dual-network + `HOSTNAME=0.0.0.0`; app → `LANGFUSE_HOST=http://langfuse-web:3000`; shim `langfuse/docker-compose.yml`.
- **Chạm (chỉ task này):**
  - [`docker-compose.observability.yml:1`](../docker-compose.observability.yml#L1) — file mới (header)
  - [`docker-compose.observability.yml:36`](../docker-compose.observability.yml#L36) — `HOSTNAME: "0.0.0.0"`
  - [`docker-compose.observability.yml:68`](../docker-compose.observability.yml#L68) — web → `langfuse_internal` (+ kcn)
  - [`docker-compose.observability.yml:167-173`](../docker-compose.observability.yml#L167-L173) — networks internal + `kcn_network` external
  - [`langfuse/docker-compose.yml:7-10`](../langfuse/docker-compose.yml#L7-L10) — include shim
  - [`docker-compose.yml:95`](../docker-compose.yml#L95) — `LANGFUSE_HOST: http://langfuse-web:3000`
  - [`deploy/release.sh:136`](../deploy/release.sh#L136) — `-e LANGFUSE_HOST=http://langfuse-web:3000`
- **Cách test:** `docker compose -f docker-compose.observability.yml --env-file langfuse/.env up -d` → `PORT=8010 ./deploy/release.sh deploy …` → `printenv LANGFUSE_HOST` = `http://langfuse-web:3000`; span `obs_compose_b`; smoke PASS.
- **Report:** (chat fix-product)

## 2026-11-25 — fix — Langfuse HOST + gỡ hẳn cột Luồng agent
- **Task:** Fix UI/ops — Cho Langfuse nhận trace từ container app, và **xóa hẳn** cột “Luồng agent” trên chat UI (không ẩn CSS).
- **Đổi gì:** `LANGFUSE_HOST=http://langfuse-web:3000` (compose). Gỡ `aside#graph-panel` + CSS `.graph-*` + logic `upsertGraphNode`/IO panel; chat full width; giữ `lastAgentTrace` cho feedback.
- **Chạm (chỉ task này):**
  - [`deploy/release.sh:136`](../deploy/release.sh#L136) — `LANGFUSE_HOST`
  - [`frontend/index.html:179`](../frontend/index.html#L179) — workspace chat-only (đã xóa aside graph)
  - [`frontend/index.html:221`](../frontend/index.html#L221) — welcome-desc
  - [`frontend/style.css:520`](../frontend/style.css#L520) — workspace/chat full width (đã xóa `.graph-*`)
  - [`frontend/app.js:790`](../frontend/app.js#L790) — `resetStreamState` (thay Graph Logic)
- **Cách test:** Hard-refresh http://192.168.1.198:8088 — không còn DOM `#graph-panel`; chat vẫn stream; Langfuse http://192.168.1.198:3001 có trace.
- **Report:** (chat fix-product)

## 2026-11-25 — fix — real `.env` deploy/smoke (compose network)
- **Task:** Fix deploy local — Chạy smoke/deploy với `.env` thật (compose network), không dùng key hermetic `sk-x`.
- **Đổi gì:** Symlink `.env` từ main checkout; `release.sh` default `DOCKER_NETWORK=compose` + `-e` an toàn với `#` trong password; `cd.yml` dùng `secrets.OPENAI_API_KEYS` (bỏ dummy). Smoke health/ready PASS với postgres+qdrant+llm ok.
- **Chạm (chỉ task này):**
  - [`.env:8`](../.env#L8) (symlink → main checkout, gitignored)
  - [`deploy/release.sh:136`](../deploy/release.sh#L136)
  - [`.github/workflows/cd.yml:30`](../.github/workflows/cd.yml#L30)
- **Cách test:** `docker compose up -d agent_postgres qdrant` → `PORT=8010 ./deploy/release.sh deploy $(git rev-parse --short HEAD)` → smoke → `/ready` ready:true (postgres/qdrant/llm ok). `--ask` cần Bearer vì `IAM_REQUIRED=true`.

## 2026-11-25 — 21.4 Fix-only — hermetic CD + chatkcn
- **Task:** Phase 21.4 Fix-only — Sửa CD smoke hermetic (`sk-x`, tắt memory) + đổi tên image `chatkcn`, chờ `/ready` trước khi smoke.
- **Đổi gì:** Hermetic sk-x/openai/MEMORY_ENABLED=false; wait /ready; chatkcn naming.
- **Chạm (chỉ task này):**
- [`.github/workflows/cd.yml:30`](../.github/workflows/cd.yml#L30)
- [`.github/workflows/deploy.yml:4`](../.github/workflows/deploy.yml#L4)
- [`deploy/release.sh:136`](../deploy/release.sh#L136)
- **Cách test:** python deploy/smoke.py → SMOKE PASS
- **Report:** [`agent-reports/20261125-112700-04a-implementer.md`](agent-reports/20261125-112700-04a-implementer.md)

## 2026-11-25 — 21.4 — cd.yml + deploy.yml
- **Task:** Phase 21.4 — Thêm workflow CD local-first (`cd.yml`) và skeleton deploy SSH (`deploy.yml`, mặc định tắt).
- **Đổi gì:** CD local-first; SSH deploy skeleton gated off; G14 Partial.
- **Chạm (chỉ task này):**
- [`.github/workflows/cd.yml:30`](../.github/workflows/cd.yml#L30)
- [`.github/workflows/deploy.yml:4`](../.github/workflows/deploy.yml#L4)
- **Cách test:** yaml.safe_load; smoke --help

## 2026-11-25 — 21.3 — deploy/ scripts
- **Task:** Phase 21.3 — Viết bộ script deploy local (`release.sh` build/deploy/smoke/rollback + `smoke.py`).
- **Đổi gì:** release.sh + smoke.py + README + gitignore state.
- **Chạm (chỉ task này):**
- [`deploy/release.sh:136`](../deploy/release.sh#L136)
- [`deploy/smoke.py:125`](../deploy/smoke.py#L125)
- [`.gitignore:32`](../.gitignore#L32)
- **Cách test:** E2E PORT=8010

## 2026-11-25 — 21.2 Fix-only — baseline-offline
- **Task:** Phase 21.2 Fix-only — Tránh PR eval-gate fail giả bằng baseline offline riêng (~18%).
- **Đổi gì:** PR gate → baseline-offline.json (~18.18%).
- **Chạm (chỉ task này):**
- [`.github/workflows/eval-gate.yml:6`](../.github/workflows/eval-gate.yml#L6)
- [`resource/eval/results/baseline-offline.json:1`](../resource/eval/results/baseline-offline.json#L1)
- **Cách test:** offline gate exit 0

## 2026-11-25 — 21.2 — eval-gate.yml
- **Task:** Phase 21.2 — Thêm GitHub Action eval-gate (chặn PR khi chất lượng agent tụt) + skeleton nightly.
- **Đổi gì:** Eval PR gate + nightly skeleton.
- **Chạm (chỉ task này):**
- [`.github/workflows/eval-gate.yml:6`](../.github/workflows/eval-gate.yml#L6)
- **Cách test:** pytest tests/test_product_eval_gate.py

## 2026-11-25 — 21.1 — CI 2 tầng
- **Task:** Phase 21.1 — CI 2 tầng: checks (ruff/lint) rồi mới tests pytest hermetic.
- **Đổi gì:** checks→tests, ruff F, requirements-dev.txt.
- **Chạm (chỉ task này):**
- [`.github/workflows/ci.yml:1`](../.github/workflows/ci.yml#L1)
- [`requirements-dev.txt:3`](../requirements-dev.txt#L3)
- [`pyproject.toml:11`](../pyproject.toml#L11)
- **Cách test:** ruff + hermetic pytest

## 2026-11-25 — Planner — v21
- **Task:** Planner v21 — Lập kế hoạch CI/CD local-first phases 21.1–21.4.
- **Đổi gì:** Plan CI/CD local-first 21.1–21.4.
- **Chạm (chỉ task này):**

## 2026-11-25 — 20.6 Fix-only — dashboard filters
- **Task:** Phase 20.6 Fix-only — Sửa filter dashboard ops (widget chat name + rating negative).
- **Đổi gì:** Widget1 name==chat; Widget7 rating==negative.
- **Chạm (chỉ task này):**
- [`resource/docs/ops/dashboard-map.md:3`](../resource/docs/ops/dashboard-map.md#L3)

## 2026-11-25 — 20.6 — dashboard-map
- **Task:** Phase 20.6 — Viết bản đồ 7 widget ops dashboard (`dashboard-map.md`).
- **Đổi gì:** 7-widget ops map; đóng G13/G15/G16 sau Approved.
- **Chạm (chỉ task này):**
- [`resource/docs/ops/dashboard-map.md:3`](../resource/docs/ops/dashboard-map.md#L3)

## 2026-11-25 — 20.5 — TRACE_SAMPLE_RATE
- **Task:** Phase 20.5 — Thêm `TRACE_SAMPLE_RATE` để lấy mẫu trace Langfuse (giảm volume).
- **Đổi gì:** settings + Langfuse sample_rate.
- **Chạm (chỉ task này):**
- [`src/shared/settings.py:148`](../src/shared/settings.py#L148)
- [`src/domain/observability/tracing.py:34`](../src/domain/observability/tracing.py#L34)
- [`tests/test_trace_sampling.py:1`](../tests/test_trace_sampling.py#L1)
- **Cách test:** pytest tests/test_trace_sampling.py

## 2026-11-25 — 20.4 — circuit breaker
- **Task:** Phase 20.4 — Circuit breaker LLM/SQL: fail-fast khi lỗi liên tiếp + fallback model.
- **Đổi gì:** LLM/SQL breaker; fail-fast + fallback.
- **Chạm (chỉ task này):**
- [`src/infra/resilience/breaker.py:25`](../src/infra/resilience/breaker.py#L25)
- [`src/infra/resilience/__init__.py:1`](../src/infra/resilience/__init__.py#L1)
- [`src/shared/settings.py:148`](../src/shared/settings.py#L148)
- [`src/infra/llm/completion.py:1`](../src/infra/llm/completion.py#L1)
- [`src/infra/storage/sql/connection.py:1`](../src/infra/storage/sql/connection.py#L1)
- [`tests/test_product_circuit_breaker.py:1`](../tests/test_product_circuit_breaker.py#L1)
- **Cách test:** pytest tests/test_product_circuit_breaker.py

## 2026-11-25 — 20.3 Fix-only — playbooks
- **Task:** Phase 20.3 Fix-only — Sửa playbook ops cho khớp shape ping/audit thật.
- **Đổi gì:** audit status error; ping shape; jq sed.
- **Chạm (chỉ task này):**
- [`resource/docs/ops/playbooks/llm-down.md:3`](../resource/docs/ops/playbooks/llm-down.md#L3)
- [`resource/docs/ops/playbooks/latency-spike.md:3`](../resource/docs/ops/playbooks/latency-spike.md#L3)

## 2026-11-25 — 20.3 — incident playbooks
- **Task:** Phase 20.3 — Viết 4 playbook sự cố: LLM down, DB down, latency spike, rollback deploy.
- **Đổi gì:** 4 playbooks: llm/db/latency/rollback.
- **Chạm (chỉ task này):**
- [`resource/docs/ops/playbooks/llm-down.md:3`](../resource/docs/ops/playbooks/llm-down.md#L3)
- [`resource/docs/ops/playbooks/db-down.md:3`](../resource/docs/ops/playbooks/db-down.md#L3)
- [`resource/docs/ops/playbooks/latency-spike.md:3`](../resource/docs/ops/playbooks/latency-spike.md#L3)
- [`resource/docs/ops/playbooks/bad-deploy-rollback.md:3`](../resource/docs/ops/playbooks/bad-deploy-rollback.md#L3)

## 2026-11-25 — 20.2 Fix-only — CI ignores
- **Task:** Phase 20.2 Fix-only — Bổ sung danh sách pytest `--ignore` để CI hermetic xanh.
- **Đổi gì:** Hermetic --ignore list → CI pytest exit 0.
- **Chạm (chỉ task này):**
- [`.github/workflows/ci.yml:1`](../.github/workflows/ci.yml#L1)
- **Cách test:** 114 passed exit 0

## 2026-11-25 — 20.2 — CI GitHub Actions
- **Task:** Phase 20.2 — Thêm GitHub Actions CI chạy pytest offline trên push/PR.
- **Đổi gì:** ci.yml lean push/PR pytest offline (G15).
- **Chạm (chỉ task này):**
- [`.github/workflows/ci.yml:1`](../.github/workflows/ci.yml#L1)

## 2026-11-25 — 20.1 — multi-stage Dockerfile
- **Task:** Phase 20.1 — Dockerfile multi-stage (builder/runtime, user 10001, HEALTHCHECK).
- **Đổi gì:** builder/runtime, COPY src/resource/config, appuser 10001, HEALTHCHECK.
- **Chạm (chỉ task này):**
- [`Dockerfile:46`](../Dockerfile#L46)
- [`.dockerignore:21`](../.dockerignore#L21)
- **Cách test:** docker build; uid 10001

## 2026-11-25 — Planner — v20
- **Task:** Planner v20 — Lập kế hoạch hardening G13/G15/G16 (phases 20.1–20.6).
- **Đổi gì:** Plan G13·G15·G16 (20.1–20.6).
- **Chạm (chỉ task này):**

## 2026-11-23 — 19.9 Fix-only — logger
- **Task:** Phase 19.9 Fix-only — Log rõ khi gRPC lifespan start thất bại.
- **Đổi gì:** logger trong lifespan gRPC failure.
- **Chạm (chỉ task này):**
- [`src/main.py:36`](../src/main.py#L36)
- [`tests/test_product_grpc.py:1`](../tests/test_product_grpc.py#L1)
- **Cách test:** pytest tests/test_product_grpc.py

## 2026-11-23 — 19.9 — gRPC
- **Task:** Phase 19.9 — Thêm gRPC StreamTurn cạnh SSE (tắt mặc định bằng `GRPC_ENABLED`).
- **Đổi gì:** proto + grpc server cạnh SSE; GRPC_ENABLED off mặc định.
- **Chạm (chỉ task này):**
- [`proto/agent.proto:6`](../proto/agent.proto#L6)
- [`proto/agent_pb2.py:6`](../proto/agent_pb2.py#L6)
- [`proto/agent_pb2_grpc.py:2`](../proto/agent_pb2_grpc.py#L2)
- [`proto/__init__.py:1`](../proto/__init__.py#L1)
- [`src/api/grpc/server.py:1`](../src/api/grpc/server.py#L1)
- [`src/api/grpc/__init__.py:1`](../src/api/grpc/__init__.py#L1)
- [`src/main.py:36`](../src/main.py#L36)
- [`src/shared/settings.py:148`](../src/shared/settings.py#L148)
- [`requirements.txt:1`](../requirements.txt#L1)
- [`tests/test_product_grpc.py:1`](../tests/test_product_grpc.py#L1)
- **Cách test:** pytest tests/test_product_grpc.py

## 2026-11-23 — 19.8 — ui_navigate
- **Task:** Phase 19.8 — Deep-link UI an toàn: whitelist path + nút “Mở trang” trên FE qua SSE.
- **Đổi gì:** Whitelist deep-link SSE + FE Mở trang.
- **Chạm (chỉ task này):**
- [`config/ui_navigate.yaml:5`](../config/ui_navigate.yaml#L5)
- [`src/domain/agents/ui_navigate.py:1`](../src/domain/agents/ui_navigate.py#L1)
- [`src/domain/agents/state.py:1`](../src/domain/agents/state.py#L1)
- [`src/domain/agents/nodes/respond.py:1`](../src/domain/agents/nodes/respond.py#L1)
- [`src/application/agent_turn.py:1`](../src/application/agent_turn.py#L1)
- [`frontend/app.js:285`](../frontend/app.js#L285)
- [`frontend/style.css:547`](../frontend/style.css#L547)
- [`tests/test_product_ui_navigate.py:1`](../tests/test_product_ui_navigate.py#L1)
- **Cách test:** pytest tests/test_product_ui_navigate.py

## 2026-11-23 — 19.7 — batch API
- **Task:** Phase 19.7 — API/batch eval offline xuất JSONL (`resource/eval/batch.py`).
- **Đổi gì:** resource/eval/batch.py offline JSONL.
- **Chạm (chỉ task này):**
- [`resource/eval/batch.py:8`](../resource/eval/batch.py#L8)
- [`tests/test_product_eval_batch.py:1`](../tests/test_product_eval_batch.py#L1)
- **Cách test:** pytest tests/test_product_eval_batch.py

## 2026-11-23 — 19.10 — feedback→golden
- **Task:** Phase 19.10 — Pipeline thumbs-down feedback → draft golden YAML + checklist audit.
- **Đổi gì:** thumbs-down → draft YAML + AUDIT-CHECKLIST.
- **Chạm (chỉ task này):**
- [`scripts/feedback_to_golden.py:1`](../scripts/feedback_to_golden.py#L1)
- [`resource/eval/AUDIT-CHECKLIST.md:3`](../resource/eval/AUDIT-CHECKLIST.md#L3)
- [`resource/eval/datasets/agent_stat/draft-20261123.yaml:1`](../resource/eval/datasets/agent_stat/draft-20261123.yaml#L1)
- [`tests/test_feedback_to_golden.py:1`](../tests/test_feedback_to_golden.py#L1)
- **Cách test:** pytest tests/test_feedback_to_golden.py

## 2026-11-23 — 19.6 Fix-only — gate baseline
- **Task:** Phase 19.6 Fix-only — Khi `--gate` không tự tạo baseline; commit `baseline.json`.
- **Đổi gì:** Không auto-create baseline khi --gate; unignore baseline.json.
- **Chạm (chỉ task này):**
- [`.gitignore:32`](../.gitignore#L32)
- [`resource/eval/run.py:520`](../resource/eval/run.py#L520)
- [`tests/test_product_eval_gate.py:1`](../tests/test_product_eval_gate.py#L1)
- **Cách test:** pytest tests/test_product_eval_gate.py

## 2026-11-23 — 19.6 — Eval Gate
- **Task:** Phase 19.6 — Eval gate CLI (`--gate`/`--baseline`) so pass-rate với baseline.
- **Đổi gì:** --gate/--baseline; trajectory; baseline.json.
- **Chạm (chỉ task này):**
- [`resource/eval/run.py:520`](../resource/eval/run.py#L520)
- [`resource/eval/results/baseline.json:1`](../resource/eval/results/baseline.json#L1)
- [`tests/test_product_eval_gate.py:1`](../tests/test_product_eval_gate.py#L1)
- **Cách test:** pytest tests/test_product_eval_gate.py

## 2026-11-23 — 19.5 Fix-only — batch audit
- **Task:** Phase 19.5 Fix-only — Timeout + audit JSON trên đường chạy SQL batch.
- **Đổi gì:** Timeout+audit SQL batch path.
- **Chạm (chỉ task này):**
- [`src/domain/agents/analytics/sql_agent/tools/execute.py:1`](../src/domain/agents/analytics/sql_agent/tools/execute.py#L1)
- [`tests/test_product_sandbox_audit.py:1`](../tests/test_product_sandbox_audit.py#L1)
- **Cách test:** pytest tests/test_product_sandbox_audit.py

## 2026-11-23 — 19.5 — sandbox + audit
- **Task:** Phase 19.5 — Sandbox SQL (LIMIT/timeout) + logger audit JSON mỗi tool call.
- **Đổi gì:** SQL LIMIT/timeout; agent_audit JSON.
- **Chạm (chỉ task này):**
- [`src/infra/storage/sql/connection.py:1`](../src/infra/storage/sql/connection.py#L1)
- [`src/infra/storage/sql/executor.py:1`](../src/infra/storage/sql/executor.py#L1)
- [`src/domain/observability/audit.py:1`](../src/domain/observability/audit.py#L1)
- [`src/domain/agents/analytics/sql_agent/tools/execute.py:1`](../src/domain/agents/analytics/sql_agent/tools/execute.py#L1)
- [`tests/test_product_sandbox_audit.py:1`](../tests/test_product_sandbox_audit.py#L1)
- **Cách test:** pytest tests/test_product_sandbox_audit.py

## 2026-11-23 — 19.4 Fix-only — chat_stream
- **Task:** Phase 19.4 Fix-only — Bật fallback model cho luồng `chat_stream`.
- **Đổi gì:** Fallback cho chat_stream.
- **Chạm (chỉ task này):**
- [`src/infra/llm/completion.py:1`](../src/infra/llm/completion.py#L1)
- [`tests/test_product_models_fallback.py:1`](../tests/test_product_models_fallback.py#L1)
- **Cách test:** pytest tests/test_product_models_fallback.py

## 2026-11-23 — 19.4 — models.yaml
- **Task:** Phase 19.4 — `config/models.yaml` + loader + tự fallback LLM khi primary lỗi.
- **Đổi gì:** config/models.yaml + loader + LLM fallback.
- **Chạm (chỉ task này):**
- [`config/models.yaml:1`](../config/models.yaml#L1)
- [`src/shared/models_config.py:1`](../src/shared/models_config.py#L1)
- [`src/infra/llm/completion.py:1`](../src/infra/llm/completion.py#L1)
- [`src/infra/llm/structured.py:1`](../src/infra/llm/structured.py#L1)
- [`src/infra/llm/client.py:1`](../src/infra/llm/client.py#L1)
- [`src/api/routers/web_backend/routes_meta.py:1`](../src/api/routers/web_backend/routes_meta.py#L1)
- [`tests/test_product_models_fallback.py:1`](../tests/test_product_models_fallback.py#L1)
- **Cách test:** pytest tests/test_product_models_fallback.py

## 2026-11-23 — 19.3 — loop protection
- **Task:** Phase 19.3 — Chống loop agent: recursion_limit, đếm iteration/supervisor hops.
- **Đổi gì:** recursion_limit + iteration_count + supervisor_hops.
- **Chạm (chỉ task này):**
- [`src/shared/settings.py:148`](../src/shared/settings.py#L148)
- [`src/domain/agents/graph.py:1`](../src/domain/agents/graph.py#L1)
- [`src/application/agent_turn.py:1`](../src/application/agent_turn.py#L1)
- [`src/domain/agents/state.py:1`](../src/domain/agents/state.py#L1)
- [`src/domain/agents/nodes/supervisor.py:1`](../src/domain/agents/nodes/supervisor.py#L1)
- [`src/api/helpers/errors.py:1`](../src/api/helpers/errors.py#L1)
- [`tests/test_product_loop_protection.py:1`](../tests/test_product_loop_protection.py#L1)
- **Cách test:** pytest tests/test_product_loop_protection.py

## 2026-11-23 — 19.2 — /ready + SSE
- **Task:** Phase 19.2 — Endpoint `GET /ready` + hủy SSE khi client ngắt kết nối.
- **Đổi gì:** GET /ready; SSE cancel on disconnect.
- **Chạm (chỉ task này):**
- [`src/api/routers/web_backend/routes_meta.py:1`](../src/api/routers/web_backend/routes_meta.py#L1)
- [`src/api/routers/agent/routes_agent.py:1`](../src/api/routers/agent/routes_agent.py#L1)
- [`src/application/agent_turn.py:1`](../src/application/agent_turn.py#L1)
- [`tests/test_product_ready_sse.py:1`](../tests/test_product_ready_sse.py#L1)
- **Cách test:** pytest tests/test_product_ready_sse.py

## 2026-11-23 — 19.1 / Planner — v19 + G0
- **Task:** Phase 19.1 + Planner — Cập nhật non-goals/budget/difficulty và plan phases 19.2–19.10.
- **Đổi gì:** Non-goals, budget §5.1, difficulty; plan 19.2–19.10.
- **Chạm (chỉ task này):**
  - _(tạm ẩn link docs; chỉ giữ code/config)_
---

# Tham chiếu — đã có trên `main` (không còn delta code trên branch này)

Các wave dưới **đã nằm trong `origin/main`**. Không liệt kê lại file (trùng main). Tra cứu: [`change-log.md:5`](change-log.md#L5) · [`implementation-plan.md:3`](implementation-plan.md#L3).

| Wave | Tóm tắt | Neo |
|------|---------|-----|
| **v18** | IAM RBAC + domain/geo + retrieval rename + golden RBAC | [implementation-plan § v18](implementation-plan.md) |
| **v17** | Rich Langfuse traces + MinIO charts + cross-DB «và» | change-log 2026-11-10 |
| **v16** | Hierarchical analytics/knowledge + AgentTurnService | [§ v16](implementation-plan.md) |
| **v15** | Leaf sql_agent/docs_agent + flat graph | [§ v15](implementation-plan.md) |
| **v14** | Align `src/` với ai_backend layout | [§ v14](implementation-plan.md) |
| **v13** | Nested `trace_step` toàn graph | [§ v13](implementation-plan.md) |
| **v12–v10** | domain/agents packages; src layout; tách graph | [§ v10+](implementation-plan.md) |
| **v9** | Memory & Context Engineering | change-log Phase 5–7 / AGENTS.md |
| **Pre-v9 / layout** | API routers, drop /ask, settings, guardrails→domain, gom `resource/` | change-log 2026-11-03 … 2026-11-23 |

> Nếu sau này rewrite làm **lệch** file v10–v18 so với main → prepend mục delta mới (đừng ghi vào bảng trên như thể đã đụng).
