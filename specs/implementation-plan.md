# Implementation Plan

Không có frontend/backend tách rời — 1 FastAPI service duy nhất phục vụ cả
API và static UI (giống `atin/`). Vì vậy dùng cấu trúc `src/` đơn giản, không
`frontend/` + `backend/` riêng.

**Nguồn tham khảo:** `llm-engineer-demo/` có 2 track — Module I (native
OpenAI SDK, RAG) và Module II (`app/agent_m2/`, LangChain `bind_tools` +
`ToolNode`, LangGraph). Agent này cần vòng lặp tool-calling tự động nên đi
theo pattern Module II (Buổi 2 — bản ĐƠN GIẢN NHẤT). Mỗi phase dưới đây ghi
rõ file nguồn cụ thể nên đọc — xem `specs/product-spec.md` mục "Features
Out of Scope" cho những gì KHÔNG làm.

**Phase 1, 3, 5, 6, 7 (mục "v1 — đã xong") đã hoàn thành và verify với
Postgres thật** — xem `specs/change-log.md` (các entry ngày 2026-09-16).
Mọi mục `[ ]` còn lại là v2, CHƯA CODE. Bản kế hoạch này viết lại (rewrite)
ngày 2026-09-17 theo cấu trúc 8 phase nhỏ, gọn — số thứ tự phase KHÔNG còn
khớp với số phase trong các entry `change-log.md` trước ngày này (xem ghi
chú đầu `change-log.md`).

**Nguồn grounding cho phần v2 (không suy đoán):** `kcn/crowd/
KCN_HUNGPHU_MQTT_AI_EVENTS.md` (payload MQTT thật) và `agent-harness/
services/vms-sync/sources.py` (code sync Postgres→ClickHouse đang chạy
thật) — xác nhận tên DB/bảng/cột chính xác cho từng loại sự kiện.

---

## Phase 1: Project Setup

- [x] Xoá cấu trúc `src/` cũ (kỹ thuật đã đánh dấu Out of Scope) +
      `resource/`, `docker-compose.yml`, `main.py` cũ — bắt đầu từ khung
      trống, đúng cấu trúc thống nhất trong plan này
- [x] `requirements.txt` — chỉ dependency thực sự cần (fastapi, uvicorn,
      pydantic-settings, langgraph, langchain-core, langchain-openai,
      openai, psycopg2-binary, pytest)
- [x] `.env.example` — LLM backend + DB creds (không commit `.env` thật)
- [x] `src/config.py` — đọc `.env` (điểm duy nhất chạm secrets), pattern
      `pydantic_settings`
- [x] `src/llm.py` — client hỗ trợ 2 backend (openai/ollama qua
      `base_url`), key rotation, offline mode cho pytest/không có key
- [x] Xác nhận `pytest` chạy được, app import được, `settings` load đúng
      từ `.env`

---

## Phase 2: Mở rộng 5 domain sự kiện VMS mới

Đây là bước SCOPE cho 5 domain mới (FACE, FIRE, và 3 nhánh của ANOMALY) —
xác định nguồn dữ liệu + viết trước golden dataset (biết trước "đúng" là
gì) trước khi code Phase 3/5 hiện thực hoá nó.

### Bảng ánh xạ sự kiện → nguồn dữ liệu

