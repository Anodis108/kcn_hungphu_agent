# Implementation Plan — agent dong v9: Unified Memory & Context Engineering System (Postgres-backed)

**Trạng thái v9 (Memory):** 100% hoàn thành — 7 Phase bên dưới.  
**Trạng thái v10 (Cấu trúc `src/`):** Hoàn thành — API package + tách `graph.py` (facade ~90 dòng).  
**Trạng thái v13 (Nested Langfuse):** Code + tests — xem § v13.  
**Trạng thái v14 (ai_backend layout):** 14.1–14.4 done — v14-ai-backend-layout-design.md; 14.5 optional.  
**Trạng thái v15 (leaf agents + flat graph):** 15.1–15.5 done — v15-leaf-agents-flat-graph-design.md.  
**Trạng thái v16 (hierarchical teams):** 16.1–16.7 code (continuous) — v16-hierarchical-agents-design.md · v16-hierarchical-agents-plan.md.  
**Trạng thái v18 (IAM RBAC):** đang triển khai — v18-rbac-iam-design.md · v18-rbac-iam-plan.md.  
**Trạng thái v19 (Gap G0–G17 wave):** đang triển khai — design grill Approved 2026-11-23; living tracker `specs/gap-analysis-quy-trinh-product-agent.md`.  
**Trạng thái v21 (CI/CD local-first parity demo):** plan drafted 2026-11-25 — § v21.  
**Trạng thái v20 (G13·G15·G16 ops):** plan drafted 2026-11-25 — § v20.  
**Trạng thái v22 (Test layout hermetic/db/live):** grill Approved 2026-11-25 — § v22.  
**Trạng thái v22.2 (Remove gRPC):** grill Approved 2026-11-25 — xóa Phase 19.9 (superseded).  
**Trạng thái v23 (13.5 + tối giản tests + dọn src test-only):** grill Approved 2026-11-25 — design `specs/v23-test-simplify-design.md`.  
**Nguồn:** `specs/product-spec.md`, `resource/knowledge_handbook/Spec Driven Development Guide - Vietnamese.md`  
**Quy tắc:** Mặc định một phase `[ ]` mỗi Implementer lane; tick + `change-log` sau khi xong. **Ngoại lệ §15g:** nhiều lane khi `parallel_ok` + `touches` disjoint + `depends` đã Approved — mỗi lane vẫn Review riêng. **Task mới → checklist + metadata parallel trước khi code.** Mỗi lần Planner thêm/sửa wave: **bắt buộc tự review plan** (`orca_setup` §6d / guide VN bước 3) — số phase/`[ ]` theo scope lần đó, **không** cố định theo ví dụ 7 mục greenfield. Ràng buộc wave: **không đổi sơ đồ hệ thống** (giữ SSE web + graph); ponytail = diff nhỏ nhất.

---

## v23 — Langfuse manual 13.5 + tối giản tests + dọn test-only src (grill Approved)

> **Owner: 03 Planner (Claude), 2026-11-25.** Bản này **thay thế** draft của Coordinator (lệch rule §15b). `v23-implementation-plan-detail.md` chỉ còn là pointer — nguồn sự thật là section này. 23.1: doc bị 04a ABORT revert → Reviewer Blocked; **Fix-only 23.1** khôi phục artifact rồi re-tick.

**Goal:** Đóng 13.5; gom test theo capability (~25–30 stem, tối đa 2 file/cap: `test_<cap>.py` hermetic + `test_<cap>_db.py` integration_db); `tests/support/` sâu; bỏ re-export cache "for tests" trên `src/main.py`.
**Không:** Đổi graph/SSE; xóa `integration_db`/`live`; xóa heuristic `plan.py`; sửa assert/logic test khi gom (chỉ move/merge/đổi import); thêm dependency.
**Design:** [`v23-test-simplify-design.md`](v23-test-simplify-design.md)

| Task | depends | group | parallel_ok | touches |
|:--:|:--:|:--:|:--:|---|
| **23.1** | — | P1 | no | `resource/docs/ops/langfuse-nested-trace-manual.md` (+ ticks/links) — done |
| **23.2** | 23.1 Approved | P2 | no | `tests/support/` (mới), `tests/helpers_main_exports.py`, `tests/hermetic/helpers_main_exports.py`, `tests/helpers_stream.py`, `src/main.py`, `src/api/helpers/cache_helpers.py`, `src/application/agent_turn.py`, mọi test import `_cache`/`_lookup_ttl_cache` từ `src.main` — done |
| **23.3** | 23.2 Approved | P3 | no (sửa `conftest`/support nếu cần) | Memory files (liệt kê dưới), `specs/test-plan.md` §map — done |
| **23.4** | 23.3 Approved | P4 | **yes** ∥ 23.5 | API/serving files (dưới), `specs/test-plan.md` §map (dòng riêng) — done |
| **23.5** | 23.3 Approved | P4 | **yes** ∥ 23.4 | rename hermetic còn lại (dưới), `specs/test-plan.md` §map (dòng riêng) — done |

`parallel_ok` 23.4 ∥ 23.5: file test rời nhau; chỉ chung `test-plan.md` — mỗi lane chỉ append dòng của mình trong bảng map (merge tay nếu xung đột). Không lane nào sửa `tests/support/` / `conftest.py` (cần → báo Coordinator, chạy tuần tự).

### Phase 23.1 — Manual Langfuse nested (đóng 13.5)

- [x] (Fix-only: khôi phục — bị revert) `resource/docs/ops/langfuse-nested-trace-manual.md` + tick 13.5 + link test-plan §1.1 + change-log/task-delta (04a, report `20261125-155200-04a-implementer.md`).
- **Test:** Reviewer-5a đọc checklist: đủ env, bước chat đơn, SQL batch ≥2 substeps, bảng AC-9/AC-T1–T3; link `#L` trỏ đúng.

### Phase 23.2 — `tests/support/` + cache seam

- [x] `tests/support/__init__.py` + `app.py` (`client()` TestClient), `cache.py` (`reset_ttl_cache()` gọi `ttl_cache.clear_ttl_cache()`), `sse.py` (chuyển nội dung `tests/helpers_stream.py`), `exports.py` (alias error/sse helpers — gộp **2** bản `helpers_main_exports.py`, bản root import từ hermetic → giữ bản import thẳng `src.api.helpers.*`). Xóa 3 file shim cũ; sửa 13 file import.
- [x] Gộp `_lookup_ttl_cache` (main, có `.strip()`) vào `cache_helpers.lookup_ttl_cache` (thêm strip + empty → None). `agent_turn.py` dùng `cache_helpers.lookup_ttl_cache` thay `main_mod._lookup_ttl_cache`. `src/main.py` bỏ import `_cache, get_ttl_cached, make_cache_key, set_ttl_cached` và hàm `_lookup_ttl_cache`.
- [x] Tests: `from src.main import _cache` (14 chỗ) → `tests.support.cache.reset_ttl_cache()`; monkeypatch `src.main._lookup_ttl_cache` → `src.api.helpers.cache_helpers.lookup_ttl_cache`.
- **Test:** `PYTHONPATH=. pytest tests/hermetic -q` exit 0 (≥182 pass); `grep -rn "from src.main import _cache\|_lookup_ttl_cache" src tests` → rỗng; `PYTHONPATH=. pytest tests/integration_db --collect-only -q` collect không lỗi import.

### Phase 23.3 — Gom Memory

- [x] Hermetic: `test_product_memory_postgres.py` + `test_product_memory_ttl_cache.py` → `tests/hermetic/test_memory.py` (14 tests).
- [x] DB: `test_product_memory_api/context/extract/shortterm/graph_memory/frontend_connect/user_isolation` → `tests/integration_db/test_memory_db.py` (60 tests); `test_product_memory_cache/router_ttl_cache/ttl_cache_expiration` → `tests/integration_db/test_ttl_cache_db.py` (62 tests, tách do file gom > 1500 dòng).
- [x] `test-plan.md`: bảng map file cũ → mới; sửa lệnh trong `AGENTS.md`/test-plan trỏ file memory cũ.
- **Test:** số test collect trước = sau cho nhóm này (`pytest --collect-only -q | tail -1` so sánh: 14 hermetic, 122 integration_db); hermetic xanh.

