# AGENTS.md

Project này tuân theo spec-driven development đơn giản.

## Rules

1. **Luôn đọc `/specs` trước khi code** — đặc biệt `implementation-plan.md`
   (từ Phase 2 trở đi có ghi vài giả định CHƯA verify, vd. DB host dùng
   chung, quyền role Postgres — nếu code thực tế cho thấy giả định sai,
   dừng lại và cập nhật spec trước, không âm thầm đổi hướng).
2. **Chỉ triển khai 1 phase hoặc 1 task tại 1 thời điểm** — không gộp
   nhiều phase/task vào cùng 1 lượt.
3. **Giữ app đơn giản** — không over-engineer, không thêm feature/tham số
   ngoài yêu cầu của task đang làm.
4. **Không thêm thư viện mới nếu chưa thực sự cần.**
5. **Không đổi kiến trúc trừ khi spec đã được cập nhật trước** —
   `specs/product-spec.md`/`specs/implementation-plan.md` phải phản ánh
   thay đổi TRƯỚC khi code theo hướng đó.
6. **Sau mỗi lần triển khai, cập nhật `specs/change-log.md`.**
7. **Sau mỗi lần triển khai, giải thích cách test thay đổi** — lệnh chạy
   app, các bước test thủ công, issue đã biết (nếu có).