| # | Sự kiện (VN) | Module (`ai_modules`) | DB.table Postgres | Cột chính | Trạng thái |
|---|---|---|---|---|---|
| 1 | Nhận diện khuôn mặt | `FACE` | `smart_face.smf_face_events` | `user_code`, `user_name`, `department_name`, `direction`, `score_match`, `access_time` | Mới |
| 2 | Giám sát phương tiện | `PLATE` | `its.plate_event` | `normalized_license_plate`, `vehicle_type`, `manufacturer`, `direction`, `event_time` | Đã có (v1) |
| 3 | Giám sát vùng cấm | `ZONE` | `virtual_fence.zone_event` | `zone_id`, `zone_name_cached`, `entity_type` (PERSON/VEHICLE), `direction` | Đã có (v1, gọi là "xâm nhập khu vực") |
| 4 | Phát hiện ẩu đả | `ANOMALY` (`event_type=FIGHT_DETECTION`) | `anomaly.anomaly_event` | `severity`, `confidence`, `zone_id`, `event_time` | Mới |
| 5 | Phát hiện đám đông | `ANOMALY` (`event_type=CROWD_DETECTION`) | `anomaly.anomaly_event` | `severity`, `zone_id`, `event_time` | Mới |
| 6 | Phát hiện leo trèo | `ANOMALY` (`event_type=INTRUSION_DETECTION`) | `anomaly.anomaly_event` | `severity`, `confidence`, `zone_id`, `zone_name` | Mới |
| 7 | Phát hiện cháy khói | `FIRE` | `firesmoke.fire_smoke_event` | `alert_level`, `entity_type` (FIRE/SMOKE), `event_time` | Mới |
| 8 | Giám sát mực nước | `ANOMALY` (`event_type=WATER_LEVEL_DETECTION`) | `anomaly.anomaly_event` | `payload.water_level`, `warning_threshold`, `danger_threshold`, `trend`, `unit` | Mới |

