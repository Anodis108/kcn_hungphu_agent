# Test Plan

## Nguyên tắc
- Test offline (không cần API key/DB thật) chạy được bằng `pytest`, dùng
  cho CI/mọi máy dev.
- Test thật (cần `.env` có DB Postgres + LLM key) chạy tay, dùng để xác nhận
  5 câu hỏi mẫu trong "Ý tưởng Agent.docx" trả lời đúng số liệu thật.

## Test offline (pytest, không cần Postgres/API key)

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | Guardrail chặn prompt injection ("Ignore previous instructions...") | Raise lỗi rõ ràng, không gọi agent |
| 2 | Guardrail chặn câu hỏi ngoài phạm vi ("Thời tiết Hà Nội thế nào?") | Trả lời từ chối lịch sự, không lỗi 500 |
| 3 | Câu hỏi hợp lệ chạy offline (không có API key) | Trả về answer khác rỗng, không crash |
| 4 | Tool SQL đọc-only chặn câu lệnh ghi (DELETE/UPDATE/DROP) | Trả lỗi rõ ràng, không thực thi |
| 5 | Danh sách tool đúng như thiết kế (đủ tool cần, không thiếu) | Assertion tên tool khớp |

## Test thật (chạy tay, cần `.env` đầy đủ)

Dùng đúng 5 câu hỏi mẫu trong tài liệu gốc:

| # | Câu hỏi | Acceptance |
|---|---|---|
| 1 | "Biểu đồ hôm nay có bao nhiêu lượt xe ra và vào, phân loại theo xe máy, ô tô" | Trả lời có số liệu cho cả 2 loại xe, khớp dữ liệu thô trả về |
| 2 | "Biểu đồ thống kê hôm nay có bao nhiêu lượt ra vào, phân loại xe máy/tải/5,7,9,16,29,40 chỗ" | Trả lời phân loại đúng theo `vehicle_type` có trong DB (BUS/CAR/MOTORCYCLE/TRUCK — lưu ý DB thật không phân theo số chỗ ngồi, cần nêu rõ giới hạn này trong câu trả lời hoặc README) |
| 3 | "Số liệu ô tô theo hãng xe trong hôm nay" | Trả lời liệt kê hãng xe + số lượt, khớp `manufacturer` trong DB |
| 4 | "Truy vết, lịch sử di chuyển của phương tiện có biển số XXXX" | Trả lời đúng camera/thời điểm/chiều ra-vào của biển số đó (thay XXXX bằng biển số có thật trong DB khi test) |
| 5 | "Khung thời gian xảy ra xâm nhập nhiều nhất ngày hôm nay" | Trả lời đúng khung giờ có số lượt cao nhất, khớp dữ liệu `zone_event` |

## Test guardrail an toàn (chạy tay hoặc pytest)
- Role DB dùng để kết nối KHÔNG có quyền ghi (verify bằng thử `DELETE`/`UPDATE`
  trực tiếp qua `src/db/connection.py::get_connection()`, phải bị Postgres
  từ chối — `ReadOnlySqlTransaction`).
- 2 lớp phòng thủ độc lập chặn đọc dữ liệu ngoài phạm vi — verify cả 2:
  - **Lớp code** (`get_connection()`): gọi với `dbname` không phải
    `its`/`virtual_fence` (vd. `"vms_db"`) phải raise `ValueError` NGAY,
    không mở connection thật.
  - **Lớp Postgres** (role `agent_readonly`, dự phòng nếu lớp code bị bỏ
    qua/lỗi): test bằng `psycopg2.connect()` trực tiếp (KHÔNG qua
    `get_connection()`) vào 1 DB khác — CONNECT vẫn qua (PUBLIC CONNECT mặc
    định của cluster) nhưng SELECT phải bị từ chối
    (`InsufficientPrivilege`).

## Không cần test ở MVP này
- Load test / nhiều người dùng đồng thời.
- Test UI tự động (chấp nhận test tay qua trình duyệt).
- Test độ chính xác của LLM diễn giải câu trả lời (chỉ cần không hallucinate
  số liệu ngoài dữ liệu tool trả về — guardrail output đã che phần này).

---

## Test domain sự kiện VMS mới (Phase 2/3/5/6 trong implementation-plan.md — chưa code, ghi kế hoạch trước)

### Test offline (không cần Postgres/API key thật)
| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `count_anomaly_events(event_type="LOI_BIA")` (event_type ngoài whitelist) | Trả `error` rõ ràng, không query DB — giống cách `run_sql_readonly` validate bảng ở v1 |
| 2 | Danh sách tool mới đúng như thiết kế (`count_face_events`, `count_fire_smoke_events`, `count_anomaly_events`) | Assertion tên tool khớp `product-spec.md` |
| 3 | `in_scope()` nhận đúng câu hỏi domain mới (vd. "Hôm nay có vụ ẩu đả nào không?") | Trả `True` — verify `STAT_KEYWORDS` đã mở rộng đủ, không bị từ chối oan |
| 4 | `get_connection()` với `dbname` ngoài 5 DB hợp lệ (2 cũ + 3 mới) | Raise `ValueError` ngay, không mở connection — giống test guardrail DB ở v1 |

