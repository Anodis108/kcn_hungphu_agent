# AUDIT-CHECKLIST — Kiểm toán Case Draft & Go-Live (Phụ lục C/H rút gọn)

Tài liệu hướng dẫn kiểm toán viên / chuyên viên thẩm định khi duyệt các test case nháp sinh ra từ luồng phản hồi tiêu cực (`draft-<date>.yaml` qua `scripts/feedback_to_golden.py`) trước khi gán nhãn, chuẩn hóa, và merge vào Golden Dataset chính thức phiên bản tiếp theo (`v+1.yaml`), đồng thời đối chiếu các tiêu chí Go-Live trọng yếu.

> [!NOTE]
> **Phạm vi & Giới hạn**: Rút gọn từ Phụ lục C (4 Trụ cột Go-Live) và Phụ lục H (6 Đường nối hay vỡ) trong *Quy trình Xây dựng Agent Product*.
> **Loại trừ (Non-goal v19)**: **Không** bao gồm canary rollout / beta testing rollout (theo quyết định phê duyệt v19 Non-goals).

---

## 1. Quy trình duyệt Case Draft từ Thumbs-Down (`draft-<date>.yaml`)

Mỗi case trong file draft sinh tự động từ `scripts/feedback_to_golden.py` ban đầu có trạng thái `review: pending` và các trường `slice` để trống. Người duyệt thực hiện tuần tự các bước kiểm toán sau cho từng case:

- [ ] **1.1. Thẩm định tính hợp lệ của câu hỏi (`question`)**:
  - Xác nhận câu hỏi xuất phát từ nhu cầu nghiệp vụ thực tế của người dùng.
  - Loại bỏ các câu hỏi spam, rác, hoặc câu hỏi không mang ý nghĩa ngữ cảnh.
  - Nếu là câu hỏi tấn công (Jailbreak / Prompt Injection), chuyển sang phân loại `slice.type: injection`.
- [ ] **1.2. Phân loại Slice nghiệp vụ (`slice.type`)**:
  - Gán chính xác một trong các loại slice:
    - `lookup`: Tra cứu số liệu thống kê đơn lẻ (1 tool call).
    - `comparison`: So sánh, tổng hợp nhiều mốc thời gian hoặc đa chặng (multi-hop).
    - `out_of_scope`: Câu hỏi ngoài phạm vi nghiệp vụ của hệ thống (yêu cầu từ chối lịch sự).
    - `injection`: Thử thách bảo mật, cố tình phá vỡ system prompt hoặc trích xuất prompt.
    - `rbac`: Kiểm tra quyền truy cập (cho phép hoặc từ chối theo role/khu vực/hệ thống).
- [ ] **1.3. Gán mức độ khó (`slice.difficulty`)**:
  - Đánh giá độ phức tạp thực thi: `easy` | `medium` | `hard`.
- [ ] **1.4. Thiết lập Ground Truth (`expected`) & Ràng buộc Assertions**:
  - Điền trường `expected` chuẩn xác (câu trả lời mẫu hoặc hành vi đúng mà agent phải đạt được).
  - Khai báo các ràng buộc kiểm tra nếu có:
    - `must_include_tool`: Danh sách tool bắt buộc agent phải gọi (vd: `["sql_builder"]`).
    - `must_include_columns_any`: Cột bắt buộc xuất hiện trong kết quả (vd: `["direction", "so_luot"]`).
    - `must_not_include`: Các từ khóa hoặc thực thể không được phép xuất hiện (tránh hallucination).
- [ ] **1.5. Khử định danh PII (PII Sanitization & Redaction)**:
  - Rà soát câu hỏi và đáp án: tuyệt đối không lưu thông tin cá nhân định danh (CCCD, SĐT, email cá nhân, số tài khoản ngân hàng, token/mật khẩu).
- [ ] **1.6. Chốt duyệt & Thăng hạng Case (`Promotion`)**:
  - Sau khi hoàn thành các mục trên, chuyển `review: pending` → `review: approved`.
  - Cập nhật số case vào `cases` của `resource/eval/datasets/agent_stat/v(N+1).yaml`.

---

## 2. Phụ lục C rút gọn — 4 Trụ Cột Go-Live Audit