Lưu ý: "leo trèo" (#6) và "vùng cấm" (#3) dùng 2 bảng khác nhau dù cả 2 đều
có thể dịch là "xâm nhập" trong tiếng Việt — dễ nhầm khi thiết kế tool/prompt.

### Giả định — ĐÃ XÁC NHẬN 2026-09-17
- ~~`smart_face`, `firesmoke`, `anomaly` nằm cùng Postgres host với
  `its`/`virtual_fence`~~ — ĐÚNG, verify bằng cách connect thật tới cả 3
  DB trên `DB_HOST` hiện tại (`192.168.1.250`), không cần biến `.env` mới.
- ~~Role đọc-only hiện tại (`agent_readonly`) CHƯA có `GRANT SELECT` trên 3
  DB mới~~ — ĐÚNG lúc đầu, đã GRANT xong (tái dùng role có sẵn, không tạo
  role mới) — xem `specs/change-log.md` 2026-09-17.

### Checklist
- [x] Tạo role Postgres đọc-only trên 3 DB mới (`smart_face`, `firesmoke`,
      `anomaly`) — lặp lại SQL mẫu trong README, chỉ đổi tên DB. Verify
      SELECT chạy được, verify DELETE/UPDATE bị từ chối. (Xác nhận: dùng
      role `agent_readonly` đã có sẵn, GRANT thêm trên 3 DB mới — không
      tạo role mới. Xem `specs/change-log.md` 2026-09-17.)
- [x] `src/config.py` — thêm `DB_NAME_FACE`, `DB_NAME_FIRE`,
      `DB_NAME_ANOMALY` (đổi được qua `.env` như 2 DB hiện có).
      `.env.example` cập nhật tương ứng. (Xem `specs/change-log.md`
      2026-09-17.)
- [x] `src/guardrails.py` — mở rộng `STAT_KEYWORDS` với từ khoá domain mới
      (khuôn mặt, ẩu đả, đám đông, leo trèo, cháy, khói, mực nước) — nếu
      không, câu hỏi domain mới sẽ bị `in_scope()` từ chối oan. (Xem
      `specs/change-log.md` 2026-09-17.)
- [x] `eval/datasets/agent_stat/v2.yaml` — 30 case (giữ nguyên cấu trúc
      slice của v1), trải đều theo 8 domain. (Xem `specs/change-log.md`
      2026-09-17.)

      | Slice | Số case | Ghi chú |
      |---|---|---|
      | lookup | 18 | ~2 case/domain × 8 domain + 2 case dự phòng cho domain nhiều biến thể hơn (PLATE) |
      | comparison/multihop | 6 | Ưu tiên câu hỏi CHÉO domain (vd. "hôm nay có cháy khói và đám đông ở khu nào không") |
      | out_of_scope | 3 | Giữ nguyên câu hỏi cũ |
      | injection | 3 | Giữ nguyên câu hỏi cũ |

      Case giá trị đổi theo ngày vẫn chỉ dùng `must_include`/
      `must_include_tool`, không dùng `expected` cứng — đúng quy ước v1.
- [x] `eval/run.py` (mới) — script tối thiểu: đọc YAML, gọi `run_agent()`
      từng case, kiểm `must_include`/`must_include_tool`/
      `must_not_include`, in pass/fail theo `slice.type`. Sẽ CHƯA chạy hết
      được cho tới khi Phase 3 + Phase 5 xong (tool/domain mới chưa tồn
      tại) — viết trước là chủ ý, giống cách viết test trước khi code.
      (Xem `specs/change-log.md` 2026-09-17 — script đi qua ĐÚNG pipeline
      `check_input → in_scope → run_agent → check_output`, không chỉ gọi
      thẳng `run_agent()`, để case out_of_scope/injection chấm đúng.)

---

## Phase 3: Core Backend / Data Logic (Database layer, đọc-only)

### v1 — đã xong
- [x] `src/db/connection.py` — connection Postgres read-only tới 2 DB
      (`its`, `virtual_fence`), timeout, không cần pool ở MVP
- [x] `src/db/queries.py` — 4 hàm SQL tham số hoá (đếm lượt xe, truy vết
      biển số, khung giờ xâm nhập, liệt kê khu vực)
- [x] Test kết nối thật với role read-only — verify SELECT chạy được,
      verify DELETE/UPDATE bị Postgres từ chối

### v2 — chưa code (domain mới, dựa trên Phase 2)
- [x] `src/db/connection.py` — mở rộng whitelist DB (lớp code chặn kết
      nối ngoài phạm vi) để chấp nhận thêm 3 DB mới, giữ nguyên cơ chế
      chặn DB lạ. (Xem `specs/change-log.md` 2026-09-17.)
- [x] `src/db/queries.py` — thêm hàm SQL tham số hoá theo đúng pattern có
      sẵn (placeholder `%s`, không nối chuỗi):
      - `count_face_events(date_from, date_to, direction, group_by)` →
        `smart_face.smf_face_events`
      - `count_fire_smoke_events(date_from, date_to, entity_type)` →
        `firesmoke.fire_smoke_event`
      - `count_anomaly_events(date_from, date_to, event_type, group_by)` →
        `anomaly.anomaly_event`, DÙNG CHUNG cho 4 sự kiện (FIGHT_DETECTION/
        CROWD_DETECTION/INTRUSION_DETECTION/WATER_LEVEL_DETECTION),
        `event_type` bắt buộc + validate whitelist
      - `water_level_latest(zone_code)` — KHÔNG thêm (golden dataset không
        cần giá trị mực nước hiện tại, chỉ cần đếm sự kiện qua
        `count_anomaly_events`).
      (Xem `specs/change-log.md` 2026-09-17 — phát hiện + sửa bug org
      filter khi test thật, ảnh hưởng cả `eval/datasets/agent_stat/v2.yaml`.)
- [x] Test kết nối thật với role read-only cho 3 DB mới — verify SELECT
      chạy được, verify DELETE/UPDATE bị từ chối (giống thủ tục v1). (Xem
      `specs/change-log.md` 2026-09-17 — chạy lại tường minh 1 lần cho cả
      3 DB, đã verify rải rác ở các item trước đó của Phase 2/3.)

---

## Phase 4: Core Observability — Langfuse Tracing (connect)

Chỉ dựng HẠ TẦNG tracing ở phase này — wiring vào pipeline thật (main.py,
graph.py) thuộc Phase 5.

- [x] Deploy Langfuse **self-hosted trên chính máy này** bằng Docker
      Compose chính thức của Langfuse (không dùng Langfuse Cloud). Xác
      nhận UI truy cập được, tạo 1 project, lấy `public_key`/`secret_key`.
      (Xem `specs/change-log.md` 2026-09-17 — thư mục `langfuse/`, UI tại
      `http://localhost:3000`, project/key tạo tự động qua
      `LANGFUSE_INIT_*`, đã verify hoạt động thật qua API.)
- [x] `src/config.py` — thêm `MONITORING_ENABLED` (mặc định `false`),
      `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.
      `.env.example` cập nhật, `requirements.txt` thêm `langfuse`. (Xem
      `specs/change-log.md` 2026-09-17.)
- [x] `src/monitoring/tracing.py` (mới) — copy nguyên tắc từ
      `llm-engineer-demo/app/monitoring/tracing.py`: `trace_answer()`
      (context manager cho 1 lượt `/ask`), `trace_step()` (nested span cho
      bước con). Lazy import + lazy client (không phụ thuộc cứng vào
      package `langfuse` khi tắt), no-op hoàn toàn khi
      `MONITORING_ENABLED=false`. Dùng langfuse SDK trực tiếp, KHÔNG bọc
      qua LangChain callback. (Xem `specs/change-log.md` 2026-09-17 — phát
      hiện + sửa thêm 1 bug hạ tầng Langfuse trong lúc test thật.)

---

## Phase 5: Connect UI to Data

Nối UI → agent → tool → data logic (Phase 3) thành 1 luồng chạy được, và
gắn tracing (Phase 4) vào đúng chỗ.

### v1 — đã xong
- [x] `src/agent/tools.py` — tool tham số hoá bọc hàm ở Phase 3 + 1 tool
      SQL đọc-only dự phòng
- [x] `src/agent/graph.py` — vòng lặp ReAct (LangGraph): seed → agent ⇄
      tools → pack. Tiêm ngày giờ hiện tại vào system prompt mỗi lượt gọi
      (không hardcode lúc build graph)
- [x] `src/agent/answer.py` — diễn giải số liệu thành câu tiếng Việt (LLM
      call thứ 2, tuỳ chọn qua `.env`, có fallback template)
- [x] `src/main.py` — FastAPI app, `POST /ask`, `GET /health`, phục vụ
      static UI tại `/`
- [x] `static/index.html` — UI chat tối giản (HTML/JS thuần)

### v2 — chưa code
- [x] `src/agent/tools.py` — bọc 3 hàm mới từ Phase 3 thành `@tool`,
      docstring nêu RÕ whitelist `event_type` hợp lệ cho
      `count_anomaly_events` (LLM đọc docstring để không bịa tham số).
      (Xem `specs/change-log.md` 2026-09-17.)
- [x] `list_khu_vuc` (hoặc tool mới) — mở rộng liệt kê thêm camera có
      `ai_modules` FACE/FIRE/ANOMALY.
      (Xem `specs/change-log.md` 2026-09-17.)
- [x] `src/main.py` (`ask()`) — bọc toàn bộ pipeline
      `guardrail_input → agent → guardrail_output` trong `trace_answer()`
      (từ Phase 4). (Xem `specs/change-log.md` 2026-09-17.)
- [x] `src/agent/graph.py` — wire `trace_step()` vào các bước con (chọn
      tool, chạy tool, `answer.py` diễn giải), dùng `t["_span"]` làm
      parent span. (Xem `specs/change-log.md` 2026-09-17 — kèm
      `src/agent/react.py` vì node agent/tools nằm ở helper ReAct.)

---

## Phase 6: Validation and Error States

### v1 — đã xong
- [x] `src/guardrails.py` — chặn injection/nội dung độc hại (input); kiểm
      tra phạm vi câu hỏi; đối chiếu số liệu + redact PII + giới hạn độ
      dài (output) — tất cả bằng code, không LLM
- [x] Ghép luồng: `guardrail_input → agent → guardrail_output`
- [x] UI hiển thị rõ 3 trạng thái: đang xử lý / trả lời thành công / lỗi
- [x] Test offline (`pytest`): guardrail chặn injection, guardrail từ
      chối câu hỏi ngoài phạm vi, tool SQL chặn câu lệnh ghi, agent chạy
      offline không crash
- [x] Test thật (5 câu hỏi mẫu qua endpoint đầy đủ) — xem `test-plan.md`

### v2 — chưa code
- [x] Test offline domain mới: `count_anomaly_events(event_type=...)`
      ngoài whitelist → lỗi rõ ràng, không query DB; `in_scope()` nhận
      đúng câu hỏi domain mới; `get_connection()` chặn `dbname` ngoài 5 DB
      hợp lệ. (Xem `specs/change-log.md` 2026-09-17 —
      `tests/test_offline.py`.)
- [x] Test guardrail an toàn cho 3 DB mới: SELECT chạy được, DELETE/UPDATE
      bị từ chối — lặp lại thủ tục v1 cho `smart_face`/`firesmoke`/
      `anomaly`. (Xem `specs/change-log.md` 2026-09-18 —
      `tests/test_db_guardrail_new_dbs.py`: lớp app
      `ReadOnlySqlTransaction` + lớp GRANT `InsufficientPrivilege`.)
- [x] Test thật: tối thiểu 1 câu hỏi mẫu / domain mới (5 domain), verify
      số liệu thật khớp `rows` — đặc biệt phân biệt đúng "leo trèo" vs
      "vùng cấm" (2 bảng khác nhau, xem lưu ý Phase 2). (Xem
      `specs/change-log.md` 2026-09-18 — cần fix trước 1 bug dependency
      `openai`/`httpx2` chặn mọi lời gọi LLM thật.)
- [x] Chạy `eval/run.py` full 30 case (`eval/datasets/agent_stat/v2.yaml`)
      — xác nhận tỷ lệ pass/fail theo slice; 3 case `out_of_scope` + 3 case
      `injection` PHẢI vẫn pass nguyên (tín hiệu regression nếu mở rộng
      `STAT_KEYWORDS` sai cách). (Xem `specs/change-log.md` 2026-09-18 —
      30/30 pass, ổn định qua 2 lần chạy; sửa 8 case dataset dùng
      assertion text quá cứng nhắc.)
- [x] Test Langfuse: `MONITORING_ENABLED=false` → `pytest` chạy y hệt
      trước; bật `true` + gọi `/ask` thật → trace xuất hiện trong Langfuse
      UI, không lộ `OPENAI_API_KEYS`/DB password; Langfuse service down →
      `/ask` vẫn trả lời bình thường (không crash vì lỗi tracing). (Xem
      `specs/change-log.md` 2026-09-18 — verify tận ClickHouse, phát hiện
      độ trễ khi Langfuse down cao hơn ước tính ban đầu, ~8.3s.)

---

## Phase 7: Local Run Instructions

### v1 — đã xong
- [x] `README.md` — prerequisites, cài đặt, biến môi trường, lệnh chạy,
      URL local, troubleshooting

### v2 — chưa code
- [x] `README.md` — cập nhật bảng biến môi trường: 3 DB mới
      (`DB_NAME_FACE`/`DB_NAME_FIRE`/`DB_NAME_ANOMALY`) + nhóm biến
      Langfuse (`MONITORING_ENABLED`, `LANGFUSE_*`). (Xem
      `specs/change-log.md` 2026-09-18.)
- [x] `README.md` mục "Tạo DB role read-only" — thêm ví dụ SQL cho 3 DB
      mới (cùng pattern, chỉ đổi tên DB). (Xem `specs/change-log.md`
      2026-09-18.)

---

## Phase 8: Local Demo Setup

### v1 — đã xong
- [x] `README.md` mục "Demo với ngrok" — lệnh expose cổng FastAPI duy nhất
      (`ngrok http <port>`), không cần cấu hình thêm vì frontend/backend
      chung 1 cổng

### v2 — chưa code
- [x] Demo Langfuse: mở UI Langfuse cục bộ, xem trace của 1 lượt `/ask`
      thật (input/output/latency/span con). (Xem `specs/change-log.md`
      2026-09-18 — link trace thật + hướng dẫn đăng nhập cho user tự mở.)
- [x] Demo golden dataset: chạy `eval/run.py`, trình bày báo cáo pass/fail
      theo domain — dùng làm bằng chứng "agent trả lời đúng cả 8 domain",
      không chỉ demo tay từng câu hỏi. (Xem `specs/change-log.md`
      2026-09-18 — phát hiện + sửa 1 bug thật: nhầm tool mực nước ↔
      cháy/khói trong lúc demo.)

---

## Ghi chú — phạm vi không có trong 8 phase này

**Prompt Registry** (quản lý prompt như code, versioning/rollback qua
file — vẫn đang ở `specs/product-spec.md` mục "Features In Scope") KHÔNG
có phase riêng trong bản rewrite 8-phase này, vì yêu cầu rewrite lần này
chỉ liệt kê đúng 8 phase ở trên và không nhắc Prompt Registry. Cần xác
nhận với user: giữ lại như 1 phase riêng (Phase 9) hay bỏ khỏi kế hoạch
hiện tại — tránh để `product-spec.md` hứa 1 tính năng mà
`implementation-plan.md` không lên lịch.
