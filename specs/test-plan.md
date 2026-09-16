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