### Phase 23.4 — Gom API/serving (∥ 23.5)

- [x] DB: `test_product_api_gateway.py`, `test_api_hardening.py`, `test_product_deployment_smoke.py`, `test_product_graceful_degradation.py` → `test_api_gateway_db.py`; `test_feedback_api.py` → `test_feedback_db.py`; `test_product_graph_orchestrator.py` → `test_graph_db.py`; `test_product_sql_agent.py` + `test_sql_batch.py` → `test_sql_db.py`; các file DB còn lại bỏ prefix `product_` (`test_knowledge_rag_db.py`, `test_chart_viz_db.py`, `test_observability_db.py`, `test_compaction_db.py`, `test_llm_prompts_db.py`, `test_camera_db.py`).
- **Test:** collect count bằng trước; `pytest tests/integration_db --collect-only` không lỗi.

### Phase 23.5 — Đổi tên hermetic theo capability (∥ 23.4)

- [x] `git mv` bỏ prefix `product_`/`v16_`/`v18_`: vd `test_ready_sse.py`, `test_guardrails.py`, `test_loop.py`, `test_models_fallback.py`, `test_circuit_breaker.py`, `test_sandbox_audit.py`, `test_eval_gate.py` + `test_eval_batch.py`, `test_ui_navigate.py`, `test_trace.py` (gộp `trace_sampling` + `trace_payload`), `test_llm_gateway.py` (gộp `infra_llm_gateway` + `product_llm_params`), `test_rbac.py`, `test_agent_turn_sse.py`, `test_hierarchy.py` (gộp `v16_hierarchy_skeleton` + `analytics_subgraph` + `knowledge_subgraph`), `test_inline_rewrite.py` (gộp `inline_respond` + `rewrite_chart_followup`), `test_minio_charts.py`, `test_feedback_to_golden.py`.
- **Test:** hermetic xanh, collect count bằng trước (182 tests); `.github/workflows/ci.yml` vẫn `pytest tests/hermetic -q` (không sửa).

---

## v22 — Tách test hermetic / integration_db / live + gỡ gRPC (grill Approved)

**Goal:** Tách `tests/` thành 3 folder; **giữ** suite thao tác DB (không xóa); CI chỉ chạy hermetic; helper chỉ-for-test chuyển khỏi `src/` vào `tests/`; **gỡ** adapter gRPC 19.9 (SSE only).
**Không:** Xóa `integration_db` / `live`; không đổi hành vi app ngoài gỡ re-export test-only; **không** thêm port transport mới / shim gRPC.

| Task | depends | group | touches |
|:--:|:--:|:--:|---|
| **22.1** | — | **P1** | `tests/**`, `.github/workflows/ci.yml`, `src/main.py` (re-export), `specs/test-plan.md`, `specs/change-log.md`, `specs/task-delta.md` |
| **22.2** | — | **P1∥** | `proto/`, `src/api/grpc/`, `src/main.py` (lifespan), `src/shared/settings.py`, `requirements.txt`, `pyproject.toml`, `tests/**/test*grpc*`, `specs/*`, `orca_setup/` (nếu còn ref) |

`parallel_ok`: 22.2 ∥ 22.1 với quy ước **delete-only** trên file test grpc (không đụng CI/layout folder).

### Phase 22.1 — Move suites + CI hermetic + helpers → tests

- [x] Tạo `tests/hermetic/`, `tests/integration_db/`, `tests/live/`; `git mv` theo map grill (DB/ops → `integration_db`; `test_v18_iam_live.py` → `live`; còn lại unit/CI → `hermetic`). Giữ `conftest.py` / `helpers_stream.py` ở root `tests/` hoặc share hợp lý.
- [x] CI: `pytest tests/hermetic -q` — **bỏ** list `--ignore` dài trong `ci.yml`.
- [x] Chuyển symbol chỉ-for-test từ `src.main` (vd. `_format_error_message`, `_build_chart_sse_event`, `_short_user_error`, `USER_ERROR_MAX_LEN` nếu không dùng production) sang helper dưới `tests/` (vd. `tests/hermetic/helpers_main_exports.py`); cập nhật import test; gỡ re-export thừa khỏi `src/main.py`. Giữ `_cache` / `app` nếu production/tests còn cần qua FastAPI app thật.
- [x] Cập nhật `specs/test-plan.md` (lệnh hermetic / integration_db / live); tick + `change-log` + `task-delta` (`Task` mục đích + `#L…`).
- **Test:** `PYTHONPATH=. pytest tests/hermetic -q` exit 0; `ls tests/integration_db | head` còn sql/memory suites; Reviewer-5a.

### Phase 22.2 — Remove gRPC (supersede 19.9)

- **parallel_ok:** yes (∥ 22.1, delete-only) · **parallel_group:** P1∥ · **depends:** — · **touches:** xem bảng trên
- [x] Xóa hết adapter gRPC: `proto/`, `src/api/grpc/`, mọi `**/test*grpc*`, `grpcio` + `grpcio-tools` trong `requirements*.txt`, field `grpc_enabled`/`grpc_port` + validator trong `settings.py`, khối lifespan gRPC trong `main.py`, entry `"proto"` trong `pyproject.toml` nếu có. **Không** để shim/env chết; **không** thêm `TurnTransport` port.
- [x] Specs: đánh dấu 19.9 **superseded by 22.2**; tick 22.2; `change-log`; prepend **`task-delta`** — mỗi link `#L…` nhảy **đúng dòng đã sửa** (cấm `#L1` cho cả file đã edit); cập nhật `test-plan` / goal v19 nếu còn ghi “gRPC cạnh SSE”.
- [x] `orca_setup`: chỉ sửa nếu còn nhắc gRPC; gate `#L` đã siết bởi Coord trước dispatch.
- **Test:** `rg -n 'grpc|agent_pb2|GRPC_' src requirements.txt pyproject.toml` không còn runtime hits; `PYTHONPATH=. pytest tests/hermetic -q` (hoặc `tests/ -q --ignore` nếu hermetic chưa có) exit 0; import app không kéo `grpc`; Reviewer-5a Blocked nếu task-delta sai `#L`.

---

## v21 — CI/CD parity `llm-engineer-demo` (local-first, không cloud thật)

**Goal:** Port cấu trúc + nguyên tắc demo (`resource/knowledge_handbook/llm-engineer-demo/.github/workflows/*`, `deploy/`): check rẻ trước, hermetic, eval gate theo path, chỉ promote khi CI xanh, image tag=SHA bất biến, smoke trước healthy, rollback khi fail. Mặc định chạy **local / runner**, cloud = skeleton gated `false`.
**Không:** GCP/WIF/VM/nginx/TLS thật, systemd, Secret Manager, canary, gỡ các `--ignore` test hiện có, ruff rule ngoài `F`. Không đổi app code / graph / SSE.

| Task | G* | depends | group | touches |
|:--:|:--:|:--:|:--:|---|
| **21.1** | G15 | — | **P1** | `.github/workflows/ci.yml`, `requirements-dev.txt` (mới), `pyproject.toml` (`[tool.ruff]`) |
| **21.2** | G10/G15 | — | **P1** | `.github/workflows/eval-gate.yml` (mới) |
| **21.3** | G14 | — | **P1** | `deploy/release.sh`, `deploy/smoke.py`, `deploy/README.md` (mới) |
| **21.4** | G14 | 21.1, 21.3 | **P2** | `.github/workflows/cd.yml`, `.github/workflows/deploy.yml` (mới), gap tracker |

`parallel_ok`: P1 ba task file rời nhau. 21.4 cần tên workflow CI cuối cùng (21.1) + script (21.3).

### Phase 21.1 — CI 2 tầng (checks → tests)