### Trụ cột 1: Bảo mật & Cấu hình (Security & Configuration)
- [ ] **Zero-Key on Disk / Image**: Không lưu API key, token, mật khẩu trong source code, Dockerfile, hay file tĩnh trên disk.
- [ ] **Runtime Secret Retrieval**: Secret được nạp an toàn từ biến môi trường hoặc Secret Manager lúc runtime.
- [ ] **Least Privilege DB / Sandbox**: Tool DB chỉ dùng quyền đọc (`SELECT`), cấm các lệnh thay đổi schema/data (`DROP`, `DELETE`, `UPDATE`); giới hạn thời gian thực thi (timeout) và số dòng trả về.
- [ ] **PII Sanitization**: Redact dữ liệu nhạy cảm (CCCD, SĐT, STK) trước khi lưu trữ log hoặc xuất trace ra bên thứ ba.

### Trụ cột 2: Chất lượng & Tiến hoá (Quality & Evolution)
- [ ] **Slice-based Evaluation**: Đo lường độc lập độ chính xác theo từng slice (`lookup`, `comparison`, `out_of_scope`, `injection`, `rbac`).
- [ ] **Eval Gate CI**: Tỷ lệ pass-rate trên Golden Dataset không được suy giảm quá ngưỡng cho phép (pass-rate ≥ baseline − 2pp).
- [ ] **Deterministic Smoke Test**: Có kịch bản kiểm thử các câu hỏi nghiệp vụ chốt chặn với đáp án xác định trước khi triển khai.
- [ ] **Automated Continuous Feedback**: Duy trì pipeline thu nhận phản hồi thumbs-down định kỳ vào draft golden dataset.

### Trụ cột 3: Vận hành & Chịu lỗi (Reliability & Resilience)
- [ ] **Multi-Provider Fallback**: Có cấu hình dự phòng nhà cung cấp LLM (Primary → Fallback) khi gặp sự cố quota hoặc provider outage.
- [ ] **Loop & Hop Guard**: Có chặn đệ quy vô hạn (`recursion_limit`, `SUPERVISOR_MAX_HOPS`) chống cạn kiệt tài nguyên.
- [ ] **Graceful Degradation**: Khi service phụ trợ (vector search, cache) gặp sự cố, hệ thống suy giảm chức năng an toàn thay vì crash 500.

### Trụ cột 4: Kinh tế & Giám sát (Economics & Observability)
- [ ] **Budget & Token Alerts**: Giám sát chi phí token, hop count và cảnh báo khi chạm các mốc ngưỡng (50%, 80%, 100%).
- [ ] **Incident Playbooks**: Đội ngũ vận hành nắm rõ 4 quy trình ứng phó: Cost Spike, Hallucination Spike, Jailbreak/Injection, Provider Outage.
- [ ] **Audit Trail Log**: Ghi nhận đầy đủ audit log cho các thao tác side-effect hoặc truy vấn nhạy cảm.

---

## 3. Phụ lục H rút gọn — 6 "Đường Nối" Cần Kiểm Tra

| # | Đường nối | Rủi ro khi đứt gãy | Tiêu chí kiểm soát đúng | Trạng thái |
|---|---|---|---|:--:|
| 1 | **Cache Key ↔ Prompt Version** | Sửa prompt nhưng hệ thống vẫn trả lời theo cache cũ | Cache key SHA256 kết hợp đầy đủ prompt version + model + user input | [ ] |
| 2 | **Path Filter CI** | Thay đổi logic prompt/agent nhưng test eval không kích hoạt | Config CI theo dõi đầy đủ các đường dẫn `src/**`, `resource/eval/**`, `config/**` | [ ] |
| 3 | **Deterministic Smoke Test** | Server trả về 200 OK nhưng chat thực tế bị lỗi do sai key | Kịch bản smoke test thực hiện gọi chuỗi hội thoại thực tế | [ ] |
| 4 | **Secret Runtime** | Lộ lọt credentials vào image layers hoặc artifact public | `.dockerignore` và `.gitignore` loại trừ file cấu hình chứa key thật | [ ] |
| 5 | **Alert Notification** | Cảnh báo hệ thống chỉ ghi log mà không ai tiếp nhận | Thông báo qua kênh theo dõi tập trung / Slack on-call | [ ] |
| 6 | **Feedback Loop (G17)** | Thumbs-down nằm chết trong cơ sở dữ liệu | Chạy định kỳ `scripts/feedback_to_golden.py` → Review theo AUDIT-CHECKLIST → Cập nhật `v+1.yaml` | [ ] |
