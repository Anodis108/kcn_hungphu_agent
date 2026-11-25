# Gap analysis — project vs Quy trình Product Agent (G0–G17)

- **Nguồn đối chiếu:** `resource/knowledge_handbook/quy-trinh-xay-dung-agent-product.md` (Phụ lục A; tham chiếu B/C)
- **Report Explorer:** `specs/agent-reports/20261123-135907-01-explorer.md` (session cũ; khôi phục nội dung vào tracker này)
- **Ngày (baseline):** 2026-11-23
- **Worktree:** `fix-product` (khôi phục từ session `update-quy-trình`)

---

## 0. Protocol cập nhật (bắt buộc)

Khi Implement / Fix / Review **Approved** một việc gắn với giai đoạn G0–G17:

1. Xác định **G\*** trong brief / `implementation-plan`.
2. Cập nhật **đúng chỗ** trong file này:
   - §1 bảng trạng thái (Done / Partial / Missing / N/A)
   - §3 mục chi tiết Partial (thêm/xóa bullet “còn thiếu”)
   - §4 ưu tiên P0–P2 nếu thay đổi
3. Chỉ đánh `Done` khi mọi mục còn thiếu của G\* đã xử lý (hoặc N/A có lý do).
4. Thêm dòng §5 Lịch sử + `specs/change-log.md`.
5. Report ghi `gap_updated: G..`.

**Ai cập nhật:** Implementer sau tick, hoặc Reviewer khi `Approved` nếu Implementer quên. Coordinator kiểm tra trước khi dispatch task kế.

---

## 1. Tóm tắt trạng thái G0–G17

| Trạng thái | Giai đoạn |
|------------|-----------|
| **Done** | G0 Spec · G1 Multi-provider/models.yaml · G2 Prompt · G5 Loop (−HITL) · G6 Memory & Context · G7 Soft sandbox+audit (−FastMCP) · G8 recursion/hops · G10 Eval Gate · G11 Batch offline (−$/alert) · G12 Prompt Registry/A/B · G13 multi-stage+/ready/SSE · G15 CI (−CD) · G16 ops MVP · G17 feedback→golden (−canary) |
| **Partial** | G3, G9, G14 |
| **Missing** | — |
| **N/A** | G4 Fine-tuning |

| | Số |
|--|:---:|
| Done | 14 |
| Partial | 3 |
| Missing | 0 |
| N/A | 1 |

---

## 2. Đã mạnh (Done)

- **G6** Memory 3 tầng (v9) + context engineering (sliding window, 40–60%, compression, re-inject)
- **G12** Prompt registry Git + A/B sticky theo `user_id`
- **G2** Prompt YAML + structured output + lint
- Hierarchical multi-agent (nền G8) + RBAC/authz (bổ trợ)

---

## 3. Partial — vấn đề còn lại

### Spec / nền tảng

| | Vấn đề còn lại |
|--|----------------|
| **G0** | ~~Done v19.1~~ — Non-goals + budget §5.1; `difficulty` đã có sẵn trên `agent_stat` v1/v2 (không phải thiếu) |
| **G1** | ~~Done v19.4~~ — `config/models.yaml` + loader + fallback `invoke_*` + `chat_stream` (+ `llm_fallback_used`); secrets chỉ qua env names |

### Agent / knowledge / tools

| | Vấn đề còn lại |
|--|----------------|
| **G3** | Chỉ keyword/regex trên YAML — chưa vector/embedding VN, chunking 512/64, reranker, RAGAS |
| **G5** | ~~recursion_limit 25~~; ~~loop guard SUPERVISOR_MAX_HOPS 6~~ (19.3); chưa HITL interrupt_before (non-goal v19) |
| **G7** | ~~Done v19.5~~ — soft sandbox (statement_timeout + LIMIT + `run_with_timeout`) + `agent_audit` JSON (single + batch); FastMCP/Docker non-goal |
| **G8** | ~~recursion_limit & iteration_count trong state~~; ~~metric supervisor_hops ghi Langfuse~~ (19.3) |