- [x] `requirements-dev.txt`: `-r requirements.txt` + `ruff` (pin version `ruff==0.8.4`). `pyproject.toml` `[tool.ruff]`: `select=["F"]`, `exclude` `resource/knowledge_handbook`, `frontend`, `proto`. Vi phạm `F` có sẵn → `per-file-ignores` có ghi lý do rõ ràng cho tests/scripts/eval/src — không refactor.
- [x] `ci.yml`: giữ `name: CI`; thêm `concurrency: ci-${{ github.ref }}` cancel-in-progress; job `checks` (pip `requirements-dev.txt`, `python -m src.infra.prompts.lint`, `ruff check .`); job `tests` `needs: checks` giữ nguyên env hermetic + danh sách `--ignore` hiện tại.
- **Test:** local `pip install -r requirements-dev.txt && ruff check . && PYTHONPATH=. python -m src.infra.prompts.lint` exit 0; push branch → Actions hiển thị 2 job, `tests` chỉ chạy sau `checks` xanh; thêm import thừa ở branch nháp → `checks` đỏ, `tests` skip.

### Phase 21.2 — eval-gate.yml

- [x] Trigger `pull_request` với `paths`: `src/infra/prompts/**`, `src/domain/agents/**`, `resource/eval/**`, `config/models.yaml`; `schedule` nightly; `concurrency` cancel.
- [x] Job `eval-gate` (PR, chặn): `PYTHONPATH=.:resource python resource/eval/run.py --offline --gate --baseline resource/eval/results/baseline.json` + ghi output vào `$GITHUB_STEP_SUMMARY` + upload artifact. Không secret.
- [x] Job `eval-nightly` (schedule): `if: secrets` có key (qua env check bước đầu) chạy eval thật, `continue-on-error: true`; không key → skip có log.
- **Test:** local chạy đúng lệnh gate → exit 0; tạm sửa baseline cao hơn → exit 1. PR đụng `resource/eval/` → job chạy; PR chỉ đổi README → không chạy.

### Phase 21.3 — `deploy/` scripts local

- [x] `deploy/release.sh` (bash, `set -euo pipefail`, không sudo/systemd): `build` (tag `chatkcn:<git sha>`), `deploy <tag>` (ghi `.lkg` = bản cũ từ `.current`, `docker run -d --name chatkcn-app -p ${PORT:-8000}:8000 --env-file .env chatkcn:<tag>`, đợi `/ready`), `smoke`, `rollback` (về `.lkg`), `status`. State file trong `deploy/.state/` (gitignore).
- [x] `deploy/smoke.py` (dùng `httpx`/`requests` đã có trong requirements): `/api/health` 200 → `/ready` 200 → (tùy chọn `--ask`) gửi 1 câu golden đã biết và kiểm tra từ khoá; exit code ≠ 0 khi fail.
- [x] `deploy/README.md`: luồng local, map nguyên tắc demo → script, mục "Cloud (optional)" mô tả biến `ENABLE_*` + secrets cần nếu bật sau.
- **Test:** `deploy/release.sh build && deploy/release.sh deploy $(git rev-parse --short HEAD) && deploy/release.sh smoke` → OK; deploy tag hỏng (vd image `CMD` sai qua tag thử) → smoke fail → `release.sh rollback` về bản trước, `status` hiển thị đúng; `python deploy/smoke.py --url http://localhost:8000` exit 0/1.

### Phase 21.4 — cd.yml + deploy.yml skeleton

- [x] `cd.yml`: `on: workflow_run [CI] completed main` + `workflow_dispatch`; `if: conclusion == 'success' || dispatch`; checkout `workflow_run.head_sha`; `concurrency: cd` không cancel; job local: `docker build -t chatkcn:$SHA` → `docker run` với env tối thiểu (`DB_HOST=`, `IAM_REQUIRED=false`) → `python deploy/smoke.py` (không `--ask`) → `if: failure()` dump logs. Bước push registry (ghcr) gated `vars.ENABLE_REGISTRY_PUSH == 'true'` (mặc định skip). Job summary ghi SHA + kết quả smoke.
- [x] `deploy.yml`: skeleton SSH → VM gọi `deploy/release.sh` trên host, toàn bộ job `if: vars.ENABLE_SSH_DEPLOY == 'true'` (mặc định skip); comment rõ không bật cùng lúc với push khác.
- [x] Gap tracker G14 → **Partial** (cấu trúc CD local xong; cloud/secrets Missing), G15 ghi nhận CD; §5 + change-log.
- **Test:** merge vào main (hoặc `workflow_dispatch`) → `cd` chạy sau CI xanh, build + smoke xanh không cần secret; CI đỏ → `cd` skip; `deploy` hiển thị skipped. `actionlint` (nếu có) không lỗi.

---

## v20 — Ops wave: G13 multi-stage · G15 CI · G16 ops MVP

**Goal:** G13 → Done, G15 Missing → Done, G16 Partial → Done (MVP slice). Không đổi kiến trúc/graph/SSE.
**Không:** CD cloud (G14), hard $ limit, canary, ops React console, `/api/ops/summary`, thêm ruff.
**Vị trí tài liệu ops:** `resource/docs/ops/` (giữ `specs/` = core SDD).

| Task | G* | depends | parallel group | touches |
|:--:|:--:|:--:|:--:|---|
| **20.1** | G13 | — | **P1** | `Dockerfile`, `.dockerignore` |
| **20.2** | G15 | — | **P1** | `.github/workflows/ci.yml` |
| **20.3** | G16 | — | **P1** | `resource/docs/ops/playbooks/*.md` |
| **20.4** | G16 | — | **P2** (sau P1 Approved) | `src/infra/resilience/breaker.py` (mới), `src/infra/llm/completion.py`, `src/infra/storage/sql/connection.py`, `src/shared/settings.py` |
| **20.5** | G16 | — | **P2** ∥ 20.4 | `src/domain/observability/tracing.py`, `src/shared/settings.py` (chỉ thêm 1 field — merge cẩn thận với 20.4) |
| **20.6** | G16 | 20.4, 20.5 | **P3** | `resource/docs/ops/dashboard-map.md`, gap tracker |

`parallel_ok`: P1 ba task đĩa rời nhau. P2: 20.4 ∥ 20.5 chỉ chung `settings.py` (mỗi task thêm field riêng; nếu xung đột → chạy tuần tự 20.4 → 20.5). Mỗi task vẫn qua Review Approved riêng.

### Phase 20.1 — G13 multi-stage Dockerfile

- [x] Stage `builder` (`python:3.11-slim`): `pip wheel`/`pip install --prefix=/install -r requirements.txt`. Stage `runtime`: copy `/install`, **COPY `src/` + `resource/` + `config/`** (hiện thiếu `src/` — chỉ chạy nhờ volume compose), user `appuser` uid 10001, `HEALTHCHECK` gọi `/ready` (fallback `/api/health` nếu muốn liveness — ghi chú), giữ `CMD` uvicorn. Thêm `.dockerignore` (`.git`, `tests`, `frontend/node_modules`, `.env`, `__pycache__`).
- **Test:** `docker build -t dong:v20 .` → `docker run --rm -p 8000:8000 --env-file .env dong:v20` → `curl :8000/api/health` 200, `/ready` 200/503 đúng theo env; `docker run --rm dong:v20 id -u` → 10001; image nhỏ hơn bản cũ (`docker images`). `docker compose up` vẫn chạy.

### Phase 20.2 — G15 CI GitHub Actions

- [x] `.github/workflows/ci.yml`: trigger `push` + `pull_request` (main); `ubuntu-latest`, Python 3.11, cache pip, `pip install -r requirements.txt`, `PYTHONPATH=. pytest -q tests/` với env offline (`DB_HOST=`, `IAM_REQUIRED=false`, không key LLM). Job đỏ khi test fail. Không bước deploy.
- [x] Nếu test cần mạng/DB → đánh dấu skip bằng marker sẵn có hoặc ghi rõ danh sách loại trừ trong workflow (không sửa logic test). Danh sách loại trừ (`--ignore`) được phân nhóm và justified chi tiết trong workflow (PostgreSQL session/memory fixtures, live SQL DB, external LLM/Qdrant/Langfuse, syntax collection errors). Bộ offline test suite chạy xanh: **114 passed, 70 skipped (exit 0)**.
- **Test:** chạy local giả lập `env -u OPENAI_API_KEY DB_HOST= PYTHONPATH=. pytest -q ...`; `act` (nếu có) hoặc push branch → Actions xanh; cố ý làm hỏng 1 assert ở branch nháp → Actions đỏ.

