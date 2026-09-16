# Change Log

## 2026-09-16 (Phase 6: `README.md` — hoàn thiện, gồm cả mục ngrok)

### Added
- Viết lại `README.md` đầy đủ (trước đó chỉ là placeholder từ Phase 1 —
  "chưa có business logic"), gồm cả 2 item của Phase 6 CÙNG LÚC (gộp vì
  cùng 1 file, tách ra 2 lần edit không có ích): Kiến trúc (tóm tắt pipeline
  `guardrail_input → agent → guardrail_output`, ngân sách 2 LLM call/câu
  hỏi — tham khảo cấu trúc `atin/README.md` đã kiểm chứng, rút gọn đúng
  tinh thần MVP của project này), Prerequisites, Cài đặt & chạy local,
  bảng tóm tắt Biến môi trường + mục "Tạo DB role read-only" (SQL, tham
  khảo nguyên `atin/README.md`, đã kiểm chứng thực tế), Chuyển sang model
  local (Ollama), Test, **Demo với ngrok** (`ngrok http 8000`, không cần
  cấu hình gì thêm vì 1 cổng duy nhất — đúng acceptance criteria), và bảng
  Troubleshooting mới (không có ở `atin/README.md`, viết riêng cho project
  này dựa trên các lỗi thực tế đã gặp qua các item/review trước: `404` ở
  `/`, `503` ở `/ask`, câu hỏi bị từ chối ngoài phạm vi, latency khi
  `ANSWER_USE_LLM=true`).

### Verified
- `pytest -q` → "5 passed" — khớp đúng số liệu ghi trong README.
- `GET /health` (qua `TestClient`) → `{"status": "ok", "llm_backend":
  "openai", "db_configured": true}` — khớp mô tả README.

## 2026-09-16 (Phase 5: Test thật — 5 câu hỏi mẫu qua endpoint đầy đủ)

### Fixed
- **BUG tìm thấy (hallucination thật của LLM, tái lập ổn định 3/3 lần):**
  chạy đủ cả 5 câu hỏi mẫu qua `POST /ask` (pipeline đầy đủ: guardrail →
  agent → guardrail_output) lần đầu tiên trong 1 lượt thống nhất, dùng biển
  số THẬT lấy từ DB (`15K40139`, cột `normalized_license_plate` trong
  `plate_event`) cho câu hỏi mẫu #4. Kết quả: `row_count=14`, `rows` có đủ
  14 dòng dữ liệu ĐÚNG (camera/thời điểm/chiều ra-vào) — nhưng
  `answer` lại nói "Không có dữ liệu khớp cho phương tiện có biển số
  15K40139", MÂU THUẪN trực tiếp với chính `rows` trong cùng response.
  - **Nguyên nhân:** `src/db/queries.py::trace_plate` (Phase 3) trả về
    columns `[event_time, camera_code, camera_name, direction,
    vehicle_type]` — KHÔNG có cột biển số (đã lọc đúng biển số ở tầng SQL
    nên không lặp lại giá trị đã biết trong output, tiết kiệm token). Khi
    `src/agent/answer.py::build_answer()` đưa dữ liệu này vào prompt cho
    LLM, model KHÔNG thấy chữ "15K40139" xuất hiện ở đâu trong phần "Dữ
    liệu" — theo đúng chỉ dẫn `_SYSTEM` ("CHỈ dựa vào số liệu được cung
    cấp"), model suy luận (SAI) rằng không có gì khớp câu hỏi.
  - Reproduce độc lập: gọi thẳng `invoke_text()` với system prompt +
    user prompt y hệt (không qua toàn bộ graph) → LLM trả lời sai giống
    hệt, ổn định — xác nhận đây là lỗi CÁCH ĐÓNG GÓI PROMPT, không phải
    lỗi ngẫu nhiên/nhiễu của model.
- **Sửa:** thêm đoạn vào `_SYSTEM` (`src/agent/answer.py`) giải thích rõ
  cho model: dữ liệu ĐÃ được lọc đúng theo điều kiện câu hỏi trước khi đưa
  vào, cột không lặp lại điều kiện lọc đã biết (nêu đích danh case "hỏi
  theo biển số cụ thể → dữ liệu sẽ không có cột biển số"), và có ≥1 dòng
  nghĩa là CÓ khớp — không được kết luận "không khớp" chỉ vì không thấy
  giá trị điều kiện lọc lặp lại trong cột.
- Verify lại: gọi trực tiếp `invoke_text()` với đúng prompt cũ (đã gây
  bug) 2 lần liên tiếp — cả 2 lần đều trả lời ĐÚNG, liệt kê đủ camera/thời
  điểm/chiều ra-vào, không còn hallucination "không khớp".

### Verified — Test thật đầy đủ (5/5 câu hỏi mẫu, qua `POST /ask`)
- Chạy lại TOÀN BỘ 5 câu qua endpoint thật (pipeline đầy đủ) sau fix:
  - Q1 (xe máy/ô tô): đúng số liệu cả 2 loại, khớp `rows`.
  - Q2 (số chỗ ngồi): đúng, có nêu rõ giới hạn "không phân loại theo số
    chỗ ngồi" (2 lần — cả trong câu LLM trả lời lẫn ghi chú cứng thêm vào).
  - Q3 (hãng xe): liệt kê đủ 26 hãng + số lượt, khớp `manufacturer` trong
    DB.
  - Q4 (truy vết biển số, biển số THẬT `15K40139`): đúng sau fix — liệt kê
    đủ 14 sự kiện, đúng ngày/giờ/camera/chiều ra-vào, khớp hoàn toàn
    `rows`. KHÔNG regression ở Q1-3, Q5.
  - Q5 (khung giờ xâm nhập): đúng khung giờ cao nhất (02:00, 557 lượt),
    khớp `zone_event`.
- `pytest` chính thức vẫn sạch (5 passed) sau fix — fix chỉ đổi
  `_SYSTEM` (system prompt tĩnh), không đổi logic offline/template nên
  không ảnh hưởng test offline.

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Pass:** verify thêm 2 case biên để đảm bảo fix instruction mới trong
  `_SYSTEM` không gây false negative NGƯỢC (model nói "có khớp" khi thực
  sự không có):
  - Biển số THẬT SỰ không tồn tại (`99Z99999`) → `rows=[]`,
    `answer="Không có dữ liệu khớp..."` (đúng, rơi về template vì
    `has_rows=False`, không gọi LLM nên không bị ảnh hưởng bởi `_SYSTEM`
    mới) — không lẫn với bug đã sửa (biển số CÓ dữ liệu nhưng bị nói sai
    là không có).
  - Loại xe không tồn tại trong schema DB (hỏi "xe đạp") → tool tự
    validate, trả `error` rõ ràng ("vehicle_type phải thuộc [...], nhận
    'BICYCLE'") thay vì hallucinate — không bị ảnh hưởng bởi thay đổi ở
    `answer.py` vì rơi về template do `q.error` có giá trị.
- **Fail:** không tìm thêm bug nào ở lượt review này.
- **Missing:** không có gì khác so với `product-spec.md`/`test-plan.md`
  cho phạm vi "test thật 5 câu hỏi mẫu". Toàn bộ Phase 5 (implementation-
  plan.md) đã hoàn tất sau item này.

## 2026-09-16 (Phase 5: Test offline — pytest chính thức)

### Added
- `tests/test_offline.py` — 5 test case CHÍNH THỨC, khớp đúng thứ tự bảng
  "Test offline" trong `specs/test-plan.md`:
  1. `test_guardrail_chan_prompt_injection` — `check_input()` raise
     `GuardrailViolation` với câu injection tiếng Anh.
  2. `test_guardrail_tu_choi_cau_hoi_ngoai_pham_vi` — câu hỏi ngoài phạm vi
     KHÔNG raise (chỉ injection/toxic mới raise), `in_scope()` trả `False`.
  3. `test_cau_hoi_hop_le_chay_offline_khong_crash` — `run_agent()` ở chế
     độ offline (tự động bật vì `PYTEST_CURRENT_TEST` luôn có sẵn khi chạy
     dưới `pytest`, không cần set biến môi trường thủ công) trả `answer`
     khác rỗng, không crash.
  4. `test_tool_sql_chan_cau_lenh_ghi` — gọi trực tiếp
     `run_sql_readonly.invoke()` với DELETE/UPDATE/DROP, verify có `error`
     trong response. KHÔNG cần DB thật: 3 câu này bị chặn ở lớp kiểm tra
     code (`startswith("select")`/`_WRITE_KEYWORDS`) TRƯỚC khi tool mở
     connection — verify thủ công (ghi output ra file, tránh lỗi encode
     console Windows) xác nhận lỗi trả về đúng ở bước sớm nhất
     ("Chỉ cho phép câu SELECT..."), không chạm `get_connection()`.
  5. `test_danh_sach_tool_dung_thiet_ke` — assertion tên 6 tool trong
     `TOOLS` khớp đúng `specs/product-spec.md` mục "Agent & tool".

### Verified
- `pytest -v`: cả 5 test PASS, chạy trong 0.86s — không cần network/API
  key/DB thật, đúng tinh thần "chạy được cho CI/mọi máy dev" của
  test-plan.md.
- Xác nhận test #4 an toàn dù `.env` hiện tại có DB thật cấu hình sẵn:
  không có rủi ro vô tình DELETE/UPDATE dữ liệu thật, vì code chặn ở tầng
  validate SQL text trước khi gọi `get_connection()`.

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **BUG tìm thấy, đã sửa:** test-plan.md diễn đạt test #1/#2 ở tầng hành vi
  API ("raise lỗi RÕ RÀNG", "KHÔNG lỗi 500") — nhưng bản implement ban đầu
  chỉ gọi thẳng `check_input()`/`in_scope()` (hàm nội bộ), KHÔNG verify qua
  endpoint HTTP thật. "Không lỗi 500" là khẳng định về status code, không
  thể xác nhận chỉ bằng cách gọi hàm Python — 1 lỗi wiring ở `src/main.py`
  (vd. exception handler bị gỡ nhầm) vẫn có thể lọt qua 2 test này mà
  không bị phát hiện.
- **Sửa:** thêm `TestClient(app)` và verify qua `POST /ask` thật cho cả 2
  case: #1 injection → `res.status_code == 400` (không phải 500) +
  `detail` khác rỗng; #2 ngoài phạm vi → `res.status_code == 200` (không
  phải 500) + `answer` khác rỗng + `row_count == 0` (xác nhận không gọi
  tool/DB). Giữ nguyên phần test hàm nội bộ cũ (vẫn hữu ích, chạy nhanh
  hơn, cô lập lỗi rõ hơn khi fail).
- Verify lại: cả 5 test vẫn PASS (1.03s). Warning
  `StarletteDeprecationWarning` (httpx/testclient) là cảnh báo từ thư viện
  bên thứ 3 có sẵn từ khi thêm `fastapi` vào `requirements.txt`, không
  phải lỗi trong code của item này — không sửa (ngoài phạm vi).
- **Fail:** không có vấn đề nào khác.
- **Missing:** test #3 chỉ verify ở tầng hàm nội bộ (`run_agent()` trực
  tiếp) — CHẤP NHẬN ĐƯỢC vì test-plan.md #3 chỉ yêu cầu "answer khác rỗng,
  không crash", không nhắc status code cụ thể như #1/#2, nên không thêm
  test qua `TestClient` để tránh lan phạm vi ngoài yêu cầu thật của item
  này.