### An toàn / eval / chi phí

| | Vấn đề còn lại |
|--|----------------|
| **G9** | Chỉ 1 lớp regex; thiếu LLM classifier / Llama-Guard; thiếu Presidio + redact STK; chưa timeout guardrail |
| **G10** | ~~Done v19.6~~ — Eval Gate (`--gate`, `--baseline`, exit ≠ 0 khi < baseline − 2pp) + trajectory eval (`expected_route`/`expected_agents`) + table theo `slice.difficulty`/`type` + `baseline.json` |
| **G11** | ~~Done v19.7 (Batch offline)~~ — `resource/eval/batch.py` JSONL + `--dry-run` + models.yaml client; hard-limit $/user + alert 50/80/100% vẫn ngoài wave |

### Serving / ops / go-live

| | Vấn đề còn lại |
|--|----------------|
| **G13** | ~~Done v20.1~~ — multi-stage Dockerfile (builder+runtime, COPY src/resource/config, appuser 10001, HEALTHCHECK /ready); ~~SSE is_disconnected()~~; ~~GET /ready~~ (19.2) |
| **G14** | Partial (v21.3+21.4): cấu trúc CD local (`deploy/release.sh`, `smoke.py`, `.github/workflows/cd.yml`, `deploy.yml` skeleton); cloud secrets / WIF / automated CD cloud production vẫn Missing |
| **G15** | ~~Done v20.2~~ — `.github/workflows/ci.yml` push+PR / Python 3.11 / pip cache / offline pytest (−CD deploy); curated `--ignore` for DB/Qdrant/LLM/SyntaxError |
| **G16** | ~~Done v20.6~~ — playbooks 20.3; breaker 20.4; sampling 20.5; dashboard-map 7 widgets (`name=="chat"`, `rating=="negative"`) 20.6 Approved; budget hard-limit $/user ngoài wave |
| **G17** | ~~Done v19.10~~ — thumbs-down → `draft-<date>.yaml` (`review: pending`, slice trống) + `AUDIT-CHECKLIST.md` (C/H rút gọn); canary/beta non-goal |

---

## 4. Ưu tiên (Missing + Partial)

### P0
1. ~~CI GitHub Actions~~ — **G15** (xong 20.2; CD vẫn non-goal / G14)
2. ~~Eval Gate tự động~~ — **G10** (xong 19.6)
3. ~~SSE `is_disconnected()`~~ — **G13** (xong 19.2)
4. ~~Endpoint `/ready` + multi-stage Dockerfile~~ — **G13** (19.2 + 20.1)

### P1
1. Vector RAG — **G3**
2. ~~`recursion_limit` / loop guard~~ — **G5**, **G8** (xong 19.3; HITL non-goal)
3. Guardrails sâu hơn + redact STK — **G9**

### P2
1. ~~Feedback → golden~~ — **G17** (xong 19.10; canary non-goal)
2. Secrets / cloud / backup — **G14** (Partial — CD local-first v21.3+21.4; cloud/secrets Missing)
3. ~~Incident playbooks / breaker / sampling / dashboard map (20.3–20.6)~~ — **G16** Done v20; budget hard-limit $/user ngoài wave

---

## 5. Lịch sử cập nhật