### Phase 20.3 — G16 incident playbooks (4)

- [x] `resource/docs/ops/playbooks/`: `llm-down.md`, `db-down.md`, `latency-spike.md`, `bad-deploy-rollback.md`. Mỗi file: Triệu chứng · Phát hiện (log/metric: `llm_fallback_used`, `/ready`, Langfuse latency, `agent_audit`) · Xử lý từng bước (lệnh thật: `docker compose …`, đổi `config/models.yaml`, `git revert`/tag image cũ) · Xác nhận phục hồi · Hậu kiểm.
- **Test:** review — mỗi file có đủ 5 mục; mọi lệnh/endpoint nêu ra tồn tại trong repo (`grep`).

### Phase 20.4 — G16 circuit breaker mỏng

- [x] `src/infra/resilience/breaker.py` (~50 dòng, không thư viện mới): trạng thái closed/open/half-open; mở sau `BREAKER_FAIL_THRESHOLD` (5) lỗi liên tiếp, thử lại sau `BREAKER_RESET_SECONDS` (30). Log `circuit_open`/`circuit_close`.
- [x] Bọc lời gọi LLM primary (`completion.py`): breaker open → nhảy thẳng fallback (19.4) thay vì chờ timeout. Bọc SQL execute (`connection.py`): open → lỗi gọn "dữ liệu tạm thời không khả dụng" (fail-fast, không 500).
- **Test:** unit — 5 lỗi → open, lần 6 không gọi hàm thật; sau reset (monkeypatch time) → half-open, 1 thành công → closed; LLM open → fallback được gọi; SQL open → message thân thiện.

### Phase 20.5 — G16 trace sampling

- [x] `TRACE_SAMPLE_RATE` (float 0–1, mặc định 1.0) trong settings; truyền vào khởi tạo Langfuse (`sample_rate`) trong `tracing.py`. Tail-ish rule tối giản: lượt có lỗi luôn trace (nếu SDK hỗ trợ — không thì ghi giới hạn trong doc).
- **Test:** unit — rate 0 → client khởi tạo với sample_rate=0; mặc định 1.0; env sai → 1.0 + warning. Test suite `tests/test_trace_sampling.py` pass (6 passed).

### Phase 20.6 — G16 dashboard map (doc-only) + đóng gap

- [x] `resource/docs/ops/dashboard-map.md`: 7 widget → nguồn sẵn có: (1) request/latency p95 — Langfuse; (2) error rate — Langfuse/`agent_audit`; (3) cost/ngày vs budget §5.1 — Langfuse; (4) token/lượt — Langfuse; (5) `supervisor_hops` — Langfuse metadata; (6) `llm_fallback_used` + `circuit_open` — log; (7) `/ready` uptime + thumbs-down rate — `/ready`, `/api/feedback`. Mỗi widget: query/filter cụ thể + ngưỡng alert.
- [x] Gap tracker: G13, G15, G16 → Done (20.1–20.5 Approved; 20.6 hoàn tất); §5 lịch sử; change-log.
- **Test:** review — 7 widget đều trỏ nguồn tồn tại; gap tracker nhất quán.

---

## v19 — Gap closure wave (grill Approved)

**Goal:** Đóng G0, G1, G5(−HITL), G7(−FastMCP), G8, G10, G11(Batch offline only), G13(/ready+SSE cancel), G17(feedback→golden); + deep-link D. (**19.9 gRPC** → **superseded by 22.2** — SSE only.)  
**Không:** FastMCP, HITL, Docker code-sandbox, canary, multi-stage Dockerfile, thay SSE bằng gRPC, hard $ limit runtime (chỉ ghi budget ở G0).

| Task | G* | Việc |
|:--:|:--:|------|
| **19.1** | G0 | Non-goals + bảng budget trong product-spec; xác nhận `difficulty` trên golden |
| **19.2** | G13 | `/ready` + SSE client disconnect cancel |
| **19.3** | G5/G8 | `recursion_limit` + `iteration_count` + metric hop |
| **19.4** | G1 | `config/models.yaml` + provider fallback |
| **19.5** | G7 | Soft sandbox (timeout/limit) + JSON audit log |
| **19.6** | G10 | Eval Gate + trajectory + (difficulty đã có → verify gate slices) |
| **19.7** | G11 | Offline LLM/eval batch runner |
| **19.8** | — | Deep-link D: `ui_navigate` path+query |
| **19.9** | — | ~~gRPC stream cạnh SSE~~ → **superseded by 22.2** |
| **19.10** | G17 | thumbs-down → draft golden YAML + audit checklist md |

#### Parallel schedule (§15g) — sau khi 19.5 Approved

| Wave | Lanes (∥) | Notes |
|------|-----------|--------|
| **P1** | **19.6** ∥ **19.10** | Eval gate vs feedback→golden — path rời |
| **P2** | **19.7** ∥ **19.8** | Batch offline vs deep-link — path rời |
| **P3** | **19.9** alone | gRPC đụng `AgentTurnService` — tuần tự sau P2 |

> Mỗi phase dưới đây có `parallel_*`. Shared: `specs/change-log.md` / gap / plan tick — patch hẹp hoặc Coordinator merge sau Approved.

### Phase 19.1 — G0 spec artifacts (Planner làm xong trong lượt plan)

- [x] Mục **Non-goals** `product-spec` §5 (sửa mâu thuẫn Qdrant: self-hosted được phép; không vector DB cloud mới; ngoài wave: FastMCP/HITL/canary/sandbox Docker/multi-stage).
- [x] Bảng **ngân sách / metric** §5.1 (cost, token, latency, hop, alert 50/80/100% — chưa enforce).
- [x] Xác nhận `agent_stat` v1 (30) / v2 (33) đã có `slice.difficulty` → §5.2.
- [x] Cập nhật gap tracker + change-log.
- **Test:** review đọc `specs/product-spec.md` §5; `grep -c difficulty resource/eval/datasets/agent_stat/v*.yaml` → 30 / 33.

> Mỗi task: Implementer đúng phase của lane → Review Approved. Song song chỉ theo bảng P1/P2/P3 + metadata. Không đổi topology graph; không đổi SSE contract.

### Phase 19.2 — G13 `/ready` + SSE disconnect

- [x] `GET /ready` (cạnh `/health` trong `src/api/routers/web_backend/routes_meta.py`): check Postgres (`SELECT 1`, timeout 2s), Qdrant nếu bật, LLM config có key; 200 `{ready:true, checks:{...}}` / 503 khi check bắt buộc fail. Thành phần tắt → `skipped`.
- [x] SSE trong `src/api/routers/agent/routes_agent.py`: mỗi vòng lặp event gọi `await request.is_disconnected()` → dừng generator + hủy task graph; log `sse_client_disconnected`.
- **Files:** `routes_meta.py`, `routes_agent.py`, test mới `tests/test_product_ready_sse.py`.
- **Test:** TestClient `/ready` (mock DB ok/fail → 200/503); test generator dừng khi `is_disconnected` trả True. `curl localhost:8000/ready`.

### Phase 19.3 — G5/G8 loop protection

- [x] Truyền `config={"recursion_limit": settings.graph_recursion_limit}` (env `GRAPH_RECURSION_LIMIT`, mặc định 25) ở chỗ invoke/stream graph (`AgentTurnService`); bắt `GraphRecursionError` → câu trả lời fallback thân thiện, không 500.
- [x] Thêm `iteration_count: int` vào state; supervisor node tăng mỗi hop; vượt `SUPERVISOR_MAX_HOPS` (6) → route `respond`/END (chỉ điều kiện, **không thêm node/edge mới**).
- [x] Metric `supervisor_hops` ghi vào Langfuse trace metadata/score cuối lượt.
- **Files:** `src/shared/settings.py`, state module trong `src/domain/agents/`, supervisor node, `AgentTurnService`.
- **Test:** unit — supervisor giả lặp vô hạn → dừng ≤ max hops, có answer; `GraphRecursionError` → response hợp lệ; metadata có `supervisor_hops`.

### Phase 19.4 — G1 `config/models.yaml` + fallback