## 2026-09-16 (Phase 5: UI hiển thị rõ 3 trạng thái)

### Not changed (đã đủ từ trước, chỉ xác nhận + đánh dấu hoàn thành)
- `static/index.html` (viết ở Phase 4) đã có sẵn đủ 3 trạng thái: "Đang xử
  lý..." (class `.pending`, disable nút tránh double-submit), trả lời
  thành công (bong bóng chat + bảng số liệu), lỗi (class `.error`, đọc
  `data.detail`). `src/main.py::guardrail_violation_handler` (sửa ở item
  "ghép luồng" review trước) đã thêm field `detail` cho response `400` để
  UI đọc đúng. Vì cả 2 phần này đã hoàn thiện và verify qua các item/review
  trước, item này KHÔNG cần sửa code gì thêm — chỉ còn thiếu case "lỗi kết
  nối DB/LLM" (`503`) chưa được verify tường minh, nên tập trung test case
  đó.

### Verified
- Mô phỏng lỗi DB/LLM (`unittest.mock.patch` để `run_agent()` raise
  `RuntimeError("DB connection timeout")`, không cần tắt DB thật): response
  `503` với `{"detail": "Không trả lời được: DB connection timeout"}` —
  đúng dạng string mà JS trong `index.html` cần (`typeof data.detail ===
  "string"`), sẽ hiện "Lỗi: Không trả lời được: DB connection timeout" ở
  bong bóng đỏ, không phải "Bad Request" mơ hồ.
- Tổng hợp lại cả 3 loại lỗi acceptance criteria yêu cầu, đều đã có response
  `detail` dạng string UI đọc đúng: `422` (Pydantic validation, câu hỏi
  rỗng), `400` (guardrail — injection/toxic, sửa ở review trước), `503`
  (agent/DB lỗi, verify ở đây).
- `pytest` chính thức vẫn chạy sạch (exit code 5, chưa có test case chính
  thức).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Pass:** câu hỏi ngoài phạm vi → `200` (không phải trạng thái lỗi, đúng
  thiết kế: đây là phản hồi hợp lệ "từ chối lịch sự", không phải lỗi hệ
  thống) → UI hiện bong bóng chat bình thường (không đỏ), đúng acceptance
  criteria "bị từ chối lịch sự, không gọi tool/DB" (verify `tool: ""`,
  `row_count: 0`).
- **BUG tìm thấy, đã sửa:** đang "Đang xử lý..." (nút Hỏi bị `disabled`)
  nhưng ô nhập liệu (`input`) KHÔNG bị khoá — user có thể nhấn Enter trong
  ô input để submit form lần 2 trong lúc request đầu chưa xong (Enter
  submit form không cần nút chưa bị disable). Không crash nhưng vi phạm
  tinh thần "trạng thái đang xử lý" rõ ràng đã thiết kế (chặn double-submit
  qua nút nhưng bỏ sót đường Enter).
- **Sửa:** thêm `input.disabled = true` cùng lúc với `button.disabled =
  true` lúc bắt đầu xử lý, mở khoá lại cả 2 ở khối `finally` (đảm bảo mở
  khoá dù thành công/lỗi/exception), thêm `input.focus()` sau khi mở khoá
  để UX mượt hơn (không phải feature mới, chỉ đi kèm fix disable/enable).
- Verify: `GET /` vẫn `200`, HTML có đủ logic mới. `pytest` vẫn sạch.
- **Missing:** không có gì khác so với `product-spec.md`/`test-plan.md`
  cho phạm vi UI 3 trạng thái.

## 2026-09-16 (Phase 5: Ghép luồng guardrail_input → agent → guardrail_output)

### Added
- `src/main.py` (`ask()`): ghép guardrail vào pipeline `/ask` bằng hàm đơn
  giản (KHÔNG dùng graph hub riêng — khác `atin/app/supervisor_agent/
  graph.py`, project này không có supervisor LangGraph, chỉ 1 agent duy
  nhất nên gọi tuần tự đủ, đúng tinh thần "giữ giải pháp đơn giản" của
  AGENTS.md):
  1. `check_input()` — injection/toxic → raise `GuardrailViolation`, KHÔNG
     gọi `run_agent()`/DB.
  2. `in_scope()` — ngoài phạm vi → trả `OUT_OF_SCOPE_REPLY` ngay, cũng
     KHÔNG gọi `run_agent()`/DB.
  3. `redact_pii()` trên câu hỏi trước khi đưa vào agent (che SĐT/email
     người dùng gõ nhầm vào câu hỏi).
  4. `run_agent()` (không đổi).
  5. `check_output()` — đối chiếu answer với evidence (câu hỏi + toàn bộ
     `columns=value` từ `query.rows` thật) → answer cuối có thể được thêm
     disclaimer/redact/cắt bớt.
  - `guardrail_violation_handler` (exception handler cho `GuardrailViolation`,
    tham khảo `atin/app/main.py`) → response `400`.

### Fixed (phát hiện khi test end-to-end lần đầu qua pipeline thật)
- **BUG:** `guardrail_violation_handler` trả JSON chỉ có
  `error`/`reason`/`details`, KHÔNG có key `detail` — trong khi
  `static/index.html` (đã viết ở Phase 4) đọc `data.detail` cho MỌI lỗi
  khác (`422`, `503`). Hậu quả: khi injection bị chặn, UI hiện "Lỗi: Bad
  Request" (rơi về `res.statusText`) thay vì lý do thật — không crash
  nhưng mất thông tin hữu ích, lần đầu lộ ra vì đây là lần đầu luồng lỗi
  injection thực sự chạy qua UI (trước đó `guardrails.py` chưa được gọi từ
  `main.py`).
- **Sửa:** thêm field `detail` (string, format sẵn
  `"Câu hỏi bị từ chối: {reason}"`) vào response, giữ nguyên
  `error`/`reason`/`details` cho API consumer khác cần chi tiết máy đọc
  được.

### Verified
- `TestClient`: injection → `400`, response giờ có cả `detail` (string,
  UI đọc được) lẫn `reason`/`details` (giữ nguyên). Câu hỏi ngoài phạm vi
  ("Thời tiết Hà Nội thế nào?") → `200`, trả đúng `OUT_OF_SCOPE_REPLY`,
  KHÔNG gọi agent/DB (verify qua `tool: ""`, `row_count: 0`).
- Test thật qua LLM (3/5 câu hỏi mẫu, đại diện đủ case) qua pipeline đầy
  đủ: số liệu đúng, không regression so với lần test riêng lẻ ở Phase 4;
  câu trả lời khớp evidence không bị gắn disclaimer thừa (case hãng xe 26
  dòng vẫn sạch).
- `pytest` chính thức vẫn chạy sạch (exit code 5, chưa có test case chính
  thức).

