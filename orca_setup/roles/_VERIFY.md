# Verify (ORCA-AGENT-SETUP §18) — bắt buộc khi role liên quan

## Tool trước AI
- Lint / typecheck / unit / build: **chạy lệnh thật**, dán output vào report.
- **Cấm** bảo “ổn” chỉ vì đã đọc code. Không dùng AI thay `pytest` / linter / typechecker.

## Review đối kháng (Reviewer 5a/5b — và khi user yêu cầu verify)
- Mục tiêu: **bác bỏ** kết quả; chỉ báo lỗi ảnh hưởng correctness / acceptance / regression.
- Mỗi finding kèm bằng chứng: lệnh + output, hoặc path + đoạn code, hoặc test fail.
- Session/model khác Implementer khi có thể (5a Cursor → 5b Claude).

## Eval metric (khi có ground truth / eval set trong specs)
- Đo trên tập cố định; so cùng tập giữa các phiên bản.
- Lab FGS: E2E + wall/RAM/compression đủ trừ khi specs yêu cầu thêm.

## Cổng SDD mỗi feature (ORCA-AGENT-SETUP §6c)
- Sau Implement/Test: Reviewer phải chạy trước khi task kế.
- `Blocked` → Fix-only cùng task → review lại. `Approved` → mới unchecked task tiếp.
- Implementer/Test **cấm** tự nhảy task trong cùng turn.

## Gap tracker G0–G17
- File: `specs/gap-analysis-quy-trinh-product-agent.md` (§0 Protocol).
- Sau hạng mục **Approved** gắn G\*: cập nhật hàng bảng §1 (trạng thái / đã có / còn thiếu) + §5 lịch sử + `change-log`.
- Report ghi `gap_updated: G..` hoặc `gap_updated: none`.

## Report
Trong `specs/agent-reports/…` thêm:
- `tools_run:` lệnh + exit code / tóm tắt output
- `verdict:` Approved | Blocked | N/A
- `findings:` Critical / Important / Minor (có bằng chứng) hoặc `none`
- `sdd_gate:` passes | fails | missing (so acceptance) khi là Reviewer
- `next_hint:` Reviewer-5a | Fix-only | next-task-after-Approved | …