| Ngày | G\* | Thay đổi | Task / evidence |
|:---|:---|:---|:---|
| 2026-11-23 | — | Baseline từ Explorer; bố cục báo cáo Coordinator | session `update-quy-trình` / Explorer report |
| 2026-11-23 | — | Khôi phục tracker + protocol vào worktree `fix-product` | restore sau khi mất worktree cũ |
| 2026-11-23 | all | Design grill **Approved** — wave v19 (thứ tự G0→G13→G5/G8→G1→G7→G10→G11→deep-link D→gRPC B'→G17); loại FastMCP/HITL/canary/Docker sandbox | `implementation-plan.md` § v19 |
| 2026-11-23 | — | Reviewer-5a **Blocked** 19.9 — `src/main.py` lifespan dùng `logger` chưa định nghĩa khi `GRPC_ENABLED` start fail → NameError abort app | `main.py` `_lifespan` · Fix-only 19.9 |
| 2026-11-23 | — | Reviewer-5a **Approved** 19.9 (re-review Fix-only) — logger defined; lifespan fail path không crash; wave v19 checklist complete | `20261123-*-05a-reviewer.md` · task 19.9 |
| 2026-11-23 | G0 | **Done**: Non-goals + budget table + sửa mâu thuẫn Qdrant; `slice.difficulty` đã có trên `agent_stat` v1 (30) / v2 (33) | `product-spec.md` §5 · task 19.1 |
| 2026-11-23 | G13 | **Partial** (tiến độ 19.2): Thêm `/ready` (Postgres/Qdrant/LLM) + SSE client `is_disconnected()` cancel & log; multi-stage Dockerfile hoãn | `routes_meta.py`, `routes_agent.py`, `test_product_ready_sse.py` · task 19.2 |
| 2026-11-23 | G5/G8 | **Done** (tiến độ 19.3): `recursion_limit` 25 + `iteration_count` state + guard `SUPERVISOR_MAX_HOPS` (6) + metric `supervisor_hops` Langfuse; bắt `GraphRecursionError` không 500 | `settings.py`, `graph.py`, `supervisor.py`, `test_product_loop_protection.py` · task 19.3 |
| 2026-11-23 | G5/G8 | Reviewer-5a **Approved** 19.3 — §1 Done (−HITL); §4 P1 struck | `20261123-*-05a-reviewer.md` · task 19.3 |
| 2026-11-23 | G1 | **Partial** (tiến độ 19.4 Implementer): `config/models.yaml` + loader + fallback invoke_* ; chưa Approved | `config/models.yaml`, `models_config.py`, `test_product_models_fallback.py` · task 19.4 |
| 2026-11-23 | G1 | Reviewer-5a **Blocked** 19.4 — `chat_stream` không fallback/`llm_fallback_used` dù respond dùng path này | `completion.py` `chat_stream` · Fix-only 19.4 |
| 2026-11-23 | G1 | **Fix applied** (Fix-only 19.4): Bọc `chat_stream` với logic provider fallback + `llm_fallback_used` logging; test pass | `src/infra/llm/completion.py`, `tests/test_product_models_fallback.py` · Fix-only 19.4 |
| 2026-11-23 | G7 | **Partial** (tiến độ 19.5 Implementer): soft sandbox + audit trên single execute; chưa Approved | `connection.py`, `audit.py`, `execute.py`, `test_product_sandbox_audit.py` · task 19.5 |
| 2026-11-23 | G7 | Reviewer-5a **Blocked** 19.5 — batch `sql_batch≥2` bỏ qua `run_with_timeout` + `log_agent_audit` | `execute.py` batch branch · Fix-only 19.5 |
| 2026-11-23 | G1 | Reviewer-5a **Approved** 19.4 (re-review Fix-only) — §1 Done | `20261123-*-05a-reviewer.md` · task 19.4 |
| 2026-11-23 | G7 | **Fix applied** (Fix-only 19.5): Bọc `sql_batch>=2` với `run_with_timeout` cho từng query + `log_agent_audit` batch; unit test pass | `execute.py`, `test_product_sandbox_audit.py` · Fix-only 19.5 |
| 2026-11-23 | G7 | Reviewer-5a **Approved** 19.5 (re-review Fix-only) — §1 Done (−FastMCP) | `20261123-*-05a-reviewer.md` · task 19.5 |
| 2026-11-23 | G17 | **Partial** (tiến độ 19.10 Implementer): `scripts/feedback_to_golden.py` + draft YAML + `AUDIT-CHECKLIST.md` (Phụ lục C/H rút gọn, không canary); chưa Approved | `feedback_to_golden.py`, `AUDIT-CHECKLIST.md`, `test_feedback_to_golden.py` · task 19.10 |
| 2026-11-23 | G17 | Reviewer-5a **Approved** 19.10 (lane B) — §1 Done (−canary); không đụng run.py/baseline | `20261123-*-05a-reviewer.md` · task 19.10 |
| 2026-11-23 | G10 | **Partial** (tiến độ 19.6 Implementer): Eval Gate (`--gate`, `--baseline`) + trajectory eval + `baseline.json` + difficulty/type breakdown; tests pass, chờ Reviewer-5a | `resource/eval/run.py`, `baseline.json`, `test_product_eval_gate.py` · task 19.6 |
| 2026-11-23 | G10 | **Fix applied** (Fix-only 19.6): .gitignore exception cho baseline.json; `--gate` thiếu baseline trả exit code 1 (không bypass auto-save); tests pass | `.gitignore`, `run.py`, `test_product_eval_gate.py` · Fix-only 19.6 |
| 2026-11-23 | G10 | Reviewer-5a **Approved** 19.6 (re-review Fix-only) — §1 Done; §4 P0 struck; `git check-ignore` exit 1; missing baseline → exit 1 | `20261123-*-06b-reviewer-5a.md` · task 19.6 |
| 2026-11-23 | G11 | **Partial** (tiến độ 19.7 Implementer): offline Batch API runner `resource/eval/batch.py` + tests; chưa Approved | `batch.py`, `test_product_eval_batch.py` · task 19.7 |
| 2026-11-23 | G11 | Reviewer-5a **Approved** 19.7 (lane A) — §1 Done (Batch offline; $/alert ngoài wave) | `20261123-*-05a-reviewer.md` · task 19.7 |
| 2026-11-25 | G16 | Reviewer-5a **Blocked** 20.3 — 4 playbooks đủ 5 mục; Important: `llm-down.md` grep `agent_audit` `"status":"failed"` nhưng code emit `"error"` | `playbooks/*.md` · Fix-only 20.3 |
| 2026-11-25 | G16 | **Fix applied** (Fix-only 20.3): Sửa grep `agent_audit` `status="error"` trong `llm-down.md`, chỉnh kỳ vọng `/api/llm/ping` status; chờ Reviewer-5a | `llm-down.md`, `latency-spike.md` · Fix-only 20.3 |
| 2026-11-25 | G13 | **Partial** (tiến độ 20.1 Implementer): multi-stage builder+runtime Dockerfile (appuser 10001, COPY src/resource/config, HEALTHCHECK /ready); chờ Reviewer | `Dockerfile`, `.dockerignore` · task 20.1 |
| 2026-11-25 | G13 | Reviewer-5a **Approved** 20.1 — §1 Done; build OK; `id -u` 10001; logs `/api/health` 200 + `/ready` 503 | `20261125-*-06b-reviewer-5a.md` · task 20.1 |
| 2026-11-25 | G15 | Reviewer-5a **Blocked** 20.2 — workflow shape OK nhưng offline `pytest tests/` (2 SyntaxError ignores) → 104 fail + 142 errors; Actions không xanh | `ci.yml` · Fix-only 20.2 |
| 2026-11-25 | G15 | Reviewer-5a **Approved** 20.2 (re-review Fix-only) — §1 Done (−CD); exact CI pytest **114 passed / exit 0** | `20261125-*-06b-reviewer-5a.md` · Fix-only 20.2 |
| 2026-11-25 | G16 | Reviewer-5a **Approved** 20.3 (re-review Fix-only) — detection `"error"` khớp code; ping expect `status`; TRACE=20.5 forward-ref; G16 vẫn Partial (20.4–20.6) | `20261125-*-05a-reviewer.md` · Fix-only 20.3 |
| 2026-11-25 | G16 | Reviewer-5a **Approved** 20.5 — `TRACE_SAMPLE_RATE` default 1.0; invalid→1.0+warn; Langfuse `sample_rate`; head-based limit documented; tests 6 passed; G16 vẫn Partial | `20261125-*-06a-reviewer.md` · task 20.5 |
| 2026-11-25 | G16 | Reviewer-5a **Approved** 20.4 — breaker closed/open/half-open; LLM open→fallback; SQL friendly fail-fast; TRACE coexistence OK; G16 vẫn Partial (20.6) | `20261125-*-06b-reviewer-5a.md` · task 20.4 |
| 2026-11-25 | G16 | **Partial** (tiến độ 20.6 Implementer): `dashboard-map.md` 7 widgets; chờ Review | `resource/docs/ops/dashboard-map.md` · task 20.6 |
| 2026-11-25 | G16 | Reviewer-5a **Blocked** 20.6 — Important: thumbs-down filter `rating < 0` nhưng API `"positive"\|"negative"`; filter Langfuse `agent_chat/ask/stream` không khớp `trace_name="chat"`; G16 Partial (G13/G15 Done giữ) | `dashboard-map.md` · Fix-only 20.6 |
| 2026-11-25 | G16 | **Fix applied** (Fix-only 20.6): Sửa filter Widget 1 sang `name == "chat"`, Widget 7 sang `rating == "negative"`; làm rõ `agent_audit` logger; chờ Reviewer-5a re-review | `resource/docs/ops/dashboard-map.md` · Fix-only 20.6 |
| 2026-11-25 | G16 | Reviewer-5a **Approved** 20.6 (re-review Fix-only) — §1 Done; filters khớp schema; wave v20 G13/G15/G16 đóng; **không merge** (chờ user §17 Explicit) | `20261125-*-06a-reviewer.md` · Fix-only 20.6 |
| 2026-11-25 | G14/G15 | v21 planned: CI 2 tầng + eval-gate + CD local-first (`deploy/`, `cd.yml`); G14 sẽ → Partial khi 21.4 Approved (cloud/secrets vẫn Missing) | `implementation-plan.md` § v21 |
| 2026-11-25 | G15 | Reviewer-5a **Approved** 21.1 — CI 2 tầng `checks`→`tests` + concurrency; ruff F + prompt lint; hermetic ignores preserved; G15 vẫn Done | `20261125-*-06b-reviewer-5a.md` · task 21.1 |
| 2026-11-25 | G14 | Reviewer-5a **Approved** 21.3 — `deploy/release.sh`+`smoke.py`+README local-first; G14 vẫn Missing (Partial khi 21.4) | `20261125-*-06b-reviewer-5a.md` · task 21.3 |
| 2026-11-25 | G14 | **Partial** (tiến độ 21.4 Implementer): CD local-first `.github/workflows/cd.yml` (workflow_run sau CI xanh, local smoke test, ghcr push gated) + `deploy.yml` (SSH skeleton gated ENABLE_SSH_DEPLOY); chờ Reviewer-5a | `.github/workflows/cd.yml`, `deploy.yml` · task 21.4 |
| 2026-11-25 | G14 | Reviewer-5a **Blocked** 21.4 — Important: `OPENAI_API_KEYS=""` → `/ready` 503 → `deploy/smoke.py` fail; CD không xanh “không secret” | `cd.yml` · Fix-only 21.4 |
| 2026-11-25 | G14 | **Fix applied** (Fix-only 21.4): env hermetic dummy (`OPENAI_API_KEYS=sk-x`, `LLM_BACKEND=openai`, `MEMORY_ENABLED=false`) trong `cd.yml` giúp `/ready` 200 và smoke pass không cần cloud secrets; chờ Reviewer-5a re-review | `.github/workflows/cd.yml` · Fix-only 21.4 |
| 2026-11-25 | G14 | Reviewer-5a **Approved** 21.4 (re-review Fix-only) — hermetic dummy env + wait `/ready`; local smoke PASS; naming `chatkcn`/`chatkcn-app`/`/opt/chatkcn`; G14 vẫn **Partial** (cloud/secrets Missing) | `20261125-112954-06b-reviewer-5a.md` · Fix-only 21.4 |