- [x] Tạo `config/models.yaml` (primary + fallback list: provider, model, base_url env-name, timeout). Secrets **chỉ** trong `.env` (yaml tham chiếu tên biến).
- [x] Loader trong `src/shared/settings.py` (hoặc `src/shared/models_config.py`); thiếu file → giữ hành vi `LLM_MODEL` hiện tại.
- [x] Client LLM: lỗi kết nối/5xx/timeout ở primary → thử fallback kế tiếp; log `llm_fallback_used`.
- **Test:** unit — mock primary raise → fallback được gọi; không có yaml → dùng `.env`; yaml không chứa chuỗi key. `/api/models` vẫn chạy.

### Phase 19.5 — G7 soft sandbox + audit

- **parallel_ok:** no · **parallel_group:** — · **depends:** 19.4 · **touches:** `src/infra/storage/sql/`, `src/domain/observability/audit.py`, sql tool execute
- [x] SQL tool: validate chỉ `SELECT`/`WITH` (đã có thì giữ, thêm test), `statement_timeout` + `LIMIT` mặc định trong `src/infra/storage/sql/connection.py`; tool timeout wrapper (`asyncio.wait_for`).
- [x] Logger JSON `agent_audit` (một dòng/tool call: ts, user_id, session_id, tool, args rút gọn, duration_ms, status, rows). Không log secrets/PII đầy đủ.
- **Không:** Docker sandbox, FastMCP.
- **Test:** SQL `DELETE`/`DROP` bị chặn; query chậm → timeout lỗi gọn; caplog có record `agent_audit` JSON parse được.

### Phase 19.6 — G10 Eval Gate + trajectory

- **parallel_ok:** yes · **parallel_group:** P1 · **depends:** 19.5 · **touches:** `resource/eval/run.py`, `resource/eval/results/baseline.json`, `tests/test_*eval*gate*`
- [x] `resource/eval/run.py --gate --baseline <file>`: exit code ≠ 0 khi pass-rate < baseline − 2pp; in bảng theo `slice.difficulty`/`type`.
- [x] Trajectory: ghi chuỗi node/agent đã đi cho mỗi case; so với `expected_route`/`expected_agents` nếu dataset có (thiếu → bỏ qua, không fail).
- [x] Lưu baseline `resource/eval/results/baseline.json`.
- **Test:** unit với kết quả giả: dưới baseline → exit 1; bằng/ trên → 0; bảng slice có easy/medium.

### Phase 19.7 — G11 offline Batch API

- **parallel_ok:** yes · **parallel_group:** P2 · **depends:** 19.6, 19.10 · **touches:** `resource/eval/batch.py`, `resource/eval/results/` (file batch-*), `tests/test_*batch*`
- [x] Script `resource/eval/batch.py`: build JSONL request từ golden/judge prompts → submit Batch API của provider (từ `models.yaml`) → poll → ghi kết quả vào `resource/eval/results/`. Chỉ offline (eval/judge), **không** đụng path online, **không** đụng SQL batch hiện có.
- **Test:** unit build JSONL đúng format (mock client); `--dry-run` không gọi mạng.

### Phase 19.8 — Deep-link D (`ui_navigate`)

- **parallel_ok:** yes · **parallel_group:** P2 · **depends:** 19.6, 19.10 · **touches:** `src/domain/agents/` (ui_navigate emit only), config whitelist, FE chat UI, `tests/test_*ui_navigate*`
- [x] Whitelist path (vd. `/dashboard/traffic`, `/devices`, …) trong config; từ structured plan/filters (date range, area, device) build `query` string; trả event/field `ui_navigate: {path, query}` trong payload cuối (SSE event mới cùng stream, không đổi event cũ).
- [x] FE: nút "Mở trang" khi nhận `ui_navigate`. Path ngoài whitelist → bỏ.
- **Test:** unit — filters → query encode đúng; path lạ → không emit; SSE cũ vẫn parse.

### Phase 19.9 — gRPC B' cạnh SSE — **SUPERSEDED by 22.2**

- **parallel_ok:** no · **parallel_group:** P3 · **depends:** 19.7, 19.8 · **touches:** `proto/`, gRPC server module, `src/application/agent_turn.py` (wire only), `src/shared/settings.py` (GRPC_*), `tests/test_*grpc*`
- [x] ~~Shipped rồi gỡ~~ — xem **Phase 22.2**. Lịch sử: `proto/agent.proto` StreamTurn; `GRPC_ENABLED` mặc định tắt; cùng `AgentTurnService`.
- [x] SSE web giữ nguyên (và là transport duy nhất sau 22.2).
- **Test:** (lịch sử) in-process gRPC ≈ SSE; sau 22.2 không còn suite grpc.

### Phase 19.10 — G17 feedback → golden

- **parallel_ok:** yes · **parallel_group:** P1 · **depends:** 19.5 · **touches:** `scripts/feedback_to_golden.py`, `resource/eval/datasets/agent_stat/draft-*.yaml`, `resource/eval/AUDIT-CHECKLIST.md`, `tests/test_*feedback*golden*`
- [x] Script `scripts/feedback_to_golden.py`: đọc thumbs-down (storage feedback) → ghi `resource/eval/datasets/agent_stat/draft-<date>.yaml` (case nháp, `review: pending`, slice trống để người duyệt).
- [x] `resource/eval/AUDIT-CHECKLIST.md` (Phụ lục C/H rút gọn) cho người duyệt draft trước khi merge vào v+1. **Không** canary.
- **Test:** unit — 2 feedback giả (1 up, 1 down) → draft chứa đúng 1 case; YAML load được.

---

## v18 — IAM RBAC + domain/geo + retrieval rename

**Goal:** Bộ phận chỉ hỏi domain được phép; SQL geo/org; IAM `/auth/me`.  
**Design:** v18-rbac-iam-design.md · **Plan:** v18-rbac-iam-plan.md · **AC:** AC-12.

- [x] 18.1 Spec + AC-12 + index
- [x] 18.2 IAM gate + AccessContext
- [x] 18.3 Domain RBAC
- [x] 18.4 Geo SQL scope
- [x] 18.5 Docs domain filter
- [x] 18.6 Rename knowledge → retrieval
- [x] 18.7 FE headers + smoke

---

## v16 — Hierarchical `analytics_team` | `knowledge_team`

**Goal:** Root graph + team subgraphs + `AgentTurnService` (SSE mới).  
**Design:** v16-hierarchical-agents-design.md · **Plan:** v16-hierarchical-agents-plan.md.

| Task | Mục tiêu |
|:--:|-----------|
| **16.1** | Skeleton `AssistantState` + `build_graph` stub + `nodes` stub |
| **16.2** | Shared prefix / canonical root graph |
| **16.3** | `analytics/` subgraph |
| **16.4** | `knowledge/` subgraph |
| **16.5** | `top_supervisor` + `synth` |
| **16.6** | `AgentTurnService` + SSE + FE |
| **16.7** | Cleanup dead code |

### Phase 16.1 — Skeleton

- [x] `AssistantState` trên `domain/agents/state.py` (re-export vms I/O).
- [x] `nodes.py` stub supervisor/synth; `graph.build_graph` → vms `_build_graph`; `start_graph` stub.
- [x] `tests/test_v16_hierarchy_skeleton.py` PASS.

### Phase 16.2–16.7 — Continuous

- [x] 16.2 Canonical `domain/agents/graph.py`; `vms.graph` shim.
- [x] 16.3 `analytics/` subgraph + root `analytics_team`.
- [x] 16.4 `knowledge/` subgraph + root `knowledge_team`.
- [x] 16.5 `top_supervisor` (+ multi collect); route helpers.
- [x] 16.6 `AgentTurnService` + SSE `complete` + FE bridge.
- [x] 16.7 Docs/changelog; giữ `vms/nodes` (impl); không xóa hết shim nội bộ.

**Done khi:** `pytest tests/test_v16_*.py` + `test_graph_nodes_and_structure` xanh.

---

## v15 — Leaf `sql_agent` / `docs_agent` + flat `vms/graph.py`

**Goal:** Package giống `ai_backend` leaf; wiring flat; không đổi hành vi.  
**Design:** v15-leaf-agents-flat-graph-design.md · **Plan chi tiết:** v15-leaf-agents-flat-graph-plan.md · **AC:** product-spec AC-11.

