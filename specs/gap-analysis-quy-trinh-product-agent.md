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
| **Done** | G2 Prompt · G6 Memory & Context · G12 Prompt Registry/A/B |
| **Partial** | G0, G1, G3, G5, G7, G8, G9, G10, G11, G13, G16, G17 |
| **Missing** | **G14** Cloud/Secrets · **G15** CI/CD |
| **N/A** | G4 Fine-tuning |

| | Số |
|--|:---:|
| Done | 3 |
| Partial | 12 |
| Missing | 2 |
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
| **G0** | Thiếu Non-goals rõ; thiếu slice `difficulty`; chưa bảng ngân sách token/cost |
| **G1** | Config vẫn qua `.env` (chưa `models.yaml`); chưa fallback multi-provider khi model chính sập |

### Agent / knowledge / tools

| | Vấn đề còn lại |
|--|----------------|
| **G3** | Chỉ keyword/regex trên YAML — chưa vector/embedding VN, chunking 512/64, reranker, RAGAS |
| **G5** | Chưa `recursion_limit`; chưa loop detection root; chưa HITL `interrupt_before` |
| **G7** | Chưa FastMCP; chưa sandbox process; chưa audit log riêng cho tool calls |
| **G8** | Chưa `recursion_limit` / `iteration_count` trong state; chưa metric Supervisor Loop Frequency (Langfuse) |

### An toàn / eval / chi phí

| | Vấn đề còn lại |
|--|----------------|
| **G9** | Chỉ 1 lớp regex; thiếu LLM classifier / Llama-Guard; thiếu Presidio + redact STK; chưa timeout guardrail |
| **G10** | Có golden 30 + runner/judge — **chưa Eval Gate** (exit code + baseline CI); chưa trajectory eval; chưa `difficulty` |
| **G11** | Có cache + fast-path — chưa daily hard-limit $/user; chưa alert 50/80/100%; chưa Batch API |

### Serving / ops / go-live

| | Vấn đề còn lại |
|--|----------------|
| **G13** | Dockerfile single-stage; SSE chưa `is_disconnected()`; chưa `/ready` (Postgres/Qdrant/LLM) |
| **G16** | Trace 100% (chưa tail sampling); chưa dashboard 7 widgets; chưa circuit breaker; thiếu 4 incident playbooks |
| **G17** | Có thumbs API — chưa pipeline thumbs-down → golden v+1; chưa audit Phụ lục C/H; chưa canary/beta rollout |

---

## 4. Ưu tiên (Missing + Partial)

### P0
1. CI GitHub Actions — **G15** (Missing)
2. Eval Gate tự động — **G10**
3. SSE `is_disconnected()` — **G13**
4. Endpoint `/ready` — **G13**

### P1
1. Vector RAG — **G3**
2. `recursion_limit` / loop guard — **G5**, **G8**
3. Guardrails sâu hơn + redact STK — **G9**

### P2
1. Feedback → golden — **G17**
2. Secrets / cloud / backup — **G14** (Missing)
3. Incident playbooks + budget hard-limit — **G11**, **G16**

---

## 5. Lịch sử cập nhật

| Ngày | G\* | Thay đổi | Task / evidence |
|:---|:---|:---|:---|
| 2026-11-23 | — | Baseline từ Explorer; bố cục báo cáo Coordinator | session `update-quy-trình` / Explorer report |
| 2026-11-23 | — | Khôi phục tracker + protocol vào worktree `fix-product` | restore sau khi mất worktree cũ |