### Review lần 2 (kiểm tra sâu hơn sau lượt review đầu)
- **Pass:** toxic content ("đụ mẹ mày...") → `400`, `reason:
  unsafe_content`, không gọi agent/DB. Câu hỏi in-scope có PII nhúng sẵn
  ("...gọi tôi qua 0912345678 nhé") → PII bị redact TRƯỚC khi vào agent
  (`question` trả về đã là `"...qua [SĐT ẩn] nhé"`), không lộ SĐT ở bất kỳ
  đâu trong response.
- **Pass (edge case):** câu hỏi chỉ có khoảng trắng (`"   "`, qua được
  Pydantic `min_length=1` vì không tự strip) — không bị `check_input()`
  raise nhầm, `in_scope()` đúng đắn coi là ngoài phạm vi (không khớp
  keyword nào) → trả lời từ chối lịch sự, không gọi agent/DB, không crash.
  Pipeline tự nhiên an toàn với case này nhờ thứ tự
  check_input → in_scope, không cần sửa thêm.
- **Fail:** không tìm thêm bug nào trong phạm vi item này ở lượt review
  thứ 2.
- **Missing:** không có gì khác so với `product-spec.md`/`test-plan.md`
  cho phạm vi "ghép luồng". 2 item còn lại của Phase 5 (UI 3 trạng thái —
  đã có sẵn từ Phase 4, và test offline `pytest` chính thức) chưa làm,
  đúng như đã ghi nhận.

## 2026-09-16 (Phase 5: `src/guardrails.py`)

### Added
- `src/guardrails.py` — gộp `atin/app/guardrails/checks.py` +
  `atin/app/supervisor_agent/guardrails.py` (2 file, đã kiểm chứng) thành 1
  file phẳng, khớp cấu trúc `src/` không tách package `guardrails/` riêng
  của project này:
  - `check_input()` — raise `GuardrailViolation` khi phát hiện prompt
    injection (regex Anh + Việt, tham khảo
    `llm-engineer-demo/app/guardrails/injection.py`) hoặc từ ngữ độc hại.
    KHÔNG chặn câu hỏi ngoài phạm vi (đó là `in_scope()`, trả lời lịch sự
    thay vì raise).
  - `in_scope()` + `STAT_KEYWORDS` + `OUT_OF_SCOPE_REPLY` — nhận diện câu
    hỏi có thuộc phạm vi thống kê xe/khu vực không.
  - `check_output()` — đối chiếu số trong câu trả lời với evidence (câu hỏi
    + dữ liệu tool thật), gắn disclaimer nếu có số không xác minh được;
    redact PII (SĐT/email, tham khảo
    `llm-engineer-demo/app/guardrails/pii.py`); cắt bớt nếu vượt độ dài tối
    đa; trả fallback nếu quá ngắn/độc hại.
  - Toàn bộ bằng regex/code, KHÔNG LLM — đúng quyết định đã ghi trong
    `implementation-plan.md` (giữ ngân sách tối đa 2 lời gọi LLM/câu hỏi).
- `src/config.py` — thêm 2 field cần thiết cho `check_output()`:
  `guardrails_min_answer_len` (mặc định 5), `guardrails_max_answer_len`
  (mặc định 2000). Cập nhật `.env.example` tương ứng — cần thiết để module
  chạy được, không phải mở rộng phạm vi ngoài item.