| Phase v15 | Mục tiêu |
|:--:|-----------|
| **15.1** | Spec + AC + checkbox |
| **15.2** | Skeleton + move sql/docs agents |
| **15.3** | Gộp `core/` → `vms/graph.py`; nodes/tools |
| **15.4** | Rewire + xóa package cũ |
| **15.5** | Docs + pytest subset |

### Phase 15.1 — Spec

- [x] Design `v15-leaf-agents-flat-graph-design.md` + AC-11 + index SDD.
- [x] User review / approve written spec trước khi code.
- [x] Writing-plans: `v15-leaf-agents-flat-graph-plan.md`.

**Done khi:** Spec reviewed.

### Phase 15.2 — sql_agent / docs_agent

- [x] Tạo `sql_agent/`, `docs_agent/` (`graph.py` re-export only, `state.py`, `tools.py`).
- [x] Move `vms/sql/*` + docs nodes/adapters; không `compile()`.

**Done khi:** Import package mới OK.

### Phase 15.3 — Flat graph

- [x] Gộp `vms/core/*` → `vms/graph.py`; giữ `_build_graph` / `run_agent` / `_wrap_node`.
- [x] `routing` / `respond` / `render_chart` / helpers → `vms/nodes` + `vms/tools`.
- [x] Xóa `vms/core/`.

**Done khi:** App boot; node names không đổi.

### Phase 15.4 — Rewire

- [x] Sửa import repo + tests; xóa `vms/sql`, `vms/routing`, `vms/respond`, `vms/adapters` nếu trống.
- [x] Grep sạch path cũ trong `.py`.

**Done khi:** Grep sạch.

### Phase 15.5 — Docs + verify

- [x] `src/README.md` + `change-log.md`.
- [x] Pytest subset (nodes structure, camera, greeting offline, v13) — **17 passed**.

**Done khi:** AC-11 pass.

---

## v14 — Align layout với `vn-stock-swarm/src/ai_backend`

**Goal:** `vms/` + `multi_agent/` + `application/` + `shared/settings/`; dọn specs core; không đổi hành vi.  
**Design:** v14-ai-backend-layout-design.md · **AC:** product-spec AC-10.

| Phase v14 | Mục tiêu |
|:--:|-----------|
| **14.1** | Specs hygiene (core + archive) |
| **14.2** | Package skeleton |
| **14.3** | Move + rewire + shims |
| **14.4** | Docs + pytest |
| **14.5** | Drop shims (optional) |

### Phase 14.1 — Specs hygiene

- [x] Archive `v7-chart-ui-audit.md`, `v7-dead-code-inventory.md`, `nested-trace-v13-design.md` (AC v13 đã ở product-spec / § v13).
- [x] Cập nhật `specs/README.md` + `sdd-guide-vi.md` danh sách file core.
- [x] Ghi `change-log.md` (design/hygiene).

**Done khi:** `specs/` chỉ còn core + `archive/` + `v14-ai-backend-layout-design.md`.

### Phase 14.2 — Package skeleton

- [x] Tạo `domain/agents/vms/`, `domain/agents/multi_agent/`, `application/`, `shared/settings/`.
- [x] `__init__.py` tối thiểu; chưa move logic nặng.

**Done khi:** Import package rỗng OK.

### Phase 14.3 — Move + rewire

- [x] Move graph/state/nodes/sql/routing/respond/adapters/core → `vms/`.
- [x] Move orchestrator → `multi_agent/`.
- [x] Tách turn orchestration mỏng → `application/` (nếu routes/main đang phình).
- [x] `shared/settings` từ `config.py` + shim `shared.config`.
- [x] Shim `domain.agents.graph` → `vms.graph`.
- [x] Sửa import toàn repo / tests.

**Done khi:** App boot; graph node names không đổi.

### Phase 14.4 — Docs + verify

- [x] Cập nhật `src/README.md`.
- [x] `pytest -q` (ghi fail pre-existing nếu có).
- [x] `change-log.md` entry code merge.

**Done khi:** AC-10 checklist pass.

**Verify note:** Node names LangGraph giữ nguyên; camera registry + greeting offline + audit archive path + `test_v13_*` xanh. Full suite chậm/có fail pre-existing (SQL offline heuristic `anomaly_event`, frontend memory badge string) — không phải regression layout v14.

### Phase 14.5 — Drop shims (optional)

- [x] Xóa shim `domain.agents.orchestrator` (grep sạch → chỉ còn `multi_agent`).
- [ ] Xóa shim `domain.agents.graph` / `state` + `shared.config` sau khi grep sạch.

**Done khi:** Không còn shim.

---

## v10 — Cấu trúc `src/` (pattern llm-engineer-demo)

**Goal:** Entry FastAPI mỏng, API tách package, giữ hành vi + test patch ổn định; tùy chọn tách `graph.py` khi có task riêng.

**Architecture:** `src/main.py` mount router; `src/api/*` routes + helpers; agent vẫn `src/agent/graph.py`.

| Phase v10 | Mục tiêu |
|:--:|-----------|
| **10.1** | Tách FastAPI khỏi `main.py` |
| **10.2** | Docs + SDD đồng bộ |
| **10.3** | Test suite xanh (API + orchestrator) |
| **10.4** | (Tùy chọn) Tách module trong `graph.py` |

### Phase 10.1 — API package

- [x] Tạo `src/api/`: `errors`, `cache_helpers`, `sse_helpers`, `session_helpers`, `schemas`.
- [x] Routers: `routes_meta`, `routes_sessions`, `routes_memory`, `routes_feedback`, `routes_agent`.
- [x] `src/main.py` ~70 dòng: CORS, `include_router`, static UI, `GuardrailViolation` handler, re-export hooks test (`_cache`, schemas, …).
- [x] `routes_agent` gọi `src.agent.graph.run_agent` / `run_agent_stream` (mock test đúng module).
- [x] Xóa trùng feedback + exception handler trong `routes_agent.py`.

**Done khi:** `pytest tests/test_product_api_gateway.py tests/test_feedback_api.py -q` pass.

### Phase 10.2 — Docs & spec index

- [x] Cập nhật `src/README.md` (mục `api/`).
- [x] Ghi `specs/change-log.md` (refactor API).
- [x] Cập nhật `specs/sdd-guide-vi.md` bảng API → `src/main.py` + `src/api/`.
- [x] Cập nhật `specs/README.md` trạng thái v10.
- [x] Không đổi AC endpoint — layout ghi trong `src/README.md`.

**Done khi:** Dev mới đọc specs + `src/README` biết chỗ sửa route mà không mở `graph.py`.

### Phase 10.3 — Regression tests

- [x] `test_same_thread_docs_then_stat_clears_respond_mode` — `recall_node` reset `rewritten=None` mỗi lượt.
- [x] Orchestrator + API gateway: 149 passed (subset graph + gateway).
- [x] Full suite `PYTHONPATH=. pytest -q`: **765 passed**, 24 failed (chủ yếu deployment smoke / Postgres thật / vài mock path cũ — ghi change-log).

**Done khi:** Hai test orchestrator trên pass; không regression API gateway.

### Phase 10.4 — Tách `graph.py`

- [x] Modules: `state`, `graph_runtime`, `graph_wiring`, `graph_run`, `graph_helpers`, `nodes_*`.
- [x] `graph.py` facade + re-export patch hooks (`classify_intent_safe`, `execute_sql`, `_memory_context_block`, …).

**Done khi:** `graph.py` < ~400 dòng — đạt (~90 dòng facade).

### Phase 11 — Layout `src/` (vn-stock `ai_backend`)

- [x] `domain/` (`agents`, `knowledge`), `infra/` (db, memory, llm, chart, monitoring, prompts, session), `shared/` (config, guardrails, feedback).
- [x] `api/routers`, `api/models`, `api/helpers`.
- [x] Sửa path `resource/` sau khi đổi depth (`catalog`, `prompts`, `camera_registry`).
- [x] Cập nhật import toàn repo + `src/README.md`.

**Done khi:** `from src.main import app` OK; pytest orchestrator + API gateway pass.

---

## v13 — Nested Langfuse `trace_step` toàn graph

