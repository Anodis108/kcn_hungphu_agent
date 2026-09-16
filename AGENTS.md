# AGENTS.md

Project này tuân theo simple spec-driven development.

## Nguyên tắc chính
Luôn đọc các file trong `/specs` trước khi code.

## Workflow
Với mỗi task:
1. Đọc các file spec liên quan.
2. Chỉ triển khai một task hoặc một phase tại một thời điểm.
3. Giữ giải pháp đơn giản.
4. Tránh thêm thư viện không cần thiết.
5. Không thay đổi architecture trừ khi spec được cập nhật.
6. Sau khi triển khai, cập nhật `specs/change-log.md`.
7. Giải thích cách test thay đổi.

## Coding Style
- Ưu tiên code đơn giản, dễ đọc.
- Không over-engineer.
- Không thêm feature không liên quan.
- Giữ thay đổi nhỏ và dễ review.

## Testing
Trước khi nói task đã hoàn thành, hãy cung cấp:
- command để chạy app
- các bước test thủ công
- các issue đã biết nếu có
