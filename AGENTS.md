# AGENTS.md — agent dong

Hướng dẫn thực thi chuẩn cho AI agent trong `agent-harness/dong` theo phương pháp Spec-Driven Development.

## Trạng thái dự án (v9)

- **Mục tiêu v9**: Xây dựng hệ thống Memory & Context Engineering 3 tầng (Short-Term, Long-Term, TTL Cache) lưu trữ bền vững trên PostgreSQL (bảng `user_memories`), tích hợp kỹ thuật Sliding Window, nguyên tắc 40-60%, Summarization, Tool Output Compression và Re-injecting Instructions.
- **Tài liệu bắt buộc đọc trước khi code**:
  1. [`specs/product-spec.md`](specs/product-spec.md) — Yêu cầu nghiệp vụ và tiêu chí nghiệm thu.
  2. [`specs/implementation-plan.md`](specs/implementation-plan.md) — 7 phase triển khai tuần tự.
  3. [`specs/test-plan.md`](specs/test-plan.md) — Kế hoạch kiểm thử tự động và thủ công.
  4. [`specs/change-log.md`](specs/change-log.md) — Nhật ký thay đổi qua từng bước.
  5. [`specs/gap-analysis-quy-trinh-product-agent.md`](specs/gap-analysis-quy-trinh-product-agent.md) — Living tracker G0–G17 vs quy trình product (cập nhật khi đóng hạng mục).

---

## Quy tắc thực thi (Rules)

1. **Always read the specs before coding**: Luôn đọc kỹ `specs/product-spec.md` và `specs/implementation-plan.md` trước khi viết bất kỳ dòng code nào.
2. **Implement only one phase or task at a time**: Chỉ thực hiện duy nhất 1 phase hoặc 1 task (`[ ]`) tại một thời điểm. Không nhảy cóc, không gộp nhiều task.
3. **Keep the app simple**: Giữ mã nguồn đơn giản, rõ ràng, tập trung vào phạm vi MVP, không làm phức tạp hóa vấn đề (over-engineering).
4. **Do not add unnecessary libraries**: Tận dụng tối đa thư viện và công cụ sẵn có trong dự án, không tự ý cài đặt thêm dependency nếu không bắt buộc.
5. **Do not change architecture unless the spec is updated**: Tuyệt đối không thay đổi kiến trúc hệ thống trừ khi spec đã được thảo luận và cập nhật trước.
6. **After each implementation, update specs/change-log.md**: Sau mỗi lần hoàn thành 1 task, đánh dấu `[x]` trong `specs/implementation-plan.md` và ghi nhận chi tiết vào `specs/change-log.md`.
7. **After each implementation, explain how to test the change**: Luôn giải thích rõ ràng và cung cấp lệnh/kịch bản kiểm thử cụ thể để người dùng có thể tự kiểm tra lại thay đổi.
8. **SDD feature loop (bắt buộc — guide VN)**: Mỗi feature/task phải qua cổng review trước khi sang task tiếp theo. Xem mục dưới.
9. **Orca Coordinator auto-wake**: Khi điều phối multi-agent, sau mỗi `worker-start` phải chạy `orca-coord-watch` (§15e trong `orca_setup/ORCA-AGENT-SETUP.md`). Khi có `[ORCA auto-wake]` / report mới: đọc + phản hồi user ngay — không chờ nhắc.
10. **Gap tracker G0–G17**: Khi xử lý xong (Approved) một hạng mục gắn giai đoạn G\*, **bắt buộc** cập nhật hàng tương ứng trong [`specs/gap-analysis-quy-trinh-product-agent.md`](specs/gap-analysis-quy-trinh-product-agent.md) theo §0 Protocol của file đó (trạng thái / đã có / còn thiếu + §5 lịch sử).

---

## Vòng lặp SDD mỗi feature (bắt buộc)

Khớp [`resource/knowledge_handbook/Spec Driven Development Guide - Vietnamese.md`](resource/knowledge_handbook/Spec Driven Development Guide - Vietnamese.md) và `orca_setup/ORCA-AGENT-SETUP.md` §6c.

Nguồn sự thật SDD: 4 file core (`product-spec`, `implementation-plan`, `test-plan`, `change-log`) + living tracker [`gap-analysis-quy-trinh-product-agent.md`](specs/gap-analysis-quy-trinh-product-agent.md). Không tạo plan/spec phụ khác trừ khi user Explicit yêu cầu.

```text
[Plan] specs đã review MVP
    → [Implement] đúng 1 task [ ] (+ test theo acceptance)
    → [Review] so product-spec + test-plan (pass / fail / missing)
    → [Fix] chỉ lỗi của task đó + cập nhật change-log
    → Review lại đến Approved
    → mới được sang task [ ] tiếp theo
```

**Cổng cứng**

| Cấm | Được phép |
|-----|-----------|
| Sang task `[ ]` kế khi task hiện tại chưa `Approved` sau review | Implementer/Test chỉ làm **một** unchecked item mỗi vòng |
| Gom nhiều phase/feature trong một lần code | Reviewer `Blocked` → Implementer/Test **fix-only** → review lại |
| Đổi kiến trúc / thêm scope khi đang fix | Tick `[x]` + `change-log` sau implement; ghi `verdict` review vào report |

Với khung Orca multi-role: Coordinator **không** dispatch task kế cho Implementer cho đến khi Reviewer-5a (và 5b nếu đã mở) trả `Approved`. Fix sau `Blocked` vẫn thuộc **cùng** task, không mở task mới.

---

## Lệnh kiểm thử nhanh

```bash
cd agent-harness/dong

# 1. Chạy toàn bộ unit test suite
PYTHONPATH=. pytest -q

# 2. Chạy riêng bộ kiểm thử memory & context
PYTHONPATH=. pytest tests/test_product_memory_context.py tests/test_product_memory_cache.py tests/test_product_memory_postgres.py -v

# 3. Khởi động backend local
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