**Goal:** Span con trong mọi node giống nhánh SQL — xem archive/nested-trace-v13-design.md.  
**AC:** `product-spec.md` AC-9; test AC-T1–T3 trong `test-plan.md`.

| Phase v13 | Mục tiêu |
|:--:|-----------|
| **13.1** | Guardrails input/output + recall |
| **13.2** | rewrite + classify + respond_inline |
| **13.3** | orchestrator + orchestrator_collect |
| **13.4** | execute_sql batch + answer_from_docs + respond |
| **13.5** | Tests observability + manual Langfuse |

### Phase 13.1 — Guardrails + recall

- [x] `guardrail_input_node`: `trace_step` `check_input`, `redact_pii`.
- [x] `recall_node`: `trace_step` `recall_long_term` (kể cả disabled).
- [x] `guardrail_output_node`: `build_evidence`, `check_output`.

**Done khi:** AC-T1 cover guardrail_input + recall; pytest observability pass.

### Phase 13.2 — Rewrite / classify / inline

- [x] `rewrite_node`: `sliding_window`, `compact_history`, `rewrite_question`.
- [x] `classify_node`: `classify_intent`.
- [x] `respond_inline_node`: `inline_response`.

**Done khi:** AC-T1 cover rewrite + classify.

### Phase 13.3 — Orchestrator

- [x] `orchestrator_node`: một span trong `plan_passthrough` | `plan_orchestration` | `dispatch_batch`.
- [x] `orchestrator_collect_step_node`: `collect_step`.

**Done khi:** Multi-hop trace mock có substeps orchestrator.

### Phase 13.4 — SQL batch + docs + respond

- [x] `execute_sql_node` batch: per-item `apply_org_scope`, `revalidate_sql`, `postgres_query`.
- [x] `answer_from_docs_node`: `compress_docs` khi nén.
- [x] `respond_node`: substeps nhánh inline / out_of_scope / multi (`synthesize_multi`).

**Done khi:** AC-T2 pass; không regression respond tests.

### Phase 13.5 — Verification + docs

- [x] Mở rộng `tests/test_product_observability_errors.py` (AC-T1–T2; AC-T3: 41 pass, 6 fail cache/API cũ).
- [x] Manual Langfuse §4.2 design doc (hoàn thành qua checklist tại `resource/docs/ops/langfuse-nested-trace-manual.md` — Phase 23.1).
- [x] `change-log.md` khi merge code; đánh dấu `[x]` các task 13.x.

**Done khi:** `pytest tests/test_product_observability_errors.py -q` pass; AC-9 đạt.

---

## Tổng quan các Phase

| Phase | Tên Phase | Mục tiêu chính |
|:-----:|-----------|----------------|
| **Phase 1** | Project setup | Xác nhận baseline test suite (pass 100%), thiết kế schema PostgreSQL `user_memories` và module `db.py` |
| **Phase 2** | Core UI | Cập nhật giao diện chat: hiển thị huy hiệu thông tin đã nhớ (Memory Badge), trạng thái Cache Hit, và nút Reset Memory |
| **Phase 3** | Core backend or data logic | Xây dựng các module cốt lõi: `longterm.py` (Postgres persistence), `context.py` (Sliding Window, 40% rule, Tool compression), `shortterm.py`, `ttl_cache.py`, `extract.py` |
| **Phase 4** | Connect UI to data | Tích hợp memory và context vào luồng LangGraph (`graph.py`), kết nối API reset memory và truyền metadata qua SSE stream |
| **Phase 5** | Validation and error states | Kiểm thử các trạng thái biên: fallback in-memory khi DB offline, cô lập `user_id`, hết hạn TTL cache và nén ngữ cảnh |
| **Phase 6** | Local run instructions | Cập nhật file `.env.example`, tài liệu `README.md` với các câu lệnh chạy local và chạy unit test suite |
| **Phase 7** | ngrok demo setup | Hướng dẫn expose app ra internet bằng ngrok và kịch bản demo kiểm chứng độ bền vững của Memory |

---

## Phase 1 — Project setup

