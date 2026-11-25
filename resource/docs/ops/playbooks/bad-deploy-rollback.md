# Sổ tay sự cố: Bad Deploy & Rollback / Hoàn tác triển khai lỗi khẩn cấp

> Thuộc bộ Ops Playbooks (`resource/docs/ops/playbooks/`) — Chuẩn quy trình vận hành sự cố (G16).

---

## 1. Triệu chứng (Symptoms)

- Ngay sau khi triển khai phiên bản mới (git pull, build image mới, hoặc cập nhật docker compose), hệ thống xuất hiện các lỗi diện rộng:
  - Container `ai_backend` hoặc `frontend` bị crash liên tục (`CrashLoopBackOff` hoặc `Exited (1)`).
  - Endpoint kiểm tra sức khỏe `GET /api/health` hoặc `GET /ready` trả về lỗi HTTP 500 hoặc không thể kết nối (`Connection refused`).
  - Giao diện web người dùng bị trắng màn hình (blank page) hoặc không tải được script `app.js`.
  - Mọi yêu cầu chat đều trả về lỗi nghiêm trọng và không thể khởi tạo luồng chạy đồ thị agent (graph compile error).

---

## 2. Phát hiện (Detection: Log & Metric)

### 2.1. Kiểm tra trạng thái container và mã thoát
```bash
docker compose ps
```
Quan sát nếu container `ai_backend` hiển thị trạng thái `Exit 1` hoặc thời gian `Up` chỉ vài giây (restart liên tục).

### 2.2. Kiểm tra log khởi động gần nhất
```bash
docker compose logs --tail=100 ai_backend
```
Tìm kiếm các dấu hiệu lỗi phổ biến:
- `SyntaxError` hoặc `ImportError`: Do mã nguồn mới thiếu file hoặc import sai đường dẫn.
- `pydantic.ValidationError`: Do thiếu biến môi trường mới bắt buộc trong file `.env`.
- `ModuleNotFoundError`: Do dependency mới chưa được thêm vào `requirements.txt` hoặc chưa được cài đặt trong image.

### 2.3. Kiểm tra các endpoint kiểm tra sức khỏe
```bash
curl -i http://localhost:8000/api/health
curl -i http://localhost:8000/ready
```

### 2.4. Xác định mã commit vừa deploy
```bash
git log -n 1 --oneline
```

---

## 3. Xử lý từng bước (Step-by-step Resolution)

### Bước 1: Xác định commit / tag ổn định trước đó
Kiểm tra lịch sử git để lấy mã commit hoạt động tốt gần nhất:
```bash
git log -n 5 --oneline
```
Giả sử commit ổn định trước đó có hash là `<last-known-good-commit>`.

### Bước 2: Hoàn tác mã nguồn khẩn cấp

#### Lựa chọn A: Revert commit lỗi (Khuyến nghị cho branch chính)
```bash
# Hoàn tác commit gần nhất mà không làm mất lịch sử git
git revert HEAD --no-edit
```

#### Lựa chọn B: Checkout về commit hoặc release tag ổn định
```bash
# Tạm thời chuyển working tree về commit an toàn
git checkout <last-known-good-commit>
```

### Bước 3: Rebuild và khởi động lại container dịch vụ
Sau khi đưa mã nguồn về phiên bản an toàn, tiến hành build lại và recreate container:
```bash
# Build lại container backend không sử dụng cache
docker compose build --no-cache ai_backend

# Khởi động lại dịch vụ backend và frontend
docker compose up -d --force-recreate ai_backend frontend
```

### Bước 4: Kiểm tra và phục hồi cấu hình (nếu lỗi do config/env)
Nếu lỗi xuất phát từ file cấu hình `config/models.yaml` hoặc `.env`:
```bash
# So sánh khác biệt trong thư mục config
git diff config/

# Khôi phục file cấu hình về bản gốc của commit ổn định
git checkout HEAD -- config/models.yaml
```

---

## 4. Xác nhận phục hồi (Recovery Verification)

### Bước 1: Kiểm tra container đã ở trạng thái Up ổn định
```bash
docker compose ps
```
Đảm bảo cả `kcn_hungphu_backend`, `kcn_hungphu_frontend`, `agent_postgres`, `kcn_agent_qdrant` đều ở trạng thái `Up` (healthy).

### Bước 2: Kiểm tra endpoint `/api/health` và `/ready`
```bash
curl -f http://localhost:8000/api/health
curl -f http://localhost:8000/ready
```
*Kỳ vọng:* Cả hai đều trả về mã HTTP 200 kèm `{"status": "ok"}` và `{"ready": true}`.

### Bước 3: Chạy bộ smoke test bằng pytest
Thực thi kiểm tra nhanh các endpoint chính của backend:
```bash
PYTHONPATH=. pytest tests/test_product_ready_sse.py -v
```
*Kỳ vọng:* Toàn bộ test case đạt trạng thái **PASSED**.

### Bước 4: Kiểm tra log vận hành sau phục hồi
```bash
docker compose logs --tail=50 ai_backend
```
Đảm bảo server Uvicorn đã khởi động thành công trên cổng 8000 và không có traceback unhandled exception.

---

## 5. Hậu kiểm (Post-mortem & Follow-up)

1. **Phân tích nguyên nhân triển khai thất bại:**
   - Tại sao lỗi không được phát hiện ở môi trường kiểm thử local hoặc CI workflow (`.github/workflows/ci.yml`)?
   - Có sự khác biệt nào giữa biến môi trường local và máy chủ production?
2. **Cập nhật quy trình kiểm tra (Testing Gates):**
   - Bổ sung test case kiểm tra cấu hình hoặc module bị thiếu vào `tests/`.
   - Đảm bảo CI chạy đầy đủ trước khi cho phép merge code vào branch chính.
3. **Lưu vết và báo cáo:**
   - Ghi lại mã commit lỗi, commit rollback và diễn biến sự cố vào `specs/change-log.md`.
   - Tạo branch fix riêng để xử lý triệt để nguyên nhân trước khi tiến hành deploy lại.