### Test guardrail an toàn (2 lớp — KHÁC cơ chế nhau, đừng lẫn lộn)
- **Lớp Postgres/GRANT** (verify được NGAY sau khi tạo role — không cần
  đợi Phase 3): connect trực tiếp bằng `psycopg2.connect()` (KHÔNG qua
  `get_connection()`, vì whitelist DB trong code chưa có 3 DB mới) tới
  từng DB `smart_face`/`firesmoke`/`anomaly` bằng `agent_readonly` — verify
  SELECT chạy được, verify DELETE/UPDATE bị từ chối với
  **`InsufficientPrivilege`** (KHÔNG phải `ReadOnlySqlTransaction` — lỗi
  đó chỉ xảy ra qua `conn.set_session(readonly=True)` trong
  `get_connection()`, tầng app chưa hỗ trợ 3 DB này).
- **Lớp app/session-readonly** (chỉ verify được SAU Phase 3, khi
  `get_connection()` đã mở whitelist cho 3 DB mới): gọi qua
  `get_connection()` thật rồi thử DELETE/UPDATE — lúc đó mới đúng kỳ vọng
  `ReadOnlySqlTransaction`, giống pattern v1 (`its`/`virtual_fence`).
- Lớp code (`get_connection()`) chặn `dbname` lạ NGAY, không phụ thuộc
  hoàn toàn vào quyền Postgres — verify lại sau khi mở rộng whitelist
  (đảm bảo mở rộng đúng 3 DB mới, không vô tình mở rộng quá tay).

### Test thật (chạy tay, cần `.env` đủ 5 DB + role read-only)
Tối thiểu 1 câu hỏi mẫu / domain mới (8 domain − 3 đã test ở v1 = 5 domain
cần câu hỏi mới):

| # | Câu hỏi | Acceptance |
|---|---|---|
| 1 | "Hôm nay có bao nhiêu lượt nhận diện khuôn mặt?" | Số liệu thật từ `smart_face.smf_face_events`, khớp `rows` |
| 2 | "Hôm nay có vụ ẩu đả nào không?" | Đúng `count_anomaly_events(event_type=FIGHT_DETECTION)`, không nhầm sang domain khác |
| 3 | "Hôm nay có cảnh báo đám đông ở khu vực nào không?" | Đúng `event_type=CROWD_DETECTION` |
| 4 | "Hôm nay có phát hiện leo trèo không?" | Đúng `event_type=INTRUSION_DETECTION` trên `anomaly.anomaly_event` — KHÔNG bị nhầm với `zone_intrusion_by_hour` (vùng cấm, bảng khác) |
| 5 | "Hôm nay có cảnh báo cháy hoặc khói không?" | Đúng `firesmoke.fire_smoke_event`, phân biệt được `entity_type` FIRE/SMOKE |
| 6 | "Mực nước hôm nay có vượt ngưỡng cảnh báo không?" | Đúng `event_type=WATER_LEVEL_DETECTION`, đọc được `payload.water_level`/`warning_threshold` |

### Test golden dataset v2 (30 case)
- `eval/run.py` chạy hết 30 case trong `eval/datasets/agent_stat/v2.yaml`
  → in được tỷ lệ pass/fail theo `slice.type` (lookup/comparison/
  out_of_scope/injection).
- So với v1: 3 case `out_of_scope` + 3 case `injection` PHẢI vẫn pass
  nguyên (không regression khi mở rộng `STAT_KEYWORDS`/tool) — đây là tín
  hiệu regression rõ nhất nếu mở rộng guardrail sai cách.

## Test Langfuse tracing (Phase 4/5/6 trong implementation-plan.md)

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `MONITORING_ENABLED=false` (mặc định), chạy `pytest -v` | Kết quả y hệt trước khi thêm tracing (không cần Langfuse chạy, không import lỗi nếu thiếu package) |
| 2 | `MONITORING_ENABLED=true`, Langfuse self-host đang chạy, gọi `POST /ask` thật | Trace xuất hiện trong Langfuse UI với input/output/latency; có span con cho bước chọn tool + bước diễn giải |
| 3 | Kiểm tra nội dung trace không lộ secret | Không thấy `OPENAI_API_KEYS`/`DB_PASSWORD` trong bất kỳ trường nào của trace (input/output/metadata) |
| 4 | `MONITORING_ENABLED=true` nhưng Langfuse service down | `/ask` vẫn trả lời bình thường (không crash vì lỗi kết nối Langfuse) — verify lỗi trace bị nuốt/log, không raise lên response |

## Test Prompt Registry (chưa có phase kế hoạch cụ thể — xem ghi chú cuối implementation-plan.md)

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `PromptRegistry.get("answer", version=1)` | Trả đúng nội dung `prompts/answer/v1.yaml` |
| 2 | `PromptRegistry.render("answer", version="production", question=..., context=...)` thiếu 1 biến bắt buộc | Raise lỗi rõ ràng ("Thiếu biến khi render prompt"), không âm thầm render thiếu |
| 3 | Đổi `prompts/answer/production.txt` từ `"1"` sang `"2"` (không sửa code) | `run_agent()`/`build_answer()` dùng ngay nội dung v2 ở lượt gọi tiếp theo |
| 4 | Revert `production.txt` về `"1"` | Hành vi quay lại y hệt trước khi đổi — xác nhận rollback = revert 1 file |
| 5 | `pytest` offline trong suốt quá trình thêm registry | Vẫn chạy sạch — registry đọc file tĩnh, không phụ thuộc LLM/DB thật khi ở chế độ offline |
