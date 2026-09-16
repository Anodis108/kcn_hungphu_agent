# Implementation Plan

Không có frontend/backend tách rời — 1 FastAPI service duy nhất phục vụ cả
API và static UI (giống `atin/`). Vì vậy dùng cấu trúc `src/` đơn giản, không
`frontend/` + `backend/` riêng.

**Nguồn tham khảo:** `llm-engineer-demo/` có 2 track — Module I (native
OpenAI SDK, RAG) và Module II (`app/agent_m2/`, LangChain `bind_tools` +
`ToolNode`, LangGraph). Agent này cần vòng lặp tool-calling tự động nên đi
theo pattern Module II (Buổi 2 — bản ĐƠN GIẢN NHẤT, trước khi Buổi 3-6 thêm
memory/tool-retrieval/MCP/eval/multi-agent). Mỗi phase dưới đây ghi rõ file
nguồn cụ thể nên đọc — KHÔNG đọc toàn bộ `agent_m2/`, các buổi sau nằm ngoài
scope MVP này (xem `AGENTS.md` mục "Kỹ thuật KHÔNG dùng ở MVP này").

## Phase 1: Project Setup
- [ ] Xoá/gộp lại cấu trúc `src/` cũ (đang có code viết dở từ trước) theo
      cấu trúc mới thống nhất trong plan này
- [ ] `requirements.txt` — chỉ dependency thực sự cần (fastapi, uvicorn,
      pydantic-settings, langgraph, langchain-core, langchain-openai, openai,
      psycopg2-binary, pytest)
- [ ] `.env.example` — LLM backend + DB creds (không commit `.env` thật)
- [ ] Xác nhận `pytest` chạy được (dù chưa có test nào) + app import được

## Phase 2: Config & LLM Client
- [ ] `src/config.py` — đọc `.env` (điểm duy nhất chạm secrets). Tham khảo
      `llm-engineer-demo/app/config.py` (pattern `pydantic_settings`) +
      `atin/app/config.py` (đã thêm field DB/backend, dùng lại được gần hết)
- [ ] `src/llm.py` — client hỗ trợ 2 backend (openai/ollama qua base_url),
      key rotation, offline mode cho pytest/không có key. Tham khảo
      `llm-engineer-demo/app/llm/backends.py` (bảng backend/base_url) +
      `resilience.py` (`RotatingKeyPool`, `retry_with_backoff`) — 2 file này
      là nguồn gốc của `atin/app/llm.py`, có thể copy gần như nguyên
- [ ] Xác nhận `settings` load đúng từ `.env` (test tay: in ra `db_configured`,
      `llm_backend`)

## Phase 3: Core Backend / Data Logic (Database layer, đọc-only)
- [ ] `src/db/connection.py` — connection Postgres read-only tới 2 DB
      (`its`, `virtual_fence`), timeout, không cần pool ở MVP
- [ ] `src/db/queries.py` — hàm SQL tham số hoá cho từng nhu cầu thống kê
      (đếm lượt xe, truy vết biển số, khung giờ xâm nhập, liệt kê khu vực)
- [ ] Test kết nối thật với role read-only đã tạo (không dùng user admin) —
      verify SELECT chạy được, verify DELETE/UPDATE bị Postgres từ chối

## Phase 4: Agent (function-calling, 1 lời gọi LLM chính)
- [ ] `src/agent/tools.py` — tool tham số hoá bọc các hàm ở Phase 3 + 1 tool
      SQL đọc-only dự phòng. Tham khảo nguyên tắc thiết kế tool (error
      handling không raise, mô tả rõ tham số) ở
      `llm-engineer-demo/README.module2.md` mục "Buổi 4, Section 1" — KHÔNG
      cần idempotency/composite tool (chỉ áp dụng cho tool có side-effect,
      agent này chỉ đọc)
- [ ] `src/agent/graph.py` — vòng lặp ReAct (LangGraph): seed → agent ⇄
      tools → pack. Tham khảo cấu trúc `bind_tools`/`ToolNode` ở
      `llm-engineer-demo/app/agent_m2/nodes.py` (đoạn `_base_llm`/
      `_system_prompt`, Buổi 2 — BỎ QUA phần tool retrieval/memory/MCP ở
      cùng file, thuộc Buổi 3-4). Tiêm ngày giờ hiện tại vào system prompt
      tại mỗi lượt gọi (không hardcode lúc build graph) — bắt buộc, model
      hay bịa năm/tháng sai nếu thiếu bước này
- [ ] `src/agent/answer.py` — diễn giải số liệu thành câu tiếng Việt (LLM
      call thứ 2, tuỳ chọn qua `.env`, có fallback template không cần LLM)
- [ ] `src/main.py` — FastAPI app, endpoint `POST /ask`, `GET /health`,
      phục vụ static UI tại `/`
- [ ] `static/index.html` — UI chat tối giản (HTML/JS thuần)

## Phase 5: Validation and Error States
- [ ] `src/guardrails.py` — chặn injection/nội dung độc hại (input); kiểm
      tra phạm vi câu hỏi (in-scope keywords); đối chiếu số liệu + redact
      PII + giới hạn độ dài (output) — tất cả bằng code, không LLM. Tham
      khảo trực tiếp `llm-engineer-demo/app/guardrails/injection.py` (regex
      pattern injection tiếng Anh + tiếng Việt) và `pii.py` (regex SĐT/CCCD/
      email VN) — copy gần như nguyên, KHÔNG cần lớp `llm_injection_check`
      (LLM-based, tốn thêm 1 lời gọi LLM, vượt ngân sách "tối đa 2 LLM
      call/câu hỏi" của MVP này)
- [ ] Ghép luồng: `guardrail_input → agent → guardrail_output` (graph hub
      hoặc hàm pipeline đơn giản)
- [ ] UI hiển thị rõ 3 trạng thái: đang xử lý / trả lời thành công / lỗi
      (câu hỏi bị từ chối, lỗi kết nối DB/LLM) — không im lặng, không crash
      trắng trang
- [ ] Test offline (không cần API key/DB thật, chạy bằng `pytest`): guardrail
      chặn injection, guardrail từ chối câu hỏi ngoài phạm vi, tool SQL chặn
      câu lệnh ghi, agent chạy được ở chế độ offline (không crash khi thiếu key)
- [ ] Test thật (cần `.env` đầy đủ, chạy tay): 5 câu hỏi mẫu trong tài liệu
      gốc trả lời đúng số liệu — xem `specs/test-plan.md`

## Phase 6: Local Run Instructions
- [ ] `README.md` — prerequisites, cài đặt, biến môi trường, lệnh chạy, URL
      local, troubleshooting
- [ ] `README.md` mục "Demo với ngrok" — lệnh expose cổng FastAPI duy nhất
      (`ngrok http <port>`), không cần cấu hình thêm vì frontend/backend
      chung 1 cổng