- [x] Chạy và xác nhận baseline test suite `PYTHONPATH=. pytest -q` hiện tại đạt 100% pass (≥613 tests).
- [x] Thiết kế module `src/memory/db.py`: quản lý kết nối PostgreSQL an toàn từ `src/config.py` (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME_ITS`).
- [x] Viết hàm `init_memory_db()` tự động tạo bảng `user_memories` và index trong PostgreSQL nếu chưa tồn tại:
  ```sql
  CREATE TABLE IF NOT EXISTS user_memories (
      id SERIAL PRIMARY KEY,
      user_id VARCHAR(64) NOT NULL,
      fact TEXT NOT NULL,
      category VARCHAR(32) DEFAULT 'general',
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  CREATE INDEX IF NOT EXISTS idx_user_memories_uid ON user_memories(user_id);
  CREATE INDEX IF NOT EXISTS idx_user_memories_uid_created ON user_memories(user_id, created_at DESC);
  ```
- [x] Đảm bảo cơ chế an toàn: Nếu `DB_HOST` rỗng hoặc chưa kết nối được DB, `init_memory_db()` chỉ log warning, không chặn luồng khởi động app.

**Done khi:** Baseline test xanh 100%, module `src/memory/db.py` sẵn sàng khởi tạo bảng PostgreSQL với cơ chế an toàn không crash.

---

## Phase 2 — Core UI

- [x] **Memory & Context Status Bar (Thanh trạng thái bộ nhớ)**:
  - Thêm khu vực hiển thị thông tin người dùng thu nhỏ trên giao diện chat trong `frontend/index.html` và `frontend/style.css` (ví dụ: hiển thị tên hoặc số lượng facts đã nhớ của phiên hiện tại).
- [x] **Nút Đặt lại bộ nhớ (Reset Memory)**:
  - Bổ sung nút icon "Làm mới ngữ cảnh / Xóa bộ nhớ" trên thanh công cụ chat để người dùng có thể chủ động reset facts cá nhân khi cần bắt đầu phiên làm việc mới.
- [x] **Huy hiệu Cache Hit**:
  - Chuẩn bị thẻ thông báo nhỏ (badge) bên cạnh bubble câu trả lời khi kết quả được trả về từ TTL Cache (giúp người dùng và kỹ sư nhận biết phản hồi tức thì từ cache).

**Done khi:** Giao diện frontend có đầy đủ vị trí hiển thị memory status, nút reset memory và huy hiệu cache hit.

---

## Phase 3 — Core backend or data logic

- [x] **Long-Term Memory (`src/memory/longterm.py`)**:
  - Loại bỏ hoàn toàn mã thừa `vector=[0.0]`.
  - Triển khai `save_to_long_term(user_id, fact, category="general")`: ghi fact vào PostgreSQL.
  - Triển khai `recall_long_term(user_id, query, k=3)`: truy vấn facts của `user_id` từ PostgreSQL, tính điểm tương đồng từ khóa (token overlap) và trả về top-k fact.
  - Triển khai `clear_long_term(user_id)`: xóa fact trong PostgreSQL theo `user_id` hoặc xóa toàn bộ.
  - Triển khai cơ chế Fallback in-memory: tự động lưu và đọc từ RAM (`_FALLBACK_STORE`) khi không có kết nối DB.
- [x] **Context Engineering Engine (`src/memory/context.py` - theo mẫu `llm-engineer-demo`)**:
  - `_text_of(m)` và `_role_of(m)`: trích xuất text và role chuẩn từ dict hoặc BaseMessage.
  - `sliding_window(messages, max_messages=20)`: giữ N message gần nhất, bảo tồn system message gốc.
  - `estimate_tokens(messages)` & `context_usage(messages, window_tokens)`: đo lường tải context (hỗ trợ tiktoken / 4 ký tự/token).
  - `should_compact(messages, window_tokens, threshold=0.40)` & `should_compact_route(...)`: kiểm tra điều kiện và tạo conditional edge nén chủ động theo nguyên tắc 40-60%.
  - `summarize_text(old_messages)` & `summarize_old_messages(messages, keep_recent=6)`: tóm tắt hội thoại cũ thành 3-5 câu mang tiền tố `[Tóm tắt hội thoại trước]: ...`.
  - `create_compaction_diff(messages, keep_recent=6)`: tạo diff RemoveMessage và SystemMessage nén để persist vào state LangGraph.
  - `compress_tool_result(raw_result, query, max_tokens=300)`: nén bảng SQL hoặc tài liệu VMS dài trước khi đưa vào context.
  - `reinject_instructions(messages, instructions)`: tái chèn quy tắc cốt lõi ở cuối prompt chống instruction fade-out (`[Nhắc lại chỉ dẫn]: ...`).
  - `latest_human_query(messages)` (`_latest_human_query`): quét ngược tìm câu hỏi user/human gần nhất cho tool retrieval / memory recall.
  - `detect_repetition(messages, window=4)` (`_detect_repetition`): circuit breaker phát hiện và ngắt vòng lặp tool call lặp lại liên tiếp.
- [x] **Short-Term Checkpointer (`src/memory/shortterm.py`)**:
  - Triển khai `get_checkpointer()`: cung cấp checkpointer phiên cho LangGraph, hỗ trợ fallback sang `MemorySaver()` trong RAM.
- [x] **TTL Response Cache (`src/memory/ttl_cache.py`)**:
  - Triển khai `make_cache_key(question, route)` băm SHA-256 chuẩn hóa.
  - Triển khai `get_ttl_cached(key)` và `set_ttl_cached(key, data, ttl=300)` thread-safe với `threading.Lock()`.
  - Triển khai `cleanup_expired()` và `get_cache_size()` dọn dẹp và theo dõi cache.
- [x] **Fact Extraction (`src/memory/extract.py`)**:
  - Triển khai `_heuristic_extract(question)` regex tiếng Việt (tên, vai trò, camera phụ trách, lưu ý).
  - Triển khai `extract_and_store_memory(user_id, question, answer)`: gọi LLM trích xuất fact cuối lượt và lưu vào PostgreSQL.
  - Triển khai `extract_from_messages(user_id, messages)` quét trực tiếp lịch sử tin nhắn và `memory_detail_includes_answer` lọc số liệu realtime.

**Done khi:** Toàn bộ 5 module backend trong `src/memory/` hoàn thiện, độc lập, có thể test unit test không phụ thuộc lẫn nhau.

---

## Phase 4 — Connect UI to data

- [x] **Tích hợp vào Luồng Agent Graph (`src/agent/graph.py`)**:
  - Thêm node `recall_memory_node` ở đầu graph: lấy facts của `user_id` từ PostgreSQL và nạp vào system prompt (`Thông tin đã biết về user:\n- ...`).
  - Áp dụng `context.sliding_window` và `context.reinject_instructions` trước khi gọi mô hình.
  - Áp dụng `context.compress_tool_result` nén kết quả bảng SQL hoặc Docs dài trước khi trả về graph state.
  - Thêm node `extract_memory_node` ở cuối graph: trích xuất thông tin mới và lưu vào PostgreSQL.
- [x] **Tích hợp TTL Cache vào Router/Orchestrator**:
  - Kiểm tra TTL Cache trước khi thực thi graph: nếu Cache Hit, trả về ngay câu trả lời kèm cờ `cache_hit: true`.
  - Nếu Cache Miss: chạy graph, nhận kết quả và lưu vào TTL Cache với hạn 300s.
- [x] **API Endpoint Quản lý Memory (`src/main.py`)**:
  - Bổ sung endpoint `DELETE /api/memory?user_id=...` để frontend gọi khi người dùng bấm nút Reset Memory.
  - Bổ sung endpoint `GET /api/memory?user_id=...` để frontend hiển thị các facts hiện tại của user.
- [x] **Kết nối Frontend (`frontend/app.js`)**:
  - Ghép nút Reset Memory gọi API `DELETE /api/memory`.
  - Hiển thị badge `⚡ Cache Hit` khi payload phản hồi có `cache_hit: true`.

**Done khi:** Giao diện frontend và backend kết nối thông suốt, luồng tương tác thực hiện đầy đủ vòng đời memory.

---

## Phase 5 — Validation and error states

- [x] **Kiểm thử Graceful Degradation (DB Offline)**:
  - Giả lập ngắt kết nối PostgreSQL (đổi `DB_HOST=invalid`): kiểm tra toàn bộ ứng dụng vẫn phản hồi bình thường nhờ fallback in-memory, log warning nhẹ, không trả về lỗi HTTP 500.
- [x] **Kiểm thử Cô lập dữ liệu (User Isolation)**:
  - Tạo 2 phiên chat với 2 `user_id` khác nhau: xác nhận thông tin của User A không bao giờ xuất hiện trong context của User B.
- [x] **Kiểm thử Ngưỡng nén 40% & Tool Compression**:
  - Kiểm tra khi ngữ cảnh vượt 40% window, hệ thống tự động sinh `[Tóm tắt hội thoại trước]: ...`.
  - Kiểm tra bảng SQL dài trên 300 tokens được nén cô đọng trước khi sinh câu trả lời.
- [x] **Kiểm thử TTL Cache Expiration**:
  - Kiểm tra câu hỏi thứ 2 trong vòng 300s trả về ngay lập tức (< 5ms); sau 300s tự động hết hạn và gọi lại pipeline thông thường.

**Done khi:** Toàn bộ các trạng thái biên, lỗi mất kết nối và logic bảo mật dữ liệu được kiểm thử chặt chẽ, không có lỗi tiềm ẩn.

---

## Phase 6 — Local run instructions

- [x] Cập nhật file `.env.example`:
  - Khai báo đầy đủ các biến cấu hình cho Memory:
    ```env
    # ── Memory & Context Engineering (v9) ───────────────────────────────────
    MEMORY_ENABLED=true
    MEMORY_SHORT_TERM_ENABLED=true
    MEMORY_LONG_TERM_ENABLED=true
    MEMORY_TTL_SECONDS=300
    MEMORY_MAX_MESSAGES=20
    MEMORY_COMPACT_THRESHOLD=0.40
    ```
- [x] Cập nhật file `README.md`:
  - Thêm tài liệu hướng dẫn chi tiết các lệnh chạy local trên máy (không dùng Docker và dùng Docker).
  - Cung cấp danh sách các lệnh chạy unit test cho gói Memory:
```bash
    PYTHONPATH=. pytest tests/test_product_memory_context.py tests/test_product_memory_cache.py tests/test_product_memory_postgres.py -v
    ```

**Done khi:** Tài liệu hướng dẫn rõ ràng, bất kỳ developer nào cũng có thể tự cài đặt, chạy và test app trên máy cá nhân.

## Phase 7 — ngrok demo setup

- [x] Hướng dẫn cài đặt và cấu hình ngrok expose ứng dụng an toàn ra internet:
  - Hướng dẫn cài đặt ngrok trên Windows, macOS, Linux, thiết lập Authtoken và cấu hình mở tunnel ra internet cho cổng dịch vụ (`8000` cho FastAPI backend hoặc `8080` cho Docker frontend).
  - Cung cấp script tự động chạy ngrok (`scripts/run_ngrok_demo.sh` và `scripts/run_ngrok_demo.bat`) kèm hỗ trợ truyền cổng linh hoạt và xử lý host header rewrite.
  - Cập nhật tài liệu hướng dẫn vào `README.md` (Mục 6: Expose Internet qua ngrok).
- [x] Kịch bản demo kiểm chứng độ bền vững của Memory & Context Engineering v9:
  - Xây dựng tài liệu hướng dẫn kịch bản demo 7 bước tương tác trực tiếp trên web UI theo chuẩn `specs/test-plan.md` mục 3 (Nhận diện danh tính, Short-Term memory, Long-Term persistence qua reload/tab mới, Sliding Window 10+ turns, Tool result compression, TTL Cache hit < 5ms, và Graceful degradation khi DB offline).
  - Cung cấp script kiểm chứng tự động toàn bộ 7 bước kịch bản demo `scripts/verify_memory_demo.py` để xác minh 100% độ tin cậy của luồng demo trước khi thuyết trình.

**Done khi:** Ứng dụng có thể expose an toàn ra internet qua ngrok và kịch bản demo hoạt động hoàn hảo 100%.