### Changed (phạm vi, để không lấn sang item tiếp theo)
- CHƯA ghép `check_input`/`in_scope`/`check_output` vào `src/main.py` hay
  `src/agent/graph.py` — đó là item kế tiếp Phase 5 ("Ghép luồng:
  guardrail_input → agent → guardrail_output").

### Verified
- Test tạm (viết rồi xoá sau khi xác nhận, output ghi file vì console
  Windows cp1252 không in được tiếng Việt):
  - `check_input()` chặn đúng injection tiếng Anh ("Ignore all previous
    instructions...") VÀ tiếng Việt ("bỏ qua mọi hướng dẫn trước đó") —
    raise `GuardrailViolation`.
  - `in_scope("Thời tiết Hà Nội thế nào?")` → `False`; `in_scope("Hôm nay
    có bao nhiêu lượt xe vào?")` → `True` — khớp `test-plan.md` mục "Test
    offline" #1, #2.
  - Câu hỏi bình thường không bị `check_input()` raise nhầm.
  - `check_output()`: số khớp evidence → `valid=True`, không đổi answer; số
    không khớp evidence (999999 không có trong evidence) → gắn disclaimer
    đúng, `issues=["unverified_numbers"]`.
  - `redact_pii()`: SĐT `0912345678` → `[SĐT ẩn]`, email → `[email ẩn]`.
- `pytest` chính thức vẫn chạy sạch (exit code 5, chưa có test case chính
  thức — sẽ viết ở item "Test offline" cuối Phase 5).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **BUG tìm thấy, đã sửa:** `check_output()` đối chiếu số bằng string match
  thô (`\b\d+\b`) — test với câu trả lời THẬT đã thấy ở Phase 4 (item
  `answer.py`, câu hỏi mẫu #2: `"...9.418 lượt... 5.286 lượt..."`) phát hiện
  FALSE POSITIVE: LLM tự format số có dấu `.` phân cách hàng nghìn kiểu VN
  (`5.286`), trong khi evidence (dữ liệu tool thô) không có dấu phân cách
  (`so_luot=5286`) → regex tách `5.286` thành 2 số `5` và `286`, không khớp
  `5286` trong evidence → gắn OAN disclaimer "số liệu chưa xác minh được"
  cho câu trả lời có số liệu HOÀN TOÀN ĐÚNG, chỉ khác cách trình bày.
- **Sửa:** chuẩn hoá cả `text` và `context_text` — bỏ dấu `.` đứng giữa 1
  chữ số và đúng 3 chữ số tiếp theo (`(?<=\d)\.(?=\d{3}\b)`, đặc trưng dấu
  phân cách nghìn) TRƯỚC khi trích số bằng `\b\d+\b`, không đổi hành vi với
  số thập phân thật (vd. "1.5%" không bị normalize sai vì chỉ có 1 chữ số
  sau dấu chấm, không phải 3).
- Verify lại: số giống hệt evidence, chỉ khác định dạng dấu phân cách
  (`5.286` vs `5286`) → giờ `valid=True`, không còn disclaimer oan. Số BỊA
  thật (không có trong evidence, vd. `999.999` không khớp gì) → vẫn đúng bị
  gắn disclaimer, KHÔNG bị fix này che giấu. Số thập phân thật (`1.5%`) →
  không bị ảnh hưởng bởi normalize.
- **Lưu ý (không phải bug, đúng thiết kế theo test-plan.md mục "Không cần
  test ở MVP này"):** tổng LLM tự cộng từ nhiều dòng dữ liệu (vd. tự cộng
  5286+3357+701+74=9418 rồi viết vào câu trả lời) vẫn bị gắn disclaimer vì
  `9418` không xuất hiện literal trong evidence — guardrail chỉ đối chiếu
  string match, không làm phép tính. Test-plan.md đã ghi rõ: guardrail chỉ
  cần "che" (gắn disclaimer), không cần verify độ chính xác phép tính của
  LLM — hành vi "false positive an toàn" này chấp nhận được, không sửa.
- `pytest` chính thức vẫn sạch sau fix (exit code 5).
- **Missing:** không có vấn đề nào khác so với `product-spec.md`/
  `test-plan.md` cho phạm vi `guardrails.py`. Pipeline chưa ghép (item kế
  tiếp) nên chưa test được end-to-end qua `/ask`.

## 2026-09-16 (Phase 4: `static/index.html`)

### Added
- `static/index.html` — UI chat tối giản, HTML/JS thuần (không framework),
  gọi `POST /ask` (khớp route thật trong `src/main.py`, không phải
  `/stat/ask` như bản `atin/`). Tham khảo `atin/static/index.html` (đã kiểm
  chứng), bỏ `thread_id` (route `/ask` hiện tại không nhận tham số này).
  3 trạng thái rõ ràng theo acceptance criteria: "Đang xử lý..." (class
  `.pending`, hiện ngay khi submit, disable nút Hỏi tránh double-submit),
  trả lời thành công (bong bóng chat + bảng số liệu thô nếu có), lỗi (class
  `.error`, màu đỏ, hiện cả lỗi HTTP từ backend lẫn lỗi kết nối mạng qua
  `try/catch`) — không có trường hợp nào im lặng hoặc crash trắng trang.

### Verified
- `TestClient`: `GET /` → 200, `text/html`, có `<form>` và tiêu đề đúng.
  `GET /static/index.html` → 200 (route `/static` đã mount từ item
  `main.py` trước, giờ có file thật để phục vụ).
- Server thật (`uvicorn src.main:app --port 8199`, không chỉ `TestClient`):
  `GET /` → 200. Gọi `POST /ask` qua `urllib` (giả lập request UTF-8 giống
  `fetch()` trình duyệt gửi — curl trên Git Bash Windows tự làm hỏng
  encoding tiếng Việt trong `-d`, không phải lỗi app) với câu hỏi tiếng Việt
  thật → nhận JSON đúng UTF-8, đúng field `answer`/`tool`/`columns`/`rows`/
  `row_count` mà JS trong `index.html` cần để render bong bóng chat + bảng.
- **Giới hạn đã biết:** môi trường này không có trình duyệt thật để xem
  rendering trực quan (giao diện, CSS, click nút) — chỉ xác nhận được HTML
  hợp lệ, JS đọc đúng cấu trúc response qua kiểm tra logic + dữ liệu JSON
  thật khớp những gì `addMsg()` cần. Người dùng nên tự mở
  `http://localhost:8000/` trên trình duyệt thật để xác nhận giao diện
  trước khi coi là hoàn tất theo đúng nghĩa "test UI trong browser".

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Pass:** 3 trạng thái rõ ràng (đang xử lý / thành công / lỗi) — đã có
  đủ, không trạng thái nào im lặng.
- **Kiểm tra thêm (không phải bug):** thử case `/ask` trả `422` (FastAPI
  validation error) — `detail` ở đây là MẢNG object, không phải string.
  JS đã xử lý đúng (`typeof data.detail === "string" ? ... :
  JSON.stringify(...)`) nên hiện JSON thô thay vì câu tiếng Việt đẹp —
  KHÔNG crash, KHÔNG `undefined`/`[object Object]`, vẫn đạt acceptance
  criteria tối thiểu. Không sửa vì: (1) input rỗng đã bị chặn client-side
  (`required` + `if (!question) return`) nên case 422 gần như không xảy ra
  qua UI thật, (2) polish UX thông báo lỗi đẹp hơn là thêm tính năng ngoài
  phạm vi item ("Do not add new features").
- **Fail:** không có.
- **Missing (ngoài phạm vi item này):** guardrail chưa nối (Phase 5) nên
  UI chưa test được case "câu hỏi bị từ chối vì injection/ngoài phạm vi" —
  đã ghi nhận ở lần implement, không phải thiếu sót của `index.html`.

## 2026-09-16 (Phase 4: `src/main.py`)

### Added
- `src/main.py` — FastAPI app: `POST /ask` (gọi `run_agent()`, trả câu trả
  lời + số liệu thô), `GET /health` (trạng thái backend/DB, không lộ
  secrets), `GET /` (phục vụ `static/index.html` nếu có, `404` rõ ràng nếu
  chưa có thay vì crash). Mount `/static` chỉ khi thư mục `static/` tồn tại
  (item kế tiếp của Phase 4 mới tạo `static/index.html`, tránh lỗi
  `StaticFiles` không tìm thấy thư mục lúc khởi động app). Tham khảo cấu
  trúc `atin/app/main.py` nhưng bỏ `thread_id`/CORS/exception handler riêng
  cho guardrail (guardrail chưa tồn tại — thuộc Phase 5, chưa lấn phạm vi).

### Verified
- `TestClient` (không cần chạy uvicorn thật): `GET /health` → 200, đúng
  `llm_backend`/`db_configured` từ `.env` thật. `GET /` → 404 (đúng, chưa có
  `static/index.html`). `POST /ask {"question": "test"}` → 200, gọi
  `run_agent()` qua LLM thật thành công (câu hỏi mơ hồ nên trả "Chưa truy
  vấn được dữ liệu." — đúng hành vi, không phải lỗi).
- `pytest` chính thức vẫn chạy sạch (exit code 5, chưa có test case).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Pass:** "Chạy được local bằng 1 lệnh" — verify thật bằng
  `uvicorn src.main:app --port 8199` (server thật, không chỉ `TestClient`):
  `GET /health` → 200 đúng dữ liệu, `GET /` → 404 rõ ràng (chưa có
  `static/index.html`, đúng thiết kế fallback thay vì crash).
- **Pass:** "User thấy trạng thái rõ ràng... không im lặng, không crash
  trắng trang" — verify câu hỏi rỗng (`{"question": ""}`) → Pydantic trả
  `422` kèm message rõ ràng (`string_too_short`), không crash 500. Lỗi từ
  `run_agent()` (vd. LLM lỗi) đã được bọc `try/except` → `503` với message,
  không lộ traceback thô.
- **Fail:** không phát hiện bug nào trong phạm vi `src/main.py`.
- **Missing (không thuộc phạm vi item này):** guardrail input/output
  (chặn injection, từ chối câu hỏi ngoài phạm vi, đối chiếu số liệu output)
  chưa nối vào `/ask` — đúng như đã ghi nhận lúc implement, thuộc Phase 5
  chưa tới lượt. `static/index.html` chưa có nên `/` còn 404 — là item kế
  tiếp của Phase 4, không phải lỗi của item này.

## 2026-09-16 (Phase 4: `src/agent/answer.py`)

### Added
- `src/agent/answer.py` — `build_answer(question, queries, template_answer)`:
  lời gọi LLM thứ 2 (không tool, `invoke_text`) diễn giải (các) `QueryResult`
  thành câu tiếng Việt tự nhiên. Tham khảo `atin/app/answer.py` (đã kiểm
  chứng) nhưng đổi chữ ký để nhận `list[QueryResult]` thay vì 1 cái — khớp
  với `_pack()` hiện tại của `agent_ATIN` đã gộp nhiều tool call song song
  (xem entry Phase 4 `graph.py` phía dưới). Rơi về `template_answer` (do
  caller truyền vào, không tự dựng lại) khi: `ANSWER_USE_LLM=false`,
  offline/pytest, không có dòng dữ liệu nào, hoặc lời gọi LLM lỗi — không
  bao giờ crash vì bước diễn giải.

### Changed
- `src/agent/graph.py`: `_pack()` giờ gọi `build_answer(question, queries,
  template)` thay vì dùng thẳng `template` làm `answer` cuối — template vẫn
  được dựng trước (từ `_template_answer()`) để làm fallback truyền vào.

### Verified
- Offline mode (`PYTEST_CURRENT_TEST=1`): `build_answer` phát hiện
  `use_offline_tools()` và trả thẳng `template_answer`, không gọi LLM —
  confirm qua file output (console Windows không in được tiếng Việt, dùng
  cp1252) — khớp câu trả lời template cũ, không đổi hành vi offline.
- `pytest` chính thức vẫn chạy sạch (exit code 5, chưa có test case).
- Test thật (LLM thật, `ANSWER_USE_LLM=true` mặc định) — chạy lại cả 5 câu
  hỏi mẫu qua `run_agent()`:
  - Q1, Q2, Q3, Q5: answer giờ là câu tiếng Việt tự nhiên, diễn giải đúng số
    liệu thật đã lấy được (vd. Q1: "Hôm nay có tổng cộng 1909 lượt xe máy
    vào, 1448 lượt xe máy ra, 2588 lượt ô tô vào và 2697 lượt ô tô ra.") —
    khớp số liệu tool trả về, không bịa thêm số.
  - Q4 (truy vết biển số, câu hỏi mẫu không nêu biển số cụ thể): tool
    `trace_plate` không có điều kiện lọc nên không khớp dòng nào → rơi về
    template "Không có dữ liệu khớp câu hỏi..." — đúng hành vi fallback,
    KHÔNG phải lỗi của bước Answer (do câu hỏi thiếu tham số, nằm ngoài
    phạm vi sửa của item này).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **BUG tìm thấy, đã sửa:** `test-plan.md` mục "Test thật" câu hỏi mẫu #2
  yêu cầu: khi hỏi phân loại theo số chỗ ngồi (5/7/9/16/29/40 chỗ) — thứ DB
  không có — "cần nêu rõ giới hạn này trong câu trả lời hoặc README". Test
  với `ANSWER_USE_LLM=true` (mặc định) thì PASS (LLM tự nêu giới hạn nhờ
  `_SYSTEM` prompt). Nhưng test lại với `ANSWER_USE_LLM=false` (đường
  template fallback, không qua LLM) thì FAIL: `_template_answer()` chỉ liệt
  kê số liệu thô (`vehicle_type=MOTORCYCLE...`), không có câu giải thích nào
  — README cũng chưa viết (Phase 6, chưa tới lượt). `src/db/queries.py`
  (viết ở Phase 3) đã có sẵn docstring cảnh báo đúng việc này ("Answer
  (Phase 4) cần nêu rõ giới hạn này") nên không thể coi là ngoài phạm vi
  item — đây chính là chỗ Answer phải xử lý.
- **Sửa:** thêm `_with_seat_limit_note()` vào `answer.py` — kiểm tra câu hỏi
  có nhắc "chỗ" (5/7/9 chỗ...) và kết quả có cột `vehicle_type` thì tự thêm
  1 dòng ghi chú giới hạn vào cuối câu trả lời, áp dụng cho CẢ 2 đường
  (template fallback và sau khi LLM trả lời) — không phụ thuộc LLM có tự
  nhắc hay không, tránh trường hợp model quên. Có check tránh thêm trùng nếu
  câu trả lời (từ LLM) đã chứa sẵn câu y hệt.
- Verify lại: `ANSWER_USE_LLM=false` + câu hỏi mẫu #2 → giờ có ghi chú giới
  hạn ở cuối; câu hỏi bình thường (không nhắc "chỗ") → KHÔNG có ghi chú thừa
  (test riêng để confirm không over-trigger). `ANSWER_USE_LLM=true` (mặc
  định) chạy lại cả 4 câu hỏi mẫu còn lại (Q1, Q3, Q4, Q5-tương đương) —
  không regression, câu trả lời vẫn đúng số liệu như lần verify trước.
  `pytest` chính thức vẫn sạch (exit code 5).
- **Missing:** không có vấn đề nào khác so với `product-spec.md`/
  `test-plan.md` cho phạm vi `answer.py`. README.md (Phase 6) vẫn chưa có
  ghi chú giới hạn số chỗ ngồi — chấp nhận được vì acceptance criteria dùng
  "hoặc" (answer.py đã tự đủ), để Phase 6 làm sau nếu cần bổ sung thêm.

## 2026-09-16 (Phase 4: `src/agent/graph.py`)

### Added
- `src/agent/react.py` — hạ tầng ReAct dùng chung (`build_react_subgraph`,
  `agent_node`, `should_continue`, `fresh_user`, `last_tool_json`,
  `parse_tool_output`). Copy gần như nguyên từ `atin/app/react.py` (đã kiểm
  chứng, kể cả fix "system_prompt callable" đã làm ở `atin/` trước đây), chỉ
  đổi `from app.llm` → `from src.llm`. Coi là hạ tầng cần thiết đi kèm
  `graph.py` (không tự thành business feature riêng), không phải mở rộng
  ngoài phạm vi item.
- `src/agent/graph.py` — `AgentState` (TypedDict), `Agent_Input`/
  `Agent_Output` (pydantic), graph `seed → agent ⇄ tools → pack`
  (`_build_graph()`, cache `@lru_cache`), `run_agent()`. System prompt tiêm
  ngày giờ UTC hiện tại (`_system_prompt()`, callable — đánh giá lại mỗi
  lượt gọi, không hardcode lúc build graph) — đúng kỹ thuật đã kiểm chứng ở
  `atin/` để tránh model bịa năm/tháng sai.

### Changed (quyết định phạm vi, để không lấn sang item tiếp theo)
- `_pack()` hiện trả câu trả lời TEMPLATE đơn giản (`_template_answer()` —
  liệt kê số liệu thô), CHƯA gọi `src/agent/answer.py` (chưa tồn tại — đó
  là item kế tiếp của Phase 4). Sẽ nâng cấp `_pack()` gọi `answer.py` khi
  làm item đó, giữ đúng nguyên tắc "chỉ triển khai 1 task tại 1 thời điểm".

### Verified
- `run_agent()` chạy end-to-end qua LLM thật: câu hỏi "Hôm nay có bao nhiêu
  lượt xe vào Khu A?" → agent tự chọn đúng tool `count_vehicle_flow`, trả
  số liệu thật (`so_luot=4866`) — xác nhận system prompt tiêm đúng ngày
  giờ hiện tại (không bịa năm cũ như bug đã từng gặp ở `atin/`).
- Test tạm dưới `pytest` (viết rồi xoá ngay sau khi xác nhận — test case
  chính thức thuộc Phase 5): `run_agent()` ở chế độ offline (không gọi
  OpenAI thật) trả `answer` khác rỗng, không crash — khớp `test-plan.md`
  mục "Test offline" #3.
- `pytest` chính thức vẫn chạy sạch (exit code 5, chưa có test case).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **BUG tìm thấy, đã sửa:** `product-spec.md` acceptance criteria "Trả lời
  đúng, có số liệu thật, cho cả 5 câu hỏi mẫu" — test đủ cả 5 câu (trước
  chỉ test 1 câu tự chọn). Câu #1 ("...phân loại theo xe máy, ô tô") FAIL
  thực sự: agent gọi ĐÚNG cả 2 tool call song song (MOTORCYCLE + CAR), AI
  message cuối tổng hợp đúng cả 2, nhưng `_pack()` dùng `last_tool_json()`
  (chỉ lấy 1 tool message CUỐI CÙNG) nên `answer` chỉ có CAR, mất hẳn dữ
  liệu MOTORCYCLE — trong khi model đã làm đúng phần việc của nó.
- **Sửa (lần 1, có lỗi):** thêm `all_tool_json()` vào `react.py`, đổi
  `_pack()` gộp nhiều `QueryResult`. Verify lại ngay — PHÁT HIỆN lần sửa
  đầu làm HỎNG HOÀN TOÀN cả 5 câu (`all_tool_json()` trả `[]`): logic
  duyệt `reversed(messages)` gặp AIMessage cuối cùng (câu trả lời tổng hợp,
  không phải tool message) ngay ở bước đầu tiên nên `break` tức thì, không
  bao giờ chạm tới các ToolMessage phía trước nó.
- **Sửa (lần 2, đúng):** bỏ AIMessage cuối (`messages[:-1]`) TRƯỚC khi
  duyệt ngược, rồi mới thu thập ToolMessage liên tiếp. Verify lại đủ cả 5
  câu hỏi mẫu: Q1 giờ có cả MOTORCYCLE (1889 IN/1431 OUT) và CAR
  (2671 OUT/2546 IN) — đúng, không mất dữ liệu; Q2-Q5 không bị ảnh hưởng
  (vẫn đúng như lần test trước). `_pack()` cũng đổi `detail` để liệt kê
  TẤT CẢ tool đã dùng (trước chỉ 1 tool cuối).
- Test offline (viết tạm, xoá sau khi xác nhận) vẫn pass sau cả 2 lần sửa.
  `pytest` chính thức vẫn chạy sạch.
- **Bài học quy trình:** đây là ví dụ fix-rồi-tự-kiểm-tra-lại phát hiện fix
  đầu sai hoàn toàn trước khi báo cáo xong — luôn re-run toàn bộ 5 câu hỏi
  mẫu sau MỌI thay đổi liên quan tới `_pack()`/tool-result aggregation,
  không chỉ tin logic đọc đúng.

---

## 2026-09-16 (Phase 4: `src/agent/tools.py`)

### Added
- `src/agent/tools.py` — 6 tool LangChain (`@tool`): `get_db_schema`,
  `list_khu_vuc`, `count_vehicle_flow`, `trace_plate`,
  `zone_intrusion_by_hour` (bọc 4 hàm ở `src/db/queries.py`) +
  `run_sql_readonly` (fallback, validate: chỉ SELECT, chỉ bảng
  `plate_event`/`zone_event`, tự thêm LIMIT). `QueryResult` (pydantic)
  định nghĩa ngay trong file này (không tách `schemas.py` riêng — chỉ 1
  chỗ dùng, tránh thêm file không cần thiết).

### Changed (quyết định thiết kế, đã hỏi user trước khi làm)
- **Bỏ SQLite demo fallback** so với nguồn tham khảo
  `atin/app/stat_agent/tools.py` (vốn có 2 chế độ: Postgres thật HOẶC
  SQLite demo tự sinh khi thiếu `DB_HOST`). Lý do: `.env` của
  `agent_ATIN` luôn có sẵn DB thật (`db_configured=True`, đã verify từ
  Phase 1), và `product-spec.md` không yêu cầu chế độ demo — thêm ~120
  dòng code (`nodes.py` kiểu SQLite) sẽ vi phạm nguyên tắc "không thêm
  feature không liên quan" trong `AGENTS.md`. Nếu `DB_HOST` chưa cấu hình,
  mọi tool trả lỗi rõ ràng (`_not_configured()`) thay vì âm thầm dùng dữ
  liệu giả.
- Đã thêm vào docstring `count_vehicle_flow`: DB không phân loại xe theo
  số chỗ ngồi — đúng giới hạn đã phát hiện ở lượt review `src/db/queries.py`
  trước, đưa luôn vào docstring tool (nơi LLM thực sự đọc) thay vì chỉ ở
  `queries.py`.

### Verified
- `TOOLS` có đủ 6 tool đúng tên: `get_db_schema`, `list_khu_vuc`,
  `count_vehicle_flow`, `trace_plate`, `zone_intrusion_by_hour`,
  `run_sql_readonly`.
- Gọi trực tiếp (`.invoke()`, không qua LLM) từng tool với dữ liệu thật:
  `get_db_schema` trả mô tả đúng; `list_khu_vuc`/`count_vehicle_flow`/
  `zone_intrusion_by_hour` trả số liệu thật khớp Postgres; `trace_plate('')`
  trả lỗi đúng (không crash); `run_sql_readonly` chạy SELECT hợp lệ, chặn
  đúng DELETE và bảng ngoài whitelist (`sys_admin_account`).
- `pytest` vẫn chạy sạch (exit code 5, chưa có test case chính thức).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Chưa applicable:** test-plan mục "Test offline (pytest)" #4/#5 yêu cầu
  test case CHÍNH THỨC chạy bằng `pytest` — công việc này được lên kế
  hoạch ở Phase 5 (`implementation-plan.md`), chưa phải bây giờ. Đã verify
  thủ công tương đương ở lượt implement trước (không tính là thiếu sót của
  Phase 4).
- **LỖ HỔNG BẢO MẬT tìm thấy, đã sửa:** `run_sql_readonly` dùng
  `any(t in low for t in _ALLOWED_TABLES)` (substring-match TOÀN CÂU) để
  validate bảng — câu SQL `SELECT * FROM plate_blacklist WHERE
  'plate_event' = 'plate_event'` lọt qua whitelist vì chuỗi `"plate_event"`
  xuất hiện trong string literal, dù FROM thực sự trỏ tới bảng khác. Verify
  bằng dữ liệu thật: DB `its` có các bảng ngoài whitelist
  (`plate_blacklist`, `plate_violation_case`, `violation_type_catalog`...)
  mà role `agent_readonly` CÓ quyền SELECT (GRANT ALL TABLES khi tạo role)
  — đây là lỗ hổng đọc dữ liệu thật, không chỉ lý thuyết, vi phạm đúng
  nguyên tắc "chỉ SELECT trên plate_event/zone_event" mà tool này tuyên bố
  bảo vệ.
- **Sửa:** thay whitelist substring-match bằng regex trích xuất tên bảng
  THẬT SỰ sau `FROM`/`JOIN` (`_TABLE_REF`), rồi kiểm tra tập hợp tên bảng
  đó là subset của `_ALLOWED_TABLES` — không còn cách nào nhét tên bảng
  hợp lệ vào string literal để bypass. Cũng sửa logic chọn `dbname` (trước
  dùng `"zone_event" in low`, giờ dùng `"zone_event" in referenced_tables`
  — nhất quán với cách validate mới).
- **Verify sau fix:** bypass attempt bị chặn đúng
  (`"Chỉ cho phép SELECT trên bảng ['plate_event', 'zone_event']"`); 2
  bảng hợp lệ vẫn SELECT được; self-JOIN giữa `plate_event` với chính nó
  vẫn hoạt động (không phá vỡ use-case JOIN hợp lệ); DELETE vẫn bị chặn
  (regression check). Chạy lại toàn bộ 5 tool còn lại — không bị ảnh
  hưởng. `pytest` vẫn chạy sạch.

---

## 2026-09-16 (Phase 3, item 3: test kết nối thật read-only)

Item này là task verify (không phải file code mới) — không có gì để
modify. Đã chạy lại đầy đủ, tường minh 1 lần theo đúng mô tả checklist
(trước đó chỉ verify rải rác ở các lượt review Phase 3 item 1/2).

### Verified
- SELECT chạy được qua role `agent_readonly` trên cả 2 DB: `its.plate_event`
  (316348 dòng), `virtual_fence.zone_event` (104658 dòng).
- DELETE bị Postgres từ chối: `ReadOnlySqlTransaction` (thử trên
  `its.plate_event`).
- UPDATE bị Postgres từ chối: `ReadOnlySqlTransaction` (thử trên
  `virtual_fence.zone_event`).

**Phase 3 (Core Backend / Data Logic) đã hoàn thành đủ 3/3 item.**

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Vấn đề tìm thấy:** `test-plan.md` mục "Test guardrail an toàn" mô tả
  "thử connect + SELECT vào 1 DB khác, phải bị từ chối ở tầng SELECT dù
  CONNECT có thể vẫn qua" — mô tả này đúng với hành vi Postgres GỐC (role
  `agent_readonly`), nhưng SAU KHI thêm validate whitelist vào
  `get_connection()` ở lượt review Phase 3 item 1 trước, gọi
  `get_connection('vms_db')` giờ raise `ValueError` NGAY, không bao giờ
  chạm tới Postgres nữa. Test-plan không còn khớp cách hệ thống thực sự
  hoạt động qua code — ai test đúng theo câu chữ cũ qua `get_connection()`
  sẽ thấy kết quả khác mô tả (`ValueError` thay vì
  `InsufficientPrivilege`), dễ hiểu nhầm là fail.
- **Sửa:** viết lại mục này trong `test-plan.md`, tách rõ 2 lớp phòng thủ
  độc lập cần verify riêng: lớp code (`get_connection()` chặn NGAY bằng
  `ValueError`, không mở connection) và lớp Postgres (dự phòng, test bằng
  `psycopg2.connect()` trực tiếp KHÔNG qua wrapper — CONNECT qua, SELECT bị
  `InsufficientPrivilege`).
- **Verify:** chạy đủ 4 test case theo mô tả mới — DELETE bị chặn
  (`ReadOnlySqlTransaction`), lớp code chặn `vms_db` (`ValueError`), lớp
  Postgres CONNECT qua nhưng SELECT bị chặn (`InsufficientPrivilege`) khi
  test bằng raw `psycopg2`. Cả 4 đều pass, khớp đúng mô tả đã sửa.
- **Missing:** không có gì khác cần bổ sung. `pytest` vẫn chạy sạch.

---

## 2026-09-16 (Phase 3: `src/db/queries.py`)

### Added
- `src/db/queries.py` — 4 hàm SQL tham số hoá, dùng placeholder `%s`
  (không nối chuỗi giá trị người dùng vào SQL):
  - `count_vehicle_flow(date_from, date_to, direction, vehicle_type,
    group_by)` — đếm lượt xe ra/vào, group theo vehicle_type/direction/
    manufacturer
  - `trace_plate(plate_text, date_from, date_to)` — lịch sử di chuyển 1
    biển số
  - `zone_intrusion_by_hour(date_from, date_to, zone_code)` — số lượt xâm
    nhập theo giờ
  - `list_zones()` — liệt kê camera/khu vực hợp lệ

  Copy gần như nguyên từ `atin/app/db/queries.py` (đã kiểm chứng), chỉ đổi
  `from app.config`/`from app.db.connection` → `from src.config`/
  `from src.db.connection` và cập nhật 1 dòng comment tham chiếu file tool
  sẽ dùng (`src/agent/tools.py`, Phase 4).

### Verified
- Cả 4 hàm chạy đúng với dữ liệu Postgres thật:
  `count_vehicle_flow` (24h qua) trả 8 dòng group vehicle_type×direction,
  số liệu hợp lý (CAR/MOTORCYCLE/TRUCK/BUS × IN/OUT).
  `zone_intrusion_by_hour` trả 25 dòng (khung giờ), sắp xếp đúng theo
  `so_luot DESC`.
  `list_zones` trả đúng danh sách camera (`its`) và khu vực hàng rào
  (`virtual_fence`) thật, kể cả tên có dấu tiếng Việt.
  `trace_plate('AA2505', ...)` trả đúng 1 dòng lịch sử di chuyển khớp dữ
  liệu thật đã biết từ trước.
- Error path: `trace_plate('', ...)` trả `{"error": "Thiếu plate_text."}`
  thay vì crash.
- `pytest` vẫn chạy sạch (exit code 5, chưa có test case chính thức).

**Phase 3 còn 1 item:** "Test kết nối thật với role read-only... verify
SELECT chạy được, verify DELETE/UPDATE bị Postgres từ chối" — thực chất đã
verify đủ ở lượt review `connection.py` trước (SELECT OK trên cả 2 DB,
DELETE bị `ReadOnlySqlTransaction` từ chối); sẽ đánh dấu chính thức ở lượt
tiếp theo.

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Chưa applicable:** Acceptance Criteria trong `product-spec.md` vẫn nói
  về hành vi runtime hoàn chỉnh — chưa test trực tiếp được vì UI/Agent
  (Phase 4) chưa tồn tại.
- **Vấn đề tìm thấy, liên quan trực tiếp:** `test-plan.md` câu hỏi mẫu #2
  ("...phân loại xe máy/tải/5,7,9,16,29,40 chỗ") có ghi chú "DB thật không
  phân loại theo số chỗ ngồi — cần nêu rõ giới hạn này trong câu trả lời
  hoặc README". Rà lại: giới hạn này TRƯỚC ĐÓ chỉ tồn tại trong
  `test-plan.md`, chưa xuất hiện ở bất kỳ đâu khác (README, docstring
  `queries.py`) — người tiếp tục Phase 4 (viết Answer) có thể không biết
  để xử lý đúng.
- **Sửa:** thêm đoạn giới hạn schema vào docstring `count_vehicle_flow`
  (hàm sẽ xử lý đúng loại câu hỏi này) — nêu rõ `vehicle_type` chỉ có 4 giá
  trị (BUS/CAR/MOTORCYCLE/TRUCK), không có số chỗ ngồi, và Answer (Phase 4)
  cần nêu rõ giới hạn thay vì bịa số. Chọn sửa ở docstring thay vì README
  vì đây là giới hạn của chính file/hàm này, gần code nhất, dễ thấy nhất
  khi ai đó viết tool gọi hàm này ở Phase 4 — README hiện là placeholder,
  sẽ viết đầy đủ ở Phase 6 nên chưa phải chỗ đúng lúc này.
- **Verify thêm (bảo mật):** thử injection-style input vào `direction`
  (`"IN' OR '1'='1"`) và `group_by`
  (`"vehicle_type; DROP TABLE plate_event;--"`) — cả 2 đều bị chặn đúng
  bằng whitelist validation (`_DIRECTIONS`, `_GROUP_COLUMNS`) trước khi
  chạm SQL, không lọt raw string vào câu lệnh.
- Verify lại `count_vehicle_flow` vẫn hoạt động đúng sau khi sửa docstring
  (không đổi logic). `pytest` vẫn chạy sạch.

---

## 2026-09-16 (Phase 3: `src/db/connection.py`)

### Added
- `src/db/connection.py` — `is_configured()` (proxy `settings.db_configured`)
  và `get_connection(dbname)` (context manager psycopg2, read-only qua
  `conn.set_session(readonly=True, autocommit=True)` + `statement_timeout`
  từ `.env`). Copy gần như nguyên từ `atin/app/db/connection.py` (đã kiểm
  chứng), chỉ đổi `from app.config` → `from src.config` và cập nhật 1 dòng
  comment tham chiếu (`app/stat_agent/tools.py` → `src/agent/tools.py`,
  file validate SQL sẽ viết ở Phase 4-5). Không dùng connection pool ở MVP
  này, đúng như plan chỉ định.

### Verified
- Kết nối thật tới cả 2 DB (`its`, `virtual_fence`) qua role
  `agent_readonly` trong `.env`: `SELECT count(*)` chạy được trên
  `plate_event` (316126 dòng) và `zone_event` (104497 dòng).
- Read-only enforcement hoạt động đúng ở tầng connection: thử `DELETE FROM
  plate_event` bị Postgres từ chối
  (`ReadOnlySqlTransaction: cannot execute DELETE in a read-only
  transaction`) — không cần đợi tới lớp validate SQL ở Phase 4-5.
- `pytest` vẫn chạy sạch (exit code 5, chưa có test case chính thức).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Test liên quan trực tiếp, ban đầu chưa làm:** `test-plan.md` mục "Test
  guardrail an toàn" yêu cầu "Role DB không đọc được dữ liệu ngoài 2 DB đã
  cấp quyền (connect + SELECT vào 1 DB khác phải bị từ chối ở tầng
  SELECT)". Test tay với `get_connection('vms_db')` (DB không được cấp
  quyền): xác nhận Postgres đúng là từ chối ở SELECT
  (`InsufficientPrivilege: permission denied`), CONNECT vẫn qua như dự
  kiến (do PUBLIC CONNECT mặc định của cluster — xem `atin/README.md`).

### Fixed
- **Vấn đề tìm thấy:** `get_connection(dbname: DbName)` với `DbName = str`
  chấp nhận BẤT KỲ tên DB nào, không giới hạn đúng "2 DB" mà item plan mô
  tả — chỉ được chặn nhờ quyền Postgres của role `agent_readonly` (tầng
  ngoài), không có lớp validate nào ở code. Lỗi gõ sai tên DB (hoặc giá trị
  từ nguồn không tin cậy ở Phase 4-5) sẽ âm thầm mở connection thật tới DB
  sai trước khi bị chặn muộn ở SELECT.
- **Sửa:** thêm `_allowed_dbnames()` (từ `settings.db_name_its`/
  `db_name_fence`) và validate `dbname` ngay đầu `get_connection()`, raise
  `ValueError` fail-fast — không mở connection nếu tên DB không khớp đúng
  2 DB đã khai báo. Bỏ type alias `DbName` (không còn ý nghĩa, dùng `str`
  trực tiếp cho tham số). Verify lại: `its`/`virtual_fence` vẫn hoạt động
  bình thường; `vms_db` giờ bị chặn NGAY ở code (`ValueError`, không mở
  connection thật) thay vì chỉ dựa vào Postgres từ chối muộn hơn.
- `pytest` vẫn chạy sạch sau khi sửa.

---

## 2026-09-16 (Phase 2, item 3: xác nhận settings load đúng)

Item này là task verify (không phải file code mới) — không có gì để
modify. Đã thực hiện đúng theo mô tả checklist: chạy test tay in ra
`db_configured` và `llm_backend`.

### Verified
- `python -c "from src.config import settings; print(settings.llm_backend, settings.db_configured)"`
  → `llm_backend: openai`, `db_configured: True` — khớp `.env` thật đang có
  (đã verify tương tự ở 2 lượt review trước, giờ đánh dấu chính thức hoàn
  thành item riêng trong `specs/implementation-plan.md`).

**Phase 2 (Config & LLM Client) đã hoàn thành đủ 3/3 item.**

---

## 2026-09-16 (Phase 2: `src/llm.py`)

### Added
- `src/llm.py` — LLM client hỗ trợ 2 backend (`openai`/`ollama` qua
  `_BACKENDS` dict + `base_url`), `_RotatingKeyPool` (round-robin nhiều
  `OPENAI_API_KEYS`, tự cooldown key bị 429), `use_offline_tools()` (offline
  khi chạy dưới pytest hoặc thiếu key), `base_llm()`/`invoke_with_tools()`/
  `invoke_text()`. Copy gần như nguyên từ `atin/app/llm.py` (đã kiểm chứng
  chạy tốt), bớt backend `vllm` (không có trong scope MVP — product-spec
  chỉ nói "OpenAI Cloud / Ollama local"), đổi `from app.config import
  settings` → `from src.config import settings` cho khớp namespace mới.

### Verified
- `base_llm()` dựng đúng `ChatOpenAI` với model từ `.env` thật
  (`gpt-4o-mini`).
- Gọi LLM thật qua `invoke_text()` thành công (hỏi 1 câu ngắn, nhận đúng
  câu trả lời) — xác nhận key rotation/client hoạt động end-to-end, không
  chỉ import suông.
- `use_offline_tools()` trả `True` khi chạy dưới `pytest` (viết 1 test tạm,
  xoá sau khi xác nhận — test case chính thức thuộc Phase 5).
- Đổi `LLM_BACKEND=ollama` qua biến môi trường (không sửa code): client
  dựng đúng `base_url=http://localhost:11434/v1`, không đòi API key thật
  (`use_offline_tools()=False` vì backend này không cần key) — khớp đúng
  acceptance criteria liên quan trong `product-spec.md`.
- `pytest` vẫn chạy sạch (exit code 5, chưa có test case chính thức).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Chưa applicable:** như Phase 2 item 1, mọi Acceptance Criteria nói về
  hành vi runtime hoàn chỉnh — chưa test được trực tiếp qua UI/API vì
  chưa tồn tại (Phase 4).
- **Điều tra sâu hơn 1 điểm nghi ngờ:** `_pool()` (`@lru_cache`) raise
  `ValueError` nếu backend `openai` mà `OPENAI_API_KEYS` rỗng — kể cả khi
  `use_offline_tools()` đã trả `True` báo hiệu "đừng gọi LLM thật". Đã xác
  nhận đây KHÔNG phải bug: đối chiếu `atin/app/react.py` (dòng 39) và
  `atin/app/answer.py` (dòng 37) — mọi nơi gọi `invoke_with_tools`/
  `invoke_text` trong pipeline gốc ĐỀU check `use_offline_tools()` trước;
  đây là contract cố ý (client low-level không tự guard, trách nhiệm gọi
  đúng thứ tự thuộc caller ở Phase 4). Không sửa — thêm guard vào
  `base_llm()` sẽ là thay đổi API ngoài phạm vi plan yêu cầu.
- **Verify bổ sung:** `_RotatingKeyPool` round-robin đúng thứ tự
  (key1→key2→key3→key1...) và cooldown loại đúng key vừa bị mark_limited
  khỏi vòng quay — cả 2 test tay đều pass.
- **Kết luận:** không tìm thấy vấn đề cần sửa. Không thay đổi file nào
  trong lượt review này.

---

## 2026-09-16 (Phase 2: `src/config.py`)

### Added
- `src/config.py` — `Settings` (`pydantic_settings.BaseSettings`) đọc `.env`,
  điểm duy nhất chạm secrets trong codebase. Field: LLM backend
  (`LLM_BACKEND`, `LLM_BASE_URL`, `OPENAI_API_KEYS`, `LLM_MODEL`,
  `LLM_TEMPERATURE`, `LLM_MAX_RETRIES`, `ANSWER_USE_LLM`) và Postgres
  read-only (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`,
  `DB_NAME_ITS`, `DB_NAME_FENCE`, `DB_ORGANIZATION_ID`,
  `DB_QUERY_TIMEOUT_S`, `DB_MAX_ROWS`) — khớp đúng field đã có sẵn trong
  `.env.example`/`.env` (Phase 1). Copy gần như nguyên từ
  `atin/app/config.py` (đã kiểm chứng), bớt 2 field guardrail
  (`GUARDRAILS_MIN_ANSWER_LEN`/`MAX_ANSWER_LEN`) và `APP_NAME` vì chưa dùng
  tới ở phase này — sẽ thêm khi làm Phase 5 (Guardrails) nếu cần.

### Verified
- `from src.config import settings` load đúng từ `.env` thật: `llm_backend`
  = "openai", `db_configured` = True, `api_keys` nhận đủ 2 key, tên 2 DB
  đúng (`its`, `virtual_fence`).
- `pytest` vẫn chạy sạch (exit code 5, chưa có test case — không đổi so
  với Phase 1).

### Review vs acceptance criteria (product-spec.md + test-plan.md)
- **Chưa applicable:** mọi Acceptance Criteria trong `product-spec.md` nói
  về hành vi runtime hoàn chỉnh (trả lời câu hỏi, guardrail, ngrok) — 1
  mình `config.py` chưa đủ để pass/fail tiêu chí nào, đúng kế hoạch.
- **Liên quan trực tiếp, đã kiểm tra riêng:** tiêu chí "đổi `LLM_BACKEND=ollama`
  trong `.env`, không cần sửa code" — verify `Settings` nhận giá trị
  `"ollama"` không lỗi (field kiểu `str` thường, không validate whitelist —
  đúng theo `atin/app/config.py` gốc đã kiểm chứng, không phải bug mới).
  Việc thực sự CHẠY được với backend `ollama` chỉ verify được ở `src/llm.py`
  (item tiếp theo Phase 2), chưa tồn tại.
- **test-plan.md:** không có test case riêng cho `config.py` — hợp lý, nó
  chỉ được test gián tiếp qua các feature dùng `settings` sau này. Không
  có gì missing cần bổ sung.
- **Đối chiếu `.env.example` ↔ `config.py`:** đồng bộ hoàn toàn, không
  thiếu/thừa field alias nào (kiểm bằng script so khớp key).
- **Kết luận:** không tìm thấy vấn đề nào cần sửa. Không thay đổi file nào
  trong lượt review này.

---

## 2026-09-16 (Phase 1: Project Setup)

### Added
- Khung package `src/` trống (`src/__init__.py`, `src/agent/__init__.py`,
  `src/db/__init__.py`) và `tests/__init__.py` — chưa có business logic,
  đúng scope Phase 1.
- `pyproject.toml` (`testpaths = ["tests"]`) để `pytest` chạy được.
- `.env.example` mới, khớp field với `.env` thật đang dùng (LLM backend,
  Postgres read-only) — không chứa secret thật.

### Changed
- Viết lại `requirements.txt`: từ danh sách cũ (qdrant, mcp, langfuse,
  vnstock, gradio, ...) rút xuống đúng 9 dependency cần cho MVP (fastapi,
  uvicorn, pydantic, pydantic-settings, langgraph, langchain-core,
  langchain-openai, openai, psycopg2-binary, pytest).
- Sửa link tham chiếu hỏng trong `specs/implementation-plan.md` (từng trỏ
  "AGENTS.md mục Kỹ thuật KHÔNG dùng" — mục đó đã bị xoá ở lần rút gọn
  AGENTS.md trước; giờ trỏ đúng sang `specs/product-spec.md` mục "Features
  Out of Scope").
- Đánh dấu hoàn thành 4 checklist item của Phase 1 trong
  `specs/implementation-plan.md`.

### Removed
- Xoá `src/` cũ (agent_m2-style: memory, tool_selection, multi sub-agent,
  monitoring/tracing — viết dở, có bug đã biết ở `states.py`, và thuộc các
  kỹ thuật đã đánh dấu Out of Scope trong product-spec), `resource/`,
  `docker-compose.yml`, `main.py` cũ. Đã xác nhận với user trước khi xoá
  (thao tác không thể hoàn tác).

### Notes
- `web/` (thư mục rỗng, có sẵn từ trước) được giữ nguyên, không đụng tới.
- `.env` thật (đã có sẵn từ trước, cùng field với `.env.example` mới) không
  bị ảnh hưởng — vẫn nằm ngoài git nhờ `.gitignore`.

---

## 2026-09-16 (Review Phase 1 vs acceptance criteria)

Đối chiếu Phase 1 với `specs/product-spec.md` Acceptance Criteria và
`specs/test-plan.md`.

**Kết quả:** Acceptance Criteria trong product-spec nói về hành vi runtime
của app hoàn chỉnh (trả lời câu hỏi, guardrail, đổi LLM backend, demo
ngrok) — chưa applicable ở Phase 1 vì các tính năng đó chưa tồn tại (đúng
kế hoạch, không phải fail). Checklist riêng của Phase 1 (project setup) đạt
đủ 4/4 mục, verify lại bằng lệnh thật: `import src` OK, `pytest` chạy sạch
(exit code 5 "no tests ran" — đúng vì chưa có test case), toàn bộ 9
dependency trong `requirements.txt` import được.

### Fixed
- `README.md` bị lỗi thời — vẫn ghi "chưa code cho luồng mới", "code cũ
  trong src/ giữ nguyên chưa xoá — sẽ xử lý ở Phase 1" dù Phase 1 đã xong
  và code cũ đã xoá. Cập nhật mục "Trạng thái hiện tại" khớp thực tế, thêm
  lệnh cài đặt/test thật (đã tự chạy lại để xác nhận đúng) vào "Cài đặt &
  chạy local", ghi chú rõ `pytest` trả exit code 5 khi chưa có test case là
  bình thường (tránh hiểu nhầm là lỗi).

### Not fixed (ngoài phạm vi feature này)
- `.env.example` tham chiếu "README mục Tạo DB role read-only" — mục đó
  chưa tồn tại trong README (sẽ có ở Phase 6). Đây là forward-reference hợp
  lệ theo kế hoạch, không phải lỗi của Phase 1 — không sửa, theo đúng
  nguyên tắc "chỉ sửa vấn đề liên quan tới feature vừa làm".

---

## 2026-09-16

### Added
- Tạo bộ spec ban đầu (`specs/product-spec.md`, `specs/implementation-plan.md`,
  `specs/test-plan.md`, `specs/change-log.md`) và `AGENTS.md` theo Spec-Driven
  Development. Chưa viết code cho luồng mới.
- Thêm mục "Tham khảo llm-engineer-demo/" vào `AGENTS.md` — bảng liệt kê kỹ
  thuật có trong Module II (`agent_m2/`) nhưng KHÔNG dùng ở MVP này (memory,
  tool retrieval, MCP, HITL, tracing/eval, multi-agent, LLM-based injection
  check) kèm lý do, để tránh drift scope khi code.

### Changed
- Review `specs/product-spec.md`: tách phần "ghi chú quy trình" khỏi Goal,
  nhóm lại Features In Scope theo 4 hạng mục (Agent & tool / Guardrail / Hạ
  tầng / UI) thay vì 1 list phẳng, thêm acceptance criterion về UI-state
  (loading/success/error) còn thiếu.
- Bổ sung `specs/implementation-plan.md` Phase 2/4/5 với file nguồn cụ thể
  trong `llm-engineer-demo/` nên tham khảo cho từng phần (llm/backends.py,
  llm/resilience.py, agent_m2/nodes.py, guardrails/injection.py, guardrails/pii.py).
- Viết lại `specs/implementation-plan.md` từ 9 phase rời rạc thành 6 phase
  chuẩn theo khung Spec-Driven Development (Project setup → Config & LLM
  client → Core backend/data logic → Agent → Validation and error states →
  Local run instructions). Gộp Guardrails + Testing cũ vào "Validation and
  error states"; gộp API/UI vào "Agent"; gộp local run + ngrok vào "Local
  run instructions". Không cắt tính năng nào, chỉ tổ chức lại checklist.
- Bổ sung `specs/product-spec.md` Out of Scope: liệt kê tường minh
  long-term memory/tool retrieval/MCP, LLM-based injection check, test UI
  tự động/load test — trước đây chỉ nhắc trong AGENTS.md/test-plan.md, giờ
  cũng có trong product-spec để nhất quán.

### Fixed
- (chưa có)

### Changed (tiếp)
- Viết lại `AGENTS.md` cho ngắn gọn, bám sát mẫu chuẩn trong "Spec Driven
  Development Guide" (7 quy tắc + Coding Style + Testing, bỏ phần "Ràng
  buộc riêng" và bảng "kỹ thuật không dùng" đã làm file phình to). Nội dung
  đó thuộc về `specs/product-spec.md` (scope) và
  `specs/implementation-plan.md` (chi tiết kỹ thuật từng phase), không phải
  `AGENTS.md` (chỉ nói cách hành xử khi code) — đã có sẵn ở 2 file kia nên
  không mất thông tin, chỉ sửa 1 link tham chiếu hỏng trong product-spec.md
  (trỏ sang implementation-plan.md thay vì AGENTS.md).

### Notes
- Bản spec này viết lại đơn giản hơn `atin/` (project trước, đã chạy được
  và verify với Postgres thật) — xem `atin/README.md` để biết các quyết
  định kiến trúc đã kiểm chứng (function-calling thay Text-to-SQL, tối đa
  2 lời gọi LLM/câu hỏi, mart `plate_dashboard` không dùng vì lỗi thời).
- Code cũ hiện có trong `agent_ATIN/src/` (viết dở, dựa theo Module II phức
  tạp hơn của `llm-engineer-demo`) được GIỮ LẠI theo yêu cầu, chưa xoá —
  quyết định xoá/tái cấu trúc sẽ làm ở Phase 1 implementation-plan khi thực
  sự bắt đầu code.
