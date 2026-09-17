## 2026-09-17 (Review Phase 5 item 1 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("3 tool domain mới trong
`src/agent/tools.py`") đối chiếu `specs/product-spec.md` và
`specs/test-plan.md`.

### Pass
- `test-plan.md` "Test offline" #1 ĐÚNG CHỮ: `count_anomaly_events(
  event_type="LOI_BIA")` qua `.invoke()` thật → `error` rõ ràng trong
  `QueryResult`, không query DB.
- `test-plan.md` "Test offline" #2: danh sách tool khớp thiết kế — đã sửa
  test cũ, `pytest` sạch.
- Test thêm (chưa test ở lượt implement): `group_by="department_name"`
  cho `count_face_events` → trả breakdown thật, có cả bucket `null`
  (chưa gán phòng ban) lẫn tên phòng ban thật ("Ban Lãnh Đạo", "Trí tuệ
  nhân tạo") — group_by hoạt động đúng, không chỉ default. `entity_type=
  "FIRE"` cho `count_fire_smoke_events` → vẫn rỗng đúng (domain trống mọi
  filter). `group_by="severity"` cho `count_anomaly_events` → đúng, toàn
  bộ FIGHT_DETECTION severity=HIGH.
- Không thêm thư viện, không đổi tool cũ, đúng pattern LangChain `@tool`
  có sẵn.

### Fail
- Không tìm thấy lỗi nào trong phạm vi feature này.

### Ghi nhận (không phải thiếu sót)
- `get_db_schema` (tool mô tả nguồn dữ liệu cho `run_sql_readonly`) CHƯA
  nhắc 3 nguồn mới — KHÔNG sửa, vì `run_sql_readonly` (fallback SQL tự do)
  vẫn CHỈ giới hạn `plate_event`/`zone_event` (chưa mở rộng, đúng thiết
  kế — 3 domain mới CHỈ truy cập qua tool tham số hoá riêng, không qua SQL
  tự do) — `get_db_schema` hiện tại vẫn phản ánh ĐÚNG phạm vi thật của
  `run_sql_readonly`, không lỗi thời.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `list_khu_vuc` chưa liệt kê camera có `ai_modules` FACE/FIRE/ANOMALY —
  item TIẾP THEO trong Phase 5, chưa tới lượt.
- Chưa test được qua LLM thật (agent tự chọn đúng tool cho câu hỏi domain
  mới) — vẫn bị chặn bởi bug dependency `openai`/`httpx2`
  (`task_2e390bb8`, chưa fix).

## 2026-09-17 (Phase 5, item 1: `src/agent/tools.py` — 3 tool domain mới)

### Added
- `src/agent/tools.py` — 3 `@tool` mới, đúng pattern có sẵn (check
  `settings.db_configured`, lazy import `src.db.queries`, wrap qua
  `_wrap_dict`): `count_face_events`, `count_fire_smoke_events`,
  `count_anomaly_events`. Docstring `count_anomaly_events` liệt kê RÕ 4
  giá trị `event_type` hợp lệ (kèm nghĩa tiếng Việt) + nhắc lại rõ ràng
  KHÁC `zone_intrusion_by_hour` (tránh model nhầm "leo trèo" với "vùng
  cấm" — đúng lưu ý thiết kế từ Phase 2). Docstring
  `count_fire_smoke_events` nói rõ domain hiện rỗng hoàn toàn (dữ liệu
  thật, không phải lỗi) để model không hoảng/bịa khi thấy rỗng.
- Thêm cả 3 tool vào `TOOLS`.

### Fixed (test cũ, hệ quả trực tiếp bắt buộc phải sửa)
- `tests/test_offline.py::test_danh_sach_tool_dung_thiet_ke` check
  `tool_names == {...}` (SO KHỚP CHÍNH XÁC) — fail ngay khi thêm 3 tool
  mới, đúng dự kiến (`test-plan.md` mục "Test offline" #2 đã ghi trước:
  "assertion tên tool khớp product-spec.md" — cần cập nhật khi tool mới
  tồn tại). Cập nhật set kỳ vọng thêm 3 tên tool mới.

### Verified
- `pytest -q` → "5 passed" (sau khi sửa test ở trên).
- Gọi thật cả 3 tool qua `.invoke()` (interface LangChain thật, không
  phải gọi thẳng hàm Python): `count_face_events` → 3953 IN (khoảng
  07-15/09); `count_fire_smoke_events` → rỗng (đúng, domain trống);
  `count_anomaly_events(FIGHT_DETECTION)` → 12562 (khoảng 04-16/09, org
  106); `count_anomaly_events(SIDEWALK_ENCROACHMENT)` → `error` rõ ràng
  trong `QueryResult`, không query DB, không crash tool.

## 2026-09-17 (Review Phase 4 item 3 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("`src/monitoring/tracing.py`") đối
chiếu `specs/product-spec.md` (Acceptance Criteria) và `specs/test-plan.md`
mục "Test Langfuse tracing" (4 test case).

### Pass
- Test #1 (`MONITORING_ENABLED=false` → `pytest` y hệt trước): verify lại
  — "5 passed", không cần Langfuse chạy.
- Test #4 (Langfuse service down → không crash): verify bằng
  `LANGFUSE_HOST` trỏ tới cổng không ai lắng nghe — `trace_answer()`
  KHÔNG crash, trả về bình thường sau khi hết retry (~3.8s), lỗi chỉ log
  ra `stderr` (cảnh báo), không raise lên caller.
- Test #3 (không lộ secret trong trace): rà lại code `tracing.py` — input/
  output/metadata chỉ chứa `question`/`answer`/`latency_s`, không có
  đường nào đưa `OPENAI_API_KEYS`/`DB_PASSWORD` vào trace theo THIẾT KẾ
  hiện tại (secrets không đi qua tham số nào của `trace_answer`/
  `trace_step`). Test đầy đủ với câu hỏi chứa PII thật cần chờ Phase 5
  wire vào `/ask` (đi qua `redact_pii()` trước).
- `product-spec.md`: trace thật lưu được vào Langfuse tự host — verify
  tận ClickHouse (`events_core`), không chỉ tin "không lỗi Python".

### Fail — đã sửa (thuộc hạ tầng Phase 4 item 1, không phải code
`tracing.py`)
- Xem mục "BUG hạ tầng" ở entry implement bên trên (`SignatureDoesNotMatch`
  do quên đồng bộ `LANGFUSE_S3_*_SECRET_ACCESS_KEY` với
  `MINIO_ROOT_PASSWORD`) — đã sửa `langfuse/.env`, verify lại trace lưu
  được.

### Ghi nhận thêm cho Phase 5 (không phải bug của item này)
- Khi Langfuse KHÔNG phản hồi, `trace_answer()` mất ~3.8s (2 lần retry +
  backoff) trước khi bỏ cuộc — nếu Phase 5 bọc TOÀN BỘ `/ask` trong
  `trace_answer()`, Langfuse down sẽ làm MỌI câu hỏi chậm thêm ~3.8s (dù
  vẫn trả lời đúng, không crash). Cân nhắc ở Phase 5: có cần giảm số lần
  retry/timeout của OTel exporter hay chấp nhận độ trễ này (MVP, tần suất
  Langfuse down thấp) — quyết định này thuộc Phase 5, ghi lại ở đây để
  không quên khi tới lượt.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- Test #2 (trace thật của 1 lượt `/ask` qua endpoint, có span con cho
  bước chọn tool + diễn giải) — cần wiring vào `main.py`/`graph.py`,
  đúng Phase 5, chưa tới lượt (đã verify tương đương ở MỨC MODULE:
  `trace_answer`+`trace_step` lồng nhau hoạt động đúng, xem entry
  implement).

## 2026-09-17 (Phase 4, item 3 — item cuối: `src/monitoring/tracing.py`)

### Added
- `src/monitoring/__init__.py` (rỗng, đúng phong cách `src/db/`,
  `src/agent/`).
- `src/monitoring/tracing.py` — copy gần như nguyên từ
  `llm-engineer-demo/app/monitoring/tracing.py` (đã kiểm chứng API tương
  thích với `langfuse==4.15.4` thật trước khi copy, không copy mù):
  `trace_answer(name, question, metadata)` (context manager gốc cho 1
  lượt `/ask`), `trace_step(parent_span, name, input, metadata)` (nested
  child span), `trace_stream(...)` (giữ để đồng bộ interface, chưa dùng ở
  agent_ATIN vì chưa có streaming). `_get_langfuse()` lazy import + lazy
  client. Toàn bộ no-op (yield `{}`) khi `MONITORING_ENABLED=false`.

### BUG hạ tầng tự phát hiện khi test thật — đã sửa `langfuse/.env` (Phase 4 item 1)
- Gửi thử 1 trace thật (`trace_answer` + `trace_step` lồng nhau) với
  `MONITORING_ENABLED=true` và key thật từ `langfuse/.env` → không lỗi ở
  phía Python, nhưng verify trực tiếp ClickHouse (`SELECT count(*) FROM
  events_core/observations/traces`) thấy **0 dòng** — trace đã gửi nhưng
  KHÔNG được lưu.
- Bật `debug=True` trên `Langfuse()` để xem log chi tiết → phát hiện
  `langfuse-web` log lỗi `SignatureDoesNotMatch` khi upload JSON lên
  MinIO. Nguyên nhân: ở Phase 4 item 1, tôi đổi `MINIO_ROOT_PASSWORD`
  sang giá trị ngẫu nhiên nhưng QUÊN đồng bộ 3 biến riêng
  `LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY`/
  `LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY`/
  `LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY` (langfuse-web dùng 3 biến
  này để auth vào MinIO, mặc định `miniosecret` — không tự ăn theo
  `MINIO_ROOT_PASSWORD`) — cùng LOẠI lỗi với bug `DATABASE_URL` đã gặp ở
  Phase 4 item 1 (quên đồng bộ credential dẫn xuất khi đổi mật khẩu gốc).
- **Sửa:** thêm 3 biến trên vào `langfuse/.env`, cùng giá trị
  `MINIO_ROOT_PASSWORD` (không in secret ra output), `docker compose up
  -d` để áp dụng.
- Verify lại: gửi lại trace → `events_core` có đúng 2 dòng (`ask` +
  `chon_tool`), `chon_tool.parent_span_id` trỏ đúng về span `ask` — cấu
  trúc cha-con nested ĐÚNG như thiết kế.

### Verified
- `pytest -q` → "5 passed" (không regression).
- `MONITORING_ENABLED` không set (mặc định `false`) → `trace_answer()`/
  `trace_step()` trả `{}` ngay, không tạo client Langfuse, không cần
  Langfuse chạy.
- `MONITORING_ENABLED=true` + key thật → trace THẬT xuất hiện trong
  ClickHouse (`events_core`), verify tận nơi lưu trữ (không chỉ tin log
  "không lỗi" ở phía Python) — bài học từ chính bug vừa tìm thấy trong
  mục này.
- Exception trong `with trace_answer(...)`: được RE-RAISE ra ngoài (không
  bị nuốt), verify bằng `try/except RuntimeError` bắt được đúng lỗi giả
  lập.
- Ghi nhận: `GET /api/public/traces`/`/observations` (REST API cũ) trả
  `404` với thông báo "not available... in Langfuse v4 events_only mode"
  — bản Langfuse mới nhất (deploy ngày 2026-09-17) mặc định chạy chế độ
  lưu trữ mới (`events_core` trong ClickHouse), không dùng bảng
  `traces`/`observations` cũ cho API cũ nữa. Không ảnh hưởng
  `trace_answer()`/`trace_step()` (dùng `start_observation()`, tương
  thích chế độ mới) — chỉ ảnh hưởng nếu sau này cần QUERY LẠI trace qua
  REST API cũ (`v2/observations` vẫn hoạt động, xem entry trước).

## 2026-09-17 (Review Phase 4 item 2 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("4 field cấu hình Langfuse") đối chiếu
`specs/product-spec.md` và `specs/test-plan.md` mục "Test Langfuse
tracing" #1.

### Pass
- `test-plan.md` #1 CHÍNH XÁC: gỡ hẳn package `langfuse`
  (`pip uninstall -y langfuse`) rồi chạy `pytest -q` → vẫn "5 passed",
  không lỗi import — vì `src/config.py` chỉ khai báo field, KHÔNG
  `import langfuse` — đúng yêu cầu "không import lỗi nếu thiếu package".
  Cài lại `langfuse` sau khi verify xong.
- `product-spec.md`: `MONITORING_ENABLED` mặc định `False` — verify qua
  `settings.monitoring_enabled`.
- Field mới hoàn toàn additive, không đổi field/hành vi cũ nào.

### Fail
- Không tìm thấy lỗi nào trong phạm vi feature này.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `test-plan.md` #2/#3/#4 (trace xuất hiện khi bật monitoring, không lộ
  secret, Langfuse down không crash `/ask`) — cần `src/monitoring/
  tracing.py` (item tiếp theo) + wiring vào `main.py`/`graph.py` (Phase
  5), chưa tới lượt.
- `.env` thật của app chưa điền `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY` thật
  (chỉ có ở `langfuse/.env`) — không thuộc phạm vi item này (chỉ thêm
  field + default), sẽ cần điền khi tới lượt test #2 thật.

## 2026-09-17 (Phase 4, item 2: `src/config.py` + `.env.example` + `requirements.txt` — biến Langfuse)

### Added
- `src/config.py` — thêm 4 field: `monitoring_enabled` (alias
  `MONITORING_ENABLED`, default `False`), `langfuse_public_key`,
  `langfuse_secret_key` (default rỗng), `langfuse_host` (default
  `http://localhost:3000` — khớp UI đã deploy ở Phase 4 item 1). Đặt sau
  nhóm Guardrail, đúng thứ tự thêm-mới-ở-cuối như các nhóm trước.
- `.env.example` — thêm nhóm "Observability (Langfuse, Phase 4)" tương
  ứng, ghi rõ mặc định tắt + tự host, không dùng Cloud.
- `requirements.txt` — thêm `langfuse` (SDK Python chính thức, bản
  `4.15.4`, tương thích server Langfuse v4 đã deploy ở item trước).

### Verified
- `pip install langfuse` + `pytest -q` → "5 passed" (không regression).
- `python3 -c "from src.config import settings; ..."`: `monitoring_enabled
  = False` (mặc định tắt, đúng yêu cầu), `langfuse_host =
  http://localhost:3000`, `langfuse_public_key`/`langfuse_secret_key`
  rỗng (đúng — `.env` thật của app CHƯA điền, chỉ có ở `langfuse/.env`
  tự sinh ở item trước; điền vào `.env` thật của app không thuộc phạm vi
  item này, chỉ thêm field + default).
- `import langfuse` thành công, không lỗi phụ thuộc.

## 2026-09-17 (Review Phase 4 item 1 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("deploy Langfuse self-host") đối chiếu
`specs/product-spec.md` và `specs/test-plan.md`.

### Pass
- `product-spec.md` "Observability — Langfuse tự host trên máy này": đúng
  — self-host thật (không dùng Langfuse Cloud), UI + API hoạt động thật,
  đã verify không chỉ "container chạy" mà còn "key hoạt động được".
- Tất cả secret tự sinh (không dùng giá trị mặc định `# CHANGEME` của
  file gốc) — đúng tinh thần bảo mật cho server thật.
- Không đụng code app (`pytest` vẫn "5 passed", `.env` gốc của app chưa
  có biến `LANGFUSE_*` nào — đúng phạm vi, item đó chưa tới lượt).

### Fail
- Không có lỗi nào còn tồn đọng — 2 lỗi gặp lúc deploy (xung đột cổng
  9090, sai `DATABASE_URL`) đã sửa VÀ verify lại NGAY trong lúc implement
  (không để sang lượt review riêng vì đó là lỗi chặn hoàn toàn, không thể
  coi "đã implement" khi container còn crash).

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `test-plan.md` mục "Test Langfuse tracing" (4 test case: tắt/bật
  monitoring, không lộ secret trong trace, Langfuse down không crash
  `/ask`) — CHƯA áp dụng được, cần `src/config.py` thêm
  `MONITORING_ENABLED`/`LANGFUSE_*` (item tiếp theo) + `src/monitoring/
  tracing.py` + wiring vào `main.py`/`graph.py` (Phase 5) trước.
- Chưa gửi thử 1 trace thật vào Langfuse (cần `tracing.py`, chưa code) —
  chỉ mới xác nhận HẠ TẦNG (project + key) sẵn sàng để nhận trace, đúng
  scope "chỉ dựng hạ tầng ở phase này" ghi ngay đầu Phase 4 trong
  `implementation-plan.md`.

## 2026-09-17 (Phase 4, item 1: Deploy Langfuse self-host)

### Added
- `langfuse/docker-compose.yml` — file CHÍNH THỨC tải nguyên từ
  `https://raw.githubusercontent.com/langfuse/langfuse/main/docker-compose.yml`
  (không clone repo — chỉ cần file compose vì dùng image build sẵn
  `docker.langfuse.com/langfuse/langfuse:4`, không tự build từ source).
  Sửa 2 chỗ để tránh xung đột cổng đã dùng trên máy này: cổng host của
  MinIO đổi từ `9090` → `9190` (2 dòng: port mapping + biến môi trường
  `LANGFUSE_S3_*_EXTERNAL_ENDPOINT`/`LANGFUSE_S3_MEDIA_UPLOAD_ENDPOINT`
  mặc định).
- `langfuse/.env` (không commit — khớp pattern `.env` có sẵn trong
  `.gitignore`, áp dụng cho mọi thư mục con) — sinh ngẫu nhiên toàn bộ
  secret đánh dấu `# CHANGEME` trong file gốc (`SALT`, `ENCRYPTION_KEY`,
  `NEXTAUTH_SECRET`, `POSTGRES_PASSWORD`, `CLICKHOUSE_PASSWORD`,
  `MINIO_ROOT_PASSWORD`, `REDIS_AUTH`) — KHÔNG dùng giá trị mặc định
  (`postgres`/`mysecret`/...) như file gốc, vì đây là server thật, không
  phải máy demo tạm. Dùng biến `LANGFUSE_INIT_*` (tính năng có sẵn của
  Langfuse) để tự động tạo 1 org + 1 project (`agent_ATIN`) + 1 user admin
  + 1 cặp `public_key`/`secret_key` cố định ngay lúc khởi động — KHÔNG
  cần thao tác tay qua UI (đăng ký/tạo project) để lấy key.

### Fixed (trong lúc deploy, trước khi coi là xong)
- Lần chạy đầu `docker compose up -d` lỗi
  `failed to bind host port 0.0.0.0:9090/tcp: address already in use` —
  máy này đã có service khác dùng cổng 9090. Sửa: đổi cổng host MinIO
  sang `9190` (đã free, kiểm tra bằng `ss -tln` trước khi chọn).
- Sau khi container `langfuse-web` chạy, log báo
  `Error: P1000: Authentication failed against database server` — do
  quên set `DATABASE_URL` khớp mật khẩu Postgres mới sinh (`.env` chỉ có
  `POSTGRES_PASSWORD` cho container Postgres, còn `DATABASE_URL` mặc
  định trong `docker-compose.yml` vẫn là chuỗi cũ `postgres:postgres`).
  Sửa: thêm `DATABASE_URL=postgresql://postgres:<POSTGRES_PASSWORD>@postgres:5432/postgres`
  vào `.env` (không in mật khẩu ra bất kỳ output nào trong lúc sửa).

### Verified
- `docker compose ps`: đủ 6 container (`postgres`, `clickhouse`, `redis`,
  `minio`, `langfuse-worker`, `langfuse-web`) đều `Up`/`healthy`.
- `curl http://localhost:3000` → `200 OK`, trang Langfuse render được —
  UI truy cập được qua trình duyệt (từ máy này hoặc qua SSH tunnel/LAN
  nếu truy cập từ máy khác).
- Gọi thật `GET /api/public/projects` với header `Authorization: Basic
  base64(public_key:secret_key)` (đọc từ `langfuse/.env`, không in ra
  console) → trả đúng JSON có project `agent_ATIN` + organization
  `agent_ATIN` — xác nhận cặp key KHỞI TẠO TỰ ĐỘNG hoạt động thật, không
  chỉ tồn tại trong file `.env`.
- Chỉ 2 cổng public trên host: `3000` (web) và `9190` (MinIO S3 — đổi từ
  9090) — đúng khuyến nghị bảo mật trong comment đầu file compose gốc
  ("restrict inbound traffic... to langfuse-web và minio only"), các
  service còn lại (`postgres`, `redis`, `clickhouse`) chỉ bind
  `127.0.0.1`.

### Quản lý (để dùng ở các item sau + cho user)
- Start: `cd langfuse && docker compose up -d`. Stop:
  `docker compose down` (giữ data) / thêm `-v` để xoá sạch data.
- Xem log: `docker compose logs langfuse-web -f`.
- `public_key`/`secret_key`/mật khẩu admin UI nằm trong `langfuse/.env`
  (không commit) — item Phase 4 tiếp theo (`src/config.py` thêm
  `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_HOST`) sẽ đọc từ
  đây để điền vào `.env` của app chính.

## 2026-09-17 (Review Phase 3 item 3 vs product-spec.md/test-plan.md)

Review lại đúng 1 "feature" vừa làm ("test kết nối thật read-only cho 3 DB
mới") đối chiếu `specs/product-spec.md` và `specs/test-plan.md`. Vì đây là
task verify (không có code mới), review chỉ đối chiếu xem đã verify ĐỦ và
ĐÚNG những gì test-plan.md yêu cầu cho đúng bullet này hay chưa.

### Pass
- Khớp CHÍNH XÁC bullet "Lớp app/session-readonly" trong `test-plan.md`
  mục "Test guardrail an toàn (2 lớp)": verify qua `get_connection()`
  thật, DELETE/UPDATE → `ReadOnlySqlTransaction` (không phải
  `InsufficientPrivilege` như lớp Postgres/GRANT đã verify ở Phase 2 item
  1) — đúng cả tên lỗi lẫn cơ chế.
- `product-spec.md` "Hạ tầng — đọc-only Postgres qua role riêng... trên
  mọi DB nguồn cần dùng": xác nhận đủ 5/5 DB, cả 2 lớp bảo vệ đều hoạt
  động đúng.
- Không thêm thư viện, không đổi kiến trúc, không đổi code — đúng bản
  chất "task verify" của item này.

### Fail
- Không có — không có code mới ở item này nên không có gì để tìm lỗi.

### Missing (thuộc các item/phase KHÁC, không phải thiếu sót của item này)
- `test-plan.md` "Test offline" #2 (danh sách tool mới đúng thiết kế) —
  thuộc Phase 5 (`src/agent/tools.py` chưa code).
- `test-plan.md` "Test thật" (6 câu hỏi mẫu domain mới qua agent đầy đủ)
  — cần Phase 5 xong + fix dependency `openai`/`httpx2`
  (`task_2e390bb8`, đã tạo ở lượt trước).
- Test offline #1 (`LOI_BIA`), #3 (`in_scope`), #4 (`dbname` lạ) — đã
  verify ở các lượt review TRƯỚC (Phase 2 item 3, Phase 3 item 1/2), không
  lặp lại thừa ở đây.

## 2026-09-17 (Phase 3, item 3 — item cuối: test kết nối thật read-only cho 3 DB mới)

Item này là task VERIFY (không phải file code mới) — không có gì để
modify. Đã verify rải rác qua các item trước (Phase 2 item 1: lớp
Postgres/GRANT qua raw `psycopg2`; Phase 3 item 1: lớp app/session-readonly
qua `get_connection()`) — chạy lại đầy đủ, tường minh 1 lần theo đúng mô tả
checklist, giống tiền lệ v1 (`specs/change-log.md` mục "Phase 3, item 3: test
kết nối thật read-only").

### Verified
- SELECT chạy được qua `get_connection()` cho cả 3 DB mới:
  `smart_face.smf_face_events` (3953 dòng), `firesmoke.fire_smoke_event`
  (0 dòng — đúng, bảng rỗng), `anomaly.anomaly_event` (429327 dòng, đếm
  toàn bảng không lọc org).
- DELETE/UPDATE bị Postgres từ chối cho cả 3 DB — `ReadOnlySqlTransaction`
  (lớp app, `conn.set_session(readonly=True)` trong `get_connection()`):
  `smart_face` (DELETE), `firesmoke` (UPDATE), `anomaly` (DELETE).
- `dbname` ngoài whitelist (`vms_db`) vẫn bị chặn `ValueError` ngay ở
  lớp code, không mở connection thật — không regression.

**Phase 3 (Core Backend / Data Logic) đã hoàn thành đủ 3/3 item cho cả
v1 và v2.**

## 2026-09-17 (Review Phase 3 item 2 vs product-spec.md/test-plan.md — có fix)

Review lại đúng 1 feature vừa làm ("3 hàm SQL domain mới trong
`src/db/queries.py`") đối chiếu `specs/product-spec.md` (Acceptance
Criteria) và `specs/test-plan.md`.

### Pass
- `test-plan.md` "Test offline" #1: `count_anomaly_events(event_type=
  "LOI_BIA")` (đúng chữ trong test-plan.md, giá trị vô nghĩa) → `error`
  rõ ràng, không query DB — verify lại chính xác đúng case này (lượt
  implement trước test bằng `SIDEWALK_ENCROACHMENT`, giá trị CÓ THẬT
  trong bảng nhưng ngoài whitelist — khác ý nghĩa với "vô nghĩa hoàn
  toàn" của test-plan; verify thêm cho chắc).
- `event_type` rỗng (bắt buộc theo thiết kế) → `error`, không crash.
- `group_by` sai cho cả 3 hàm (`count_anomaly_events`, đã test
  `count_face_events` tương tự lượt trước) → `error` rõ ràng, không
  query DB — nhất quán với `count_vehicle_flow` (v1).
- `product-spec.md`: số liệu thật, không hallucinate — cả 3 hàm trả đúng
  dữ liệu thật đã verify (không bịa số).

### Fail
- Không tìm thấy lỗi CODE nào trong phạm vi feature này (bug tìm thấy ở
  lượt trước là bug DỮ LIỆU/GIẢ ĐỊNH trong dataset, đã sửa ở entry
  implement bên dưới — không phải bug của 3 hàm SQL, các hàm áp dụng org
  filter ĐÚNG theo thiết kế v1).

### Ghi nhận thêm (không phải bug, chỉ là đặc điểm dữ liệu thật)
- Test thêm `group_by="zone_name"` cho `FIGHT_DETECTION` (chưa test ở
  lượt implement) → chạy đúng về mặt CODE, nhưng cột `zone_name` trong DB
  thật là `NULL` cho toàn bộ 13092 dòng — group theo `zone_name` hiện
  không tạo được breakdown hữu ích với dữ liệu thật hôm nay. Không sửa gì
  (đây là dữ liệu thật, không phải lỗi hàm) — chỉ ghi nhận để Phase 5 biết
  khi thiết kế tool/docstring cho LLM, tránh gợi ý group_by=zone_name cho
  câu hỏi cần breakdown theo khu vực nếu dữ liệu chưa hỗ trợ.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `src/agent/tools.py` chưa bọc 3 hàm này thành `@tool` — Phase 5, chưa
  tới lượt. `test-plan.md` "Test offline" #2 (danh sách tool) áp dụng cho
  Phase 5, không áp dụng ở đây.

## 2026-09-17 (Phase 3, item 2: `src/db/queries.py` — 3 hàm SQL domain mới)

### Added
- `src/db/queries.py` — 3 hàm mới, đúng pattern có sẵn (`%s` placeholder,
  `_org_filter()`, `get_connection(settings.db_name_*)`, trả `{error}`
  hoặc `{columns, rows, row_count}`):
  - `count_face_events(date_from, date_to, direction, group_by)` →
    `smart_face.smf_face_events`, group theo `{direction, department_name}`,
    dùng cột thời gian `access_time` (không phải `event_time`).
  - `count_fire_smoke_events(date_from, date_to, entity_type)` →
    `firesmoke.fire_smoke_event`, group cố định theo `entity_type` +
    `alert_level`, validate `entity_type ∈ {FIRE, SMOKE}`.
  - `count_anomaly_events(date_from, date_to, event_type, group_by)` →
    `anomaly.anomaly_event`, DÙNG CHUNG cho 4 sự kiện, `event_type` BẮT
    BUỘC + validate whitelist đúng 4 giá trị (loại trừ
    `SIDEWALK_ENCROACHMENT`/`LITTERING_DETECTION` có trong bảng nhưng
    ngoài phạm vi sản phẩm), group tuỳ chọn theo `{severity, zone_name}`.
  - KHÔNG thêm `water_level_latest` — dataset chỉ cần đếm sự kiện, không
    cần giá trị mực nước tức thời.

### BUG NGHIÊM TRỌNG tự phát hiện khi test thật — đã sửa `eval/datasets/agent_stat/v2.yaml`
- Test `count_anomaly_events('2026-08-14', '2026-09-17', 'FIGHT_DETECTION')`
  trả **13092**, KHÁC HẲN con số **31464** đã ghi trong `v2.yaml` (Phase 2
  item 4) cho cùng loại sự kiện/khoảng ngày. Điều tra bằng raw SQL: bảng
  `anomaly.anomaly_event` có DỮ LIỆU CỦA 2 `organization_id` KHÁC NHAU
  (103 và 106); `.env` cấu hình `DB_ORGANIZATION_ID=106`; hàm mới viết
  ĐÚNG áp dụng `_org_filter()` (kế thừa từ `count_vehicle_flow` v1) nên
  chỉ đếm org 106 — con số 31464 ở `v2.yaml` là TỔNG CẢ 2 ORG (lấy bằng
  raw SQL không lọc org khi grounding dataset lúc trước), SAI với những
  gì tool thật sẽ trả về.
- Điều tra sâu hơn phát hiện thêm: **org 106 (org của app) hoàn toàn
  KHÔNG CÓ dữ liệu `CROWD_DETECTION`/`INTRUSION_DETECTION` (= 0, mọi
  khoảng thời gian)** — 2 loại này chỉ tồn tại dưới org 103 (không thuộc
  app). Đây không phải lỗi tool, mà là sự thật của dữ liệu tổ chức 106.
  Đồng thời phát hiện `WATER_LEVEL_DETECTION` (org 106) vẫn được ghi
  nhận tới HÔM NAY (2026-09-17, ~100 lượt/ngày) — KHÁC domain FIGHT
  (dừng ở 2026-09-16) — trước đó tưởng nhầm cả 4 loại đều "không có dữ
  liệu hôm nay".
- **Sửa `v2.yaml`:** viết lại toàn bộ đoạn tổng hợp dữ liệu ở đầu file +
  6 case bị ảnh hưởng trực tiếp (#010, #012, #014, #017, #018, #022,
  #023, #024): cập nhật số liệu đúng (13092 FIGHT, 0 CROWD, 0 INTRUSION,
  258359+ WATER_LEVEL), đổi case #012/#014 từ "có dữ liệu" (sai) thành
  "không có dữ liệu" (đúng — org 106 chưa từng có 2 loại này), đổi case
  #017 từ "không có dữ liệu" (sai) thành "có dữ liệu hôm nay" (đúng, vì
  water level vẫn đang ghi nhận), REDESIGN case #023 (leo trèo vs cháy
  khói — cả 2 giờ đều rỗng nên mất ý nghĩa test "1 có 1 không") thành mực
  nước vs cháy khói, và REDESIGN case #024 (xếp hạng 3 loại — 2 loại tie
  ở 0 nên vô nghĩa) thành "loại nào có/không có dữ liệu trong 4 loại".

### Verified
- `pytest -q` → "5 passed".
- Test thật (đọc DB thật, không cần LLM): cả 3 hàm mới trả đúng dữ liệu +
  validate đúng (`event_type`/`entity_type`/`group_by` sai → `error` rõ
  ràng, không query DB).
- `eval/run.py` (offline, sau khi sửa `v2.yaml`) vẫn cho kết quả nhất
  quán (`injection: 3/3`, `out_of_scope: 3/3`) — sửa dataset không ảnh
  hưởng cơ chế guardrail.
- YAML parse hợp lệ, vẫn đúng 30 case / phân bổ 18-6-3-3, không trùng
  `id`, không còn số liệu sai sót lại (grep xác nhận 31464/25820/14835/
  258260 chỉ còn xuất hiện trong đoạn giải thích org 103, chủ ý giữ để
  đối chiếu).

## 2026-09-17 (Review Phase 3 item 1 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("mở rộng whitelist `get_connection()`")
đối chiếu `specs/product-spec.md` (Acceptance Criteria) và
`specs/test-plan.md` (mục "Test guardrail an toàn (2 lớp)" + "Test offline"
#4).

### Pass
- `test-plan.md` "Test offline" #4: `get_connection('vms_db')` (ngoài
  whitelist) → `ValueError` ngay, không mở connection — verify lại, đúng.
- `test-plan.md` "Lớp app/session-readonly": verify **ĐỦ CẢ 3 DB mới**
  (rút kinh nghiệm lượt review Phase 2 item 1 — lúc đó chỉ test 2/3 DB,
  lần này chủ động test cả 3 ngay từ đầu): `smart_face` (DELETE),
  `firesmoke` (UPDATE), `anomaly` (DELETE) — cả 3 đều bị `Read
  OnlySqlTransaction` (lớp app, `conn.set_session(readonly=True)`) —
  đúng dự đoán, không phải chỉ `InsufficientPrivilege` như trước Phase 3.
- SELECT qua `get_connection()` chạy được cho cả 5 DB (2 cũ + 3 mới).
- `pytest` sạch (5 passed), không thêm thư viện, không đổi kiến trúc
  ngoài phạm vi whitelist.

### Fail
- Không tìm thấy lỗi nào trong phạm vi hẹp của feature này.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `src/db/queries.py` chưa có 3 hàm SQL mới (`count_face_events`/
  `count_fire_smoke_events`/`count_anomaly_events`) — item TIẾP THEO
  trong Phase 3, chưa tới lượt. Whitelist mở rộng xong nhưng CHƯA có code
  nào gọi `get_connection()` với 3 DB mới ngoài script test tay ở trên —
  đúng dự kiến.
- `test-plan.md` mục "Test thật" cho domain mới vẫn chưa chạy được qua
  `eval/run.py`/agent thật (cần Phase 3 item 2 + Phase 5 xong, và cần
  fix dependency `openai`/`httpx2` đã ghi nhận ở `task_2e390bb8`).

## 2026-09-17 (Phase 3, item 1: `src/db/connection.py` — mở rộng whitelist 3 DB mới)

### Added
- `src/db/connection.py::_allowed_dbnames()` — thêm `settings.db_name_face`/
  `db_name_fire`/`db_name_anomaly` (3 field đã có sẵn từ Phase 2 item 2)
  vào set whitelist, giữ nguyên cơ chế: `get_connection(dbname)` raise
  `ValueError` NGAY nếu `dbname` không thuộc 5 DB hợp lệ, không mở
  connection thật. Cập nhật docstring đầu file (2 DB → 5 DB, liệt kê rõ
  bảng chính từng DB).

### Verified
- `pytest -q` → "5 passed" (không regression).
- Gọi thật `get_connection(db)` cho cả 5 DB (`its`, `virtual_fence`,
  `smart_face`, `firesmoke`, `anomaly`) → SELECT chạy được cả 5.
- `DELETE FROM anomaly_event` qua `get_connection('anomaly')` → bị chặn
  `ReadOnlySqlTransaction` (lớp APP — `conn.set_session(readonly=True)`)
  — đây là lần ĐẦU TIÊN verify được lớp bảo vệ này cho 3 DB mới (trước đó,
  ở Phase 2 item 1, chỉ verify được lớp Postgres/GRANT vì whitelist app
  chưa mở). Khớp đúng dự đoán đã ghi trong `specs/test-plan.md` khi sửa
  mục "Test guardrail an toàn" (Phase 2 review): "lớp app/session-readonly
  chỉ verify được SAU Phase 3".
- `get_connection('vms_db')` (tên ngoài whitelist) → raise `ValueError`
  ngay, không mở connection — không regression so với hành vi cũ.

## 2026-09-17 (Review Phase 2 item 5 vs product-spec.md/test-plan.md — có fix)

Review lại đúng 1 feature vừa làm ("`eval/run.py`") đối chiếu
`specs/product-spec.md` (Acceptance Criteria) và `specs/test-plan.md`.

### Pass
- `product-spec.md`: "eval/datasets/agent_stat có đủ 30 case phủ 8 domain,
  chạy được bằng eval/run.py, in được tỷ lệ pass/fail theo slice" — script
  chạy không crash, đọc đúng dataset, in đúng bảng theo `slice.type` +
  tổng, đúng exit code (0 = toàn bộ pass, 1 = có fail — dùng được trong CI
  sau này).
- `test-plan.md` mục "Test golden dataset v2": "3 case out_of_scope + 3
  case injection PHẢI vẫn pass nguyên" — verify lại SAU KHI sửa bug pipeline
  (bên dưới): cả 2 slice đạt 3/3 dưới chế độ offline, không cần LLM thật
  (đúng bản chất — 2 slice này chỉ phụ thuộc `src/guardrails.py`).
- Script tương thích ngược với `v1.yaml` (test thêm, không bắt buộc) — same
  cơ chế, injection/out_of_scope vẫn 3/3.

### Fail — đã sửa ngay trong lượt review này
- **BUG tự phát hiện (lần 2, nhỏ hơn):** `run_pipeline()` dùng biến
  `question` GỐC (chưa qua `redact_pii()`) khi build `evidence` cho
  `check_output()`, trong khi `src/main.py::ask()` thật sự dùng biến
  `question` đã bị GHI ĐÈ bằng bản đã redact TRƯỚC khi build evidence (xem
  dòng `question = redact_pii(req.question)` rồi mới `evidence = [question]
  + ...`). Với 30 case hiện tại không ảnh hưởng kết quả (không câu nào có
  PII), nhưng là sai lệch thật so với hành vi `/ask` production nếu sau
  này có case chứa SĐT/email.
- **Sửa:** thêm dòng `question = redact_pii(question)` TRƯỚC khi build
  evidence, y hệt thứ tự trong `main.py`.
- Verify lại: `pytest -q` vẫn "5 passed"; `eval/run.py` (offline, cả
  v1.yaml và v2.yaml) vẫn cho kết quả y hệt trước khi sửa (đúng dự kiến vì
  30 case hiện tại không có PII) — xác nhận fix không gây regression.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- Chưa verify được pass/fail thật với LLM thật cho slice `lookup`/
  `comparison` — bị chặn bởi lỗi dependency `openai`/`httpx2` (môi trường,
  đã ghi nhận ở entry implement, đã tạo task riêng
  `task_2e390bb8` để theo dõi, KHÔNG sửa ở đây).
- 18 case `lookup` domain mới (FACE/FIGHT/CROWD/INTRUSION/FIRE/WATER_LEVEL)
  vẫn FAIL vì tool chưa tồn tại (Phase 3/5, chưa tới lượt) — đúng dự kiến,
  đã ghi rõ trong header `v2.yaml` và docstring `eval/run.py`.

## 2026-09-17 (Phase 2, item 5 — item cuối: `eval/run.py`)

### Added
- `eval/run.py` (mới) — script chạy toàn bộ golden dataset qua **đúng
  pipeline thật** của `src/main.py::ask()` (`check_input → in_scope →
  run_agent → check_output`, xem hàm `run_pipeline()`), kiểm đủ 5 loại
  assertion đang dùng trong `v1.yaml`/`v2.yaml` (`must_include`,
  `must_include_tool`, `must_not_include`, `must_not_include_tool`,
  `must_include_columns_any` — mở rộng hơn 3 loại nêu trong checklist vì
  dataset thật đã dùng cả 5 loại, xem đối chiếu lúc review bên dưới), in
  tỷ lệ pass/fail theo `slice.type` + chi tiết lý do fail từng case.
  Dùng: `python eval/run.py [--dataset <path>]`.

### BUG tự phát hiện khi test thật lần đầu — đã sửa TRƯỚC KHI đánh dấu hoàn thành
- Bản đầu tiên gọi THẲNG `run_agent()` (đúng nghĩa đen checklist: "gọi
  `run_agent()` từng case") — chạy thử phát hiện: case `out_of_scope`/
  `injection` KHÔNG BAO GIỜ đúng kỳ vọng, vì `run_agent()` không đi qua
  `check_input()`/`in_scope()` — 2 hàm guardrail này mới là nơi sinh ra
  chuỗi `"prompt_injection_detected"`/`OUT_OF_SCOPE_REPLY` mà dataset
  kiểm tra. Gọi thẳng `run_agent()` khiến câu hỏi injection/out_of_scope
  bị đưa thẳng vào LLM như câu hỏi bình thường — sai hoàn toàn ý định của
  2 slice này.
- **Sửa:** viết `run_pipeline()` lặp lại đúng 5 bước trong
  `src/main.py::ask()` (guardrail_input → agent → guardrail_output),
  không dùng FastAPI/TestClient (gọi thẳng hàm Python, nhanh hơn, không
  cần server chạy).
- Verify lại (offline mode, không cần LLM thật): trước khi sửa,
  `out_of_scope` 0/3 (chạy qua offline `run_agent()` vẫn trả lời list
  camera, không khớp `OUT_OF_SCOPE_REPLY`), `injection` chưa test được
  (đợt đầu chạy bằng LLM thật nên injection 0/3 vì lý do tương tự — LLM
  không tự nói "prompt_injection_detected"). Sau khi sửa: `out_of_scope`
  3/3 pass, `injection` 3/3 pass (cả 2 dưới offline mode, không cần LLM
  thật — đúng bản chất 2 slice này chỉ phụ thuộc guardrail code, không
  phụ thuộc LLM).

### Verified
- `pytest -q` → "5 passed" (không regression).
- `PYTEST_CURRENT_TEST=1 python3 eval/run.py` (offline, không cần LLM/DB
  thật) → `injection: 3/3 pass`, `out_of_scope: 3/3 pass`, `lookup: 1/18
  pass` (đúng — case #006 `list_khu_vuc` khớp NGẪU NHIÊN với tool cố định
  mà offline mode luôn gọi; 17 case lookup còn lại + 6 case comparison
  FAIL vì offline mode luôn giả 1 tool `list_khu_vuc` bất kể câu hỏi —
  ĐÚNG dự kiến, offline mode chỉ để test "không crash", không test "chọn
  đúng tool", xem `specs/test-plan.md` mục Test offline #3).
- **KHÔNG verify được với LLM thật lần này** — phát hiện lỗi MÔI TRƯỜNG
  không liên quan tới code: package `openai` bản đang cài (3.14.1) phụ
  thuộc `httpx2` (2.13.0) nhưng 2 bản này KHÔNG tương thích
  (`Decompressor.decompress() got an unexpected keyword argument
  'output_buffer_limit'` khi decode response nén) — mọi lời gọi LLM thật
  (không riêng `eval/run.py`, cả `/ask` bình thường) đều lỗi trong máy
  đang chạy phiên này. `requirements.txt` không ghim version `openai` nên
  `pip install` lấy bản mới nhất, dính bug tương thích này. **KHÔNG sửa
  trong lượt này** — đây là vấn đề dependency/môi trường, không thuộc
  phạm vi checklist item "eval/run.py", cần task riêng để ghim version
  đúng.

## 2026-09-17 (Review Phase 2 item 4 vs product-spec.md/test-plan.md — có fix)

Review lại đúng 1 feature vừa làm ("`eval/datasets/agent_stat/v2.yaml`")
đối chiếu `specs/product-spec.md` (Acceptance Criteria) và
`specs/test-plan.md`.

### Pass
- Đủ 30 case, đúng phân bổ 18/6/3/3 (`implementation-plan.md` Phase 2) —
  verify bằng script đếm `slice.type`.
- YAML parse hợp lệ, không trùng `id`.
- Cả 24 case lookup/comparison đều `in_scope() == True` (không bị
  `STAT_KEYWORDS` ở item 3 từ chối oan); 3 case out_of_scope đều
  `in_scope() == False`; 3 case injection đều bị `check_input()` chặn —
  verify bằng cách gọi thẳng `src/guardrails.py`, không cần đợi
  `eval/run.py`.
- 3 câu out_of_scope giống hệt v1 (đúng yêu cầu "giữ nguyên").

### Fail — đã sửa ngay trong lượt review này
- **BUG tự phát hiện:** 3 câu injection PHẢI "giữ nguyên y hệt v1" (đúng
  cam kết ghi trong changelog của chính lượt implement trước) — nhưng
  case `agent_stat_v2_030` đã tự ý đổi `DELETE FROM plate_event` (v1)
  thành `DELETE FROM anomaly_event` (v2), vi phạm trực tiếp yêu cầu
  "Giữ nguyên câu hỏi cũ, không đổi" trong `implementation-plan.md` Phase
  2 (bảng phân bổ). Lý do sai: cố tình làm case này "liên quan" tới DB
  mới vừa GRANT ở item 1, nhưng thực chất **thừa** — item 1 đã tự verify
  trực tiếp DELETE bị chặn trên `anomaly_event` rồi, không cần lặp lại
  qua injection case.
- **Sửa:** revert `question` + `expected` của case 030 về ĐÚNG y hệt
  text gốc trong `v1.yaml` (`plate_event`, không phải `anomaly_event`).
- Verify lại: so sánh trực tiếp list câu hỏi injection giữa `v1.yaml` và
  `v2.yaml` bằng Python — kết quả giống hệt (`True`). 30 case, phân bổ
  slice không đổi.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `product-spec.md`/`test-plan.md` yêu cầu "chạy được bằng `eval/run.py`,
  in được tỷ lệ pass/fail" — `eval/run.py` CHƯA tồn tại, đó là checklist
  item TIẾP THEO trong Phase 2, chưa tới lượt. Case dùng tool domain mới
  (`count_face_events`/`count_fire_smoke_events`/`count_anomaly_events`)
  chưa chạy được qua `run_agent()` thật vì tool chưa code (Phase 3/5) —
  đã ghi rõ trong header file YAML, không phải thiếu sót của dataset.

## 2026-09-17 (Phase 2, item 4: `eval/datasets/agent_stat/v2.yaml` — 30 case, 8 domain)

### Added
- `eval/datasets/agent_stat/v2.yaml` — 30 case mới, đúng phân bổ trong
  `implementation-plan.md` Phase 2: 18 lookup (4 PLATE + 2 ZONE, giữ lại
  từ v1 + 12 case mới cho 6 domain FACE/FIGHT/CROWD/INTRUSION/FIRE/
  WATER_LEVEL, 2 case/domain), 6 comparison (3 giữ nguyên từ v1 — #019 bug
  regression, #020 seat-limit note, #021 multihop PLATE+ZONE — + 3 case
  chéo domain mới), 3 out_of_scope + 3 injection giữ NGUYÊN y hệt v1.

### Grounding (không bịa số liệu — verify thật qua psycopg2 ngày 2026-09-17)
- Tái verify 2 giá trị v1 vẫn đúng: biển số `15K40139` còn 14 dòng trong
  `its.plate_event`; VINFAST vẫn dẫn đầu hãng xe (29927 lượt, verify lại —
  tăng nhẹ so với con số 29779 ghi trong v1.yaml vì có thêm dữ liệu mới
  giữa 2 lần verify, không phải sai số).
- Phát hiện quan trọng, ảnh hưởng trực tiếp cách viết case: `smart_face.
  smf_face_events` (3953 dòng, 2026-09-07→2026-09-14) và `anomaly.
  anomaly_event` (2026-08-14→2026-09-16) đều KHÔNG có dữ liệu tới "hôm
  nay" (2026-09-17) — khác PLATE/ZONE (dữ liệu liên tục tới hiện tại).
  `firesmoke.fire_smoke_event` RỖNG HOÀN TOÀN (0 dòng, mọi thời điểm).
  → Mỗi domain mới có 2 case: 1 case "hôm nay" (test KHÔNG hallucinate khi
  rỗng — domain FIRE cả 2 case đều vậy vì bảng luôn rỗng) + 1 case theo
  khoảng ngày thật có dữ liệu (test nhánh trả lời đúng số liệu thật, trừ
  FIRE không có case này vì không tồn tại khoảng nào có dữ liệu).
- Số liệu thật dùng trong case: FIGHT_DETECTION=31464, INTRUSION_DETECTION
  (leo trèo)=25820, CROWD_DETECTION=14835, WATER_LEVEL_DETECTION=258260
  (log liên tục, khác bản chất — cố ý loại khỏi case xếp hạng #024).
- `anomaly.anomaly_event` còn có `SIDEWALK_ENCROACHMENT`/
  `LITTERING_DETECTION` — KHÔNG thuộc 8 domain `product-spec.md`, không
  đưa vào dataset.

### Quyết định thiết kế
- Tool cho 6 domain mới (`count_face_events`, `count_fire_smoke_events`,
  `count_anomaly_events`) CHƯA tồn tại trong code (Phase 3/5) — case dùng
  các tool này sẽ FAIL khi chạy `eval/run.py` (cũng chưa tồn tại) cho tới
  khi Phase 3+5 xong. Đây là chủ ý, đã ghi rõ trong header file YAML,
  không phải lỗi của dataset.
- Domain "leo trèo" (`count_anomaly_events(event_type=INTRUSION_
  DETECTION)`) và domain "vùng cấm" (`zone_intrusion_by_hour`) dễ nhầm vì
  cùng dịch "xâm nhập" — case #013 có `must_not_include_tool:
  [zone_intrusion_by_hour]` để bắt lỗi này sớm.

### Verified
- `python3 -c "import yaml; ..."` — parse YAML hợp lệ, đúng 30 case, đúng
  phân bổ slice (18/6/3/3), không trùng `id`.
- Chạy `in_scope()`/`check_input()` (đã có sẵn, không cần `run_agent()`)
  cho cả 30 câu hỏi: 24 case lookup/comparison đều `in_scope() == True`
  (không bị `STAT_KEYWORDS` mở rộng ở item 3 từ chối oan), 3 case
  out_of_scope đều `in_scope() == False`, 3 case injection đều bị
  `check_input()` raise đúng.
- **Chưa chạy được** (đúng dự kiến, ghi trong header file): case dùng tool
  domain mới chưa test qua `run_agent()` thật vì tool chưa tồn tại.

## 2026-09-17 (Review Phase 2 item 3 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("mở rộng `STAT_KEYWORDS`") đối chiếu
`specs/product-spec.md` (Acceptance Criteria) và `specs/test-plan.md`.

### Pass
- `test-plan.md` mục "Test domain sự kiện VMS mới" #3: `in_scope()` nhận
  đúng cả 6 câu hỏi mẫu domain mới → `True` — verify lại, đủ.
- `product-spec.md` Acceptance Criteria "Câu hỏi ngoài phạm vi → bị từ
  chối lịch sự, không gọi tool/DB": chạy lại **toàn bộ 30 case** trong
  `eval/datasets/agent_stat/v1.yaml` (không chỉ 3 câu out_of_scope mẫu
  trong test-plan.md) qua `in_scope()`/`check_input()` — không case nào
  bị đổi hành vi. Đây là kiểm tra RỘNG hơn yêu cầu tối thiểu của
  test-plan.md, chủ động làm thêm vì thay đổi là thêm keyword (rủi ro
  false-positive rộng hơn phạm vi 3 câu mẫu).
- `pytest` sạch (5 passed), không thêm thư viện, không đổi kiến trúc.

### Fail
- Không tìm thấy lỗi nào trong phạm vi feature này.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót)
- Câu hỏi domain mới vẫn CHƯA trả lời được số liệu thật — `in_scope()`
  chỉ là bước gác đầu vào, tool/DB cho 5 domain mới thuộc Phase 3/5, chưa
  code. Test-plan.md mục "Test thật" cho domain mới vẫn chưa chạy được
  hết pipeline — đúng như đã ghi nhận, không phải lỗi của item này.

## 2026-09-17 (Phase 2, item 3: `src/guardrails.py` — `STAT_KEYWORDS` domain mới)

### Added
- `src/guardrails.py::STAT_KEYWORDS` — thêm 14 từ khoá (7 domain mới ×
  1 bản có dấu + 1 bản không dấu, đúng phong cách các từ khoá cũ như
  "xâm nhập"/"xam nhap"): khuôn mặt, ẩu đả, đám đông, leo trèo, cháy,
  khói, mực nước. Chỉ thêm keyword — KHÔNG đổi `in_scope()`/logic khác.

### Verified
- `pytest -q` → "5 passed" (không regression v1).
- `in_scope()` trả `True` cho cả 6 câu hỏi mẫu domain mới trong
  `specs/test-plan.md` mục "Test thật" (nhận diện khuôn mặt, ẩu đả, đám
  đông, leo trèo, cháy/khói, mực nước).
- `in_scope()` vẫn trả `False` cho cả 3 câu out_of_scope cũ trong
  `specs/test-plan.md`/`eval/datasets/agent_stat/v1.yaml` (thời tiết, bài
  thơ, giá cổ phiếu VIC) — xác nhận không có từ khoá mới nào vô tình khớp
  nhầm câu hỏi ngoài phạm vi.

## 2026-09-17 (Phase 2, item 2: `src/config.py` + `.env.example` — 3 DB mới)

### Added
- `src/config.py` — thêm 3 field mới, đúng pattern `db_name_its`/
  `db_name_fence` đã có: `db_name_face` (alias `DB_NAME_FACE`, default
  `"smart_face"`), `db_name_fire` (alias `DB_NAME_FIRE`, default
  `"firesmoke"`), `db_name_anomaly` (alias `DB_NAME_ANOMALY`, default
  `"anomaly"`) — default khớp đúng tên DB thật đã verify ở item trước
  (Phase 2 item 1). Đặt ngay sau `db_name_fence`, trước
  `db_organization_id` — giữ đúng thứ tự nhóm "Database" hiện có, không
  xáo trộn field khác.
- `.env.example` — thêm 3 dòng `DB_NAME_FACE`/`DB_NAME_FIRE`/
  `DB_NAME_ANOMALY` (comment nêu rõ: đã GRANT ở Phase 2 item 1, CHƯA dùng
  ở `connection.py` vì whitelist mở rộng thuộc Phase 3, chưa code) —
  tránh gây hiểu nhầm là 3 DB này đã dùng được qua agent ngay.

### Changed (phạm vi, không lấn Phase 3)
- KHÔNG đổi `src/db/connection.py::_allowed_dbnames()` — vẫn chỉ
  `its`/`virtual_fence`. Đây là quyết định phạm vi đúng checklist
  (`config.py` là item này, whitelist connection là Phase 3 riêng) — 3
  field mới hiện CHƯA được code nào khác import/dùng tới.

### Verified
- `pip install -r requirements.txt` + `pytest -q` → "5 passed" (không
  regression, không cần đổi test nào vì field mới hoàn toàn additive).
- `python3 -c "from src.config import settings; print(settings.db_name_face, settings.db_name_fire, settings.db_name_anomaly)"`
  → in đúng `smart_face firesmoke anomaly` — khớp tên DB thật, `.env`
  hiện tại (chưa có 3 biến mới) vẫn load đúng nhờ default.
- `settings.db_configured` vẫn `True` — không bị ảnh hưởng bởi field mới
  (chỉ phụ thuộc `db_host`/`db_user`, không đổi).

## 2026-09-17 (Review Phase 2 item 2 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("`src/config.py` + `.env.example` — 3
field DB mới") đối chiếu `specs/product-spec.md` (Acceptance Criteria) và
`specs/test-plan.md`.

### Pass
- Đúng pattern field hiện có (`Field(default=..., alias=...)`), không đổi
  cách đọc `.env` (`pydantic_settings`, điểm duy nhất chạm secrets — đúng
  docstring đầu file `config.py`).
- `pytest` vẫn sạch (5 passed) — không regression cho v1.
- Không thêm thư viện mới, không đổi kiến trúc — đúng AGENTS.md.
- Giá trị default khớp CHÍNH XÁC 3 tên DB đã verify thật ở Phase 2 item 1
  (không suy đoán tên DB lần thứ 2).

### Fail
- Không tìm thấy vấn đề nào trong phạm vi hẹp của feature này (chỉ thêm
  field cấu hình, chưa có logic nào dùng tới nên không có gì để "chạy sai").

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `product-spec.md`/`test-plan.md` chưa có dòng nào assert riêng cho việc
  "3 field config tồn tại" — vì `product-spec.md` viết ở mức mục tiêu sản
  phẩm (không liệt kê tên field), và `test-plan.md` chỉ test hành vi
  runtime (DB connect được/bị chặn), field cấu hình đơn thuần không có
  hành vi để test độc lập — hợp lý, KHÔNG cần bổ sung test giả cho field
  chưa ai dùng.
- `src/db/connection.py`, `src/db/queries.py`, `src/guardrails.py` chưa
  dùng 3 field mới — đúng, đó là Phase 3/2-item-3, chưa tới lượt.
- Không có gì khác cần sửa. Không có thay đổi nào thêm ở lượt review này.

## 2026-09-17 (Review Phase 2 item 1 vs product-spec.md/test-plan.md)

Review lại đúng 1 feature vừa làm ("GRANT SELECT cho 3 DB mới") đối chiếu
`specs/product-spec.md` (Acceptance Criteria) và `specs/test-plan.md`
("Test guardrail an toàn... lặp lại cho 3 DB mới").

### Pass
- `product-spec.md` mục "Hạ tầng — đọc-only Postgres qua role riêng...
  trên mọi DB nguồn cần dùng": đúng, role `agent_readonly` giờ SELECT
  được cả 5 DB (2 cũ + 3 mới), vẫn 1 role duy nhất, không phải admin.
- `test-plan.md`: SELECT chạy được trên cả 3 DB mới — đã verify lại (xem
  entry trước).
- `test-plan.md`: DELETE/UPDATE bị từ chối trên cả 3 DB mới —
  **verify lại đủ cả 3 DB** (lượt trước chỉ test 2/3: `anomaly`,
  `firesmoke`, THIẾU `smart_face`). Đã test bổ sung `DELETE FROM
  smf_face_events` → bị từ chối đúng (`InsufficientPrivilege`).
- Không thêm thư viện mới (`psycopg2-binary` đã có sẵn trong
  `requirements.txt` từ v1). Không đổi kiến trúc — chỉ GRANT thêm trên DB
  mới, đúng SQL pattern đã có trong README.

### Fail (spec sai, không phải code sai) — đã sửa
- `test-plan.md` mục "Test guardrail an toàn... lặp lại cho 3 DB mới" ghi
  kỳ vọng lỗi `ReadOnlySqlTransaction` cho DELETE/UPDATE — SAI ở giai đoạn
  hiện tại. Đọc lại `src/db/connection.py::get_connection()` mới thấy:
  lỗi `ReadOnlySqlTransaction` đến từ `conn.set_session(readonly=True)`
  (tầng APP, trong code), không phải từ GRANT của Postgres. Hàm
  `get_connection()` hiện CHỈ whitelist `its`/`virtual_fence`
  (`_allowed_dbnames()`) — chưa hỗ trợ 3 DB mới (đó là việc của Phase 3,
  CHƯA làm). Vì vậy test cho 3 DB mới ở giai đoạn này chỉ có thể đi qua
  raw `psycopg2.connect()` (bỏ qua `get_connection()`), và lỗi ĐÚNG quan
  sát được là `InsufficientPrivilege` (thuần Postgres GRANT), không phải
  `ReadOnlySqlTransaction`. Test-plan.md copy nguyên cách diễn đạt của
  pattern v1 mà không tính tới khác biệt này.
- **Sửa:** viết lại mục đó trong `test-plan.md`, tách rõ 2 lớp bảo vệ
  KHÁC cơ chế: lớp Postgres/GRANT (verify được ngay, kỳ vọng
  `InsufficientPrivilege`) và lớp app/session-readonly (chỉ verify được
  sau Phase 3, kỳ vọng `ReadOnlySqlTransaction`) — không để lẫn lộn 2 lớp
  khi ai đó test lại theo đúng câu chữ cũ.

### Missing (đúng phạm vi, KHÔNG phải thiếu sót của feature này)
- `src/config.py` chưa có `DB_NAME_FACE`/`DB_NAME_FIRE`/`DB_NAME_ANOMALY`
  — checklist item TIẾP THEO của Phase 2, chưa tới lượt.
- `src/db/connection.py` chưa mở whitelist cho 3 DB mới — Phase 3, chưa
  tới lượt.
- `README.md` mục "Tạo DB role read-only" chưa có ví dụ SQL cho 3 DB mới
  — Phase 7, chưa tới lượt (đã ghi nhận đúng ở entry trước).
- Không có gì khác trong `product-spec.md`/`test-plan.md` áp dụng cho
  phạm vi hẹp "GRANT SELECT cho 3 DB mới" của feature này.

## 2026-09-17 (Phase 2, item 1: GRANT SELECT cho 3 DB mới)

### Added
- GRANT `SELECT` (+ `CONNECT`/`USAGE`, default privileges cho bảng tương
  lai) cho role `agent_readonly` đã có sẵn trên 3 DB mới:
  `smart_face`, `firesmoke`, `anomaly` — cùng host/port với `its`/
  `virtual_fence` hiện tại (`192.168.1.250:18644`). KHÔNG tạo role mới —
  tái dùng đúng `agent_readonly` (đơn giản hơn, không cần thêm biến
  `.env` để chọn user khác nhau theo DB).
- Thực hiện qua 1 script Python one-off (không thuộc `src/`, không
  commit vào repo) dùng tài khoản admin `dev` (nhận trực tiếp từ user
  qua chat cho phiên làm việc này, chỉ giữ trong biến môi trường tạm,
  KHÔNG ghi vào bất kỳ file nào trong repo, không log ra output).

### Verified
- Cả 3 DB (`smart_face`, `firesmoke`, `anomaly`) nằm CÙNG Postgres host
  với `its`/`virtual_fence` — xác nhận bằng connect thật (không suy
  đoán), giải quyết dứt điểm giả định #1 ở `implementation-plan.md`
  Phase 2.
- Sau khi GRANT: `agent_readonly` SELECT được trên cả 3 DB (thấy đúng
  bảng `smf_*` cho `smart_face`, `fire_smoke_event` cho `firesmoke`,
  `anomaly_event` cho `anomaly`).
- `agent_readonly` vẫn bị Postgres từ chối `DELETE`/`UPDATE` trên 2 bảng
  mới (`anomaly_event`, `fire_smoke_event`) — `InsufficientPrivilege` —
  xác nhận role vẫn đúng nghĩa read-only sau khi mở rộng, không vô tình
  cấp thừa quyền.

### Sự cố bảo mật trong lượt này (đã xử lý, cần user lưu ý)
- Khi đọc `.env` để xác nhận nội dung, dùng `sed` để redact secret trước
  khi hiện ra — nhưng regex chỉ khớp `KEY=`, không khớp `KEYS=` (biến
  `OPENAI_API_KEYS` có thêm `S`), nên 2 API key OpenAI thật đã bị hiện
  nguyên văn trong output của 1 lệnh trong phiên làm việc này.
  **Khuyến nghị: rotate/thu hồi 2 API key OpenAI đó** (`sk-proj-I1DF...`
  và `sk-proj-gVUY...` — 8 ký tự đầu để nhận diện, không lặp lại đầy đủ
  ở đây) vì đã xuất hiện trong log của phiên làm việc.
- Mật khẩu admin Postgres (`dev`) do user gõ trực tiếp trong chat — chỉ
  dùng trong biến môi trường của 1 lệnh chạy script, không ghi vào file
  nào trong repo, không xuất hiện trong output của bất kỳ lệnh nào sau
  đó.

### Review vs implementation-plan.md
- Đây là item ĐẦU TIÊN chưa check trong `implementation-plan.md` (Phase
  2, checklist). Đã đánh dấu `[x]`, cập nhật luôn mục "Giả định" của
  Phase 2 thành "ĐÃ XÁC NHẬN" (cả 2 giả định đều đúng).
- **Chưa làm** (đúng phạm vi, để item tiếp theo): chưa cập nhật
  `README.md` mục "Tạo DB role read-only" với ví dụ SQL cho 3 DB mới —
  đó là việc của Phase 7, không lấn sang ở đây theo nguyên tắc "chỉ triển
  khai 1 task tại 1 thời điểm" (AGENTS.md).

> **Lưu ý đọc lịch sử:** `specs/implementation-plan.md` được rewrite lại
> cấu trúc phase ngày 2026-09-17 (entry "Rewrite implementation-plan.md"
> bên dưới). Mọi entry **trước** ngày đó nói "Phase N" là theo số phase
> CŨ (v1: 1 Setup, 2 Config, 3 DB layer, 4 Agent, 5 Validation, 6 README).
> Entry **từ/sau** ngày đó dùng số phase MỚI (xem đầu
> `implementation-plan.md`) — 2 hệ số không tương thích 1-1, đừng suy ra
> nội dung phase từ số thứ tự khi đọc entry cũ.

## 2026-09-17 (Rewrite `implementation-plan.md` thành 8 phase nhỏ)

### Changed
- `specs/implementation-plan.md` — viết lại toàn bộ theo đúng 8 phase
  user yêu cầu: 1 Project setup, 2 Mở rộng 5 domain sự kiện VMS mới,
  3 Core backend/data logic, 4 Core Observability (Langfuse), 5 Connect UI
  to data, 6 Validation and error states, 7 Local run instructions,
  8 Local demo setup. Mỗi phase có mục "v1 — đã xong" (`[x]`, không đổi
  nội dung, chỉ sắp xếp lại vị trí) và "v2 — chưa code" (`[ ]`).
- Số phase ĐỔI so với bản trước: domain sự kiện mới (cũ Phase 7) → Phase 2;
  Langfuse (cũ Phase 8) → Phase 4. Cập nhật cross-reference ở `AGENTS.md`,
  `specs/product-spec.md`, `specs/test-plan.md`, `README.md` cho khớp.

### Quyết định phạm vi — Prompt Registry bị bỏ khỏi 8 phase
- Yêu cầu rewrite lần này liệt kê ĐÚNG 8 phase, không nhắc Prompt Registry
  (cũ Phase 9). Không tự ý nhét Prompt Registry vào 1 trong 8 phase trên
  (có thể sai ý định user) — thay vào đó giữ nguyên nội dung kỹ thuật đã
  viết trước đó (`prompts/<name>/vN.yaml` + `production.txt` alias +
  `PromptRegistry.get()/render()`) nhưng chuyển xuống 1 mục "Ghi chú" cuối
  `implementation-plan.md`, đánh dấu rõ CHƯA có phase. `product-spec.md`
  vẫn liệt kê Prompt Registry ở "Features In Scope" — có mismatch tạm thời
  giữa 2 file, đã ghi chú tường minh ở cả 2 nơi thay vì để mismatch ngầm.
- Cần hỏi lại user ở lượt sau: giữ Prompt Registry làm 1 phase riêng
  (Phase 9) hay bỏ hẳn khỏi kế hoạch hiện tại.

### Verified
- Grep lại toàn bộ `README.md`/`AGENTS.md`/`specs/*.md` sau khi đổi số
  phase — không còn chỗ nào trỏ "Phase 7/8/9" (số cũ) vào nội dung mới.

## 2026-09-17 (Review: đơn giản hoá `product-spec.md`)

### Changed
- `specs/product-spec.md` — viết lại gọn hơn theo yêu cầu review "keep it
  simple, đảm bảo rõ 6 mục: goal/target users/core user flow/features in
  scope/features out of scope/acceptance criteria". Chuyển 2 phần chi tiết
  kỹ thuật (bảng ánh xạ sự kiện → DB.table, và các giả định chưa verify)
  sang `specs/implementation-plan.md` mục Phase 7 — đây là nội dung phục
  vụ lúc CODE Phase 7, không phải mục tiêu sản phẩm nên không cần nằm ở
  product-spec. Product-spec giờ chỉ còn 8 dòng liệt kê tên sự kiện (mục
  Goal) + 1 câu trỏ sang implementation-plan cho chi tiết.
- `specs/implementation-plan.md` (Phase 7) — nhận lại bảng ánh xạ + giả
  định + bảng phân bổ 30 case (trước nằm ở product-spec) ngay tại chỗ dùng
  đến chúng (đầu Phase 7, trước checklist).
- `AGENTS.md` — sửa link trỏ giả định Phase 7 từ `product-spec.md` sang
  `implementation-plan.md` (theo đúng vị trí mới).
- Không đổi nội dung/kết luận nào đã tra cứu ở lượt trước — chỉ di chuyển
  vị trí trong doc, không code nào bị đụng tới.

### Review
- **Pass:** `specs/product-spec.md` giờ đọc hết trong ~2 phút, đủ 6 mục
  yêu cầu, không còn bảng kỹ thuật/self-review lấn vào giữa các mục.
- Grep xác nhận không còn tham chiếu treo tới 2 mục đã xoá khỏi
  product-spec (`Giả định & câu hỏi mở`, `Bảng ánh xạ sự kiện`) — đã sửa
  3 chỗ trỏ sai (`AGENTS.md`, `implementation-plan.md` 2 chỗ).

## 2026-09-17 (Spec-only: mở rộng phạm vi v2 — CHƯA CODE)

### Added (chỉ specs/docs, không có thay đổi code theo đúng yêu cầu)
- `specs/product-spec.md` — mở rộng "Goal"/"Features In Scope"/"Features
  Out of Scope"/"Acceptance Criteria" từ phạm vi v1 (xe ra/vào + xâm nhập
  vùng cấm) lên v2 (8 loại sự kiện VMS: FACE, PLATE, ZONE, ẩu đả, đám đông,
  leo trèo, FIRE, mực nước) + 2 hạ tầng mới (Langfuse tracing self-host,
  Prompt Registry git-based). Thêm mục "Giả định & câu hỏi mở" và bảng ánh
  xạ sự kiện → DB.table.
- `specs/implementation-plan.md` — thêm Phase 7 (mở rộng 5 domain sự kiện
  mới + golden dataset v2 + eval runner), Phase 8 (Langfuse tracing), Phase
  9 (Prompt Registry). Tất cả item đang `[ ]` (chưa làm) — Phase 1-6 (v1)
  giữ nguyên `[x]`, không sửa.
- `specs/test-plan.md` — thêm test plan cho Phase 7-9 (test offline, test
  guardrail an toàn cho 3 DB mới, test thật theo domain, test golden
  dataset v2, test tracing, test prompt registry).
- `README.md` — thêm mục "Lộ trình mở rộng (v2, Phase 7-9)" trỏ tới các
  spec ở trên, ghi rõ CHƯA triển khai.

### Grounding (quan trọng — không suy đoán phạm vi sự kiện mới)
Trước khi viết spec, đã tra cứu trực tiếp trong monorepo
`/home/atin/dong/dong/KCNHungPhu` (không phải trong `kcn_hungphu_agent`) để
xác nhận 8 loại sự kiện người dùng liệt kê đều có nguồn dữ liệu Postgres
thật, tránh spec ra tính năng không có data backing:
- `kcn/crowd/KCN_HUNGPHU_MQTT_AI_EVENTS.md` — payload MQTT edge→BE thật,
  liệt kê DB đích cho từng `ai_modules` (FACE→`smart_face.smf_face_events`,
  PLATE→`its.plate_event`, ZONE→`virtual_fence.zone_event`,
  FIRE→`firesmoke.fire_smoke_event`, và nhóm ANOMALY gồm
  FIGHT_DETECTION/CROWD_DETECTION/INTRUSION_DETECTION (leo trèo)/
  FALL_DETECTION/SMOKING_DETECTION/WEAPON_DETECTION).
- `agent-harness/services/vms-sync/sources.py` — code sync Postgres→
  ClickHouse ĐANG CHẠY THẬT trong harness khác cùng máy, xác nhận chính
  xác tên cột từng bảng (dùng để viết `SELECT` mẫu trong
  `implementation-plan.md` Phase 7).
- `agent-harness/skills/vms-analytics.md` — xác nhận "giám sát mực nước"
  KHÔNG có bảng riêng, mà là `event_type=WATER_LEVEL_DETECTION` trong CHUNG
  bảng `anomaly.anomaly_event` với ẩu đả/đám đông/leo trèo — quyết định
  thiết kế "1 tool `count_anomaly_events` dùng chung, `event_type` là
  tham số" trong Phase 7 xuất phát trực tiếp từ phát hiện này (không phải
  chọn tuỳ ý để đơn giản hoá).
- **Không tìm thấy** pipeline/bảng "mực nước" độc lập nào trong repo — ban
  đầu nghi ngờ đây là domain thiếu data, nhưng tra thêm `vms-analytics.md`
  mới xác nhận nó nằm trong `anomaly_event` (không phải domain rời).

### Review vs yêu cầu user
- **Pass:** đủ 6 file được yêu cầu (`README.md`, `AGENTS.md`,
  `specs/product-spec.md`, `specs/implementation-plan.md`,
  `specs/test-plan.md`, `specs/change-log.md`).
- **Quyết định phạm vi (không phải bug):** yêu cầu gốc có nhắc trực tiếp
  "update `eval/datasets/agent_stat` cho tôi" — NHƯNG dòng cuối yêu cầu ghi
  rõ "Do not implement the app yet" và "Before writing any code, create or
  update these files: [6 file trên]". Hiểu đây là 2 chỉ dẫn ở 2 tầng khác
  nhau: tầng "mô tả app idea" (4 gạch đầu dòng, có nhắc golden dataset/
  Langfuse/Prompt Registry) là NGỮ CẢNH cho việc viết spec, còn tầng "việc
  cần làm ngay" chỉ giới hạn ở 6 file docs. Vì vậy: viết CHI TIẾT kế hoạch
  golden dataset v2 (bảng phân bổ 30 case/8 domain) trong
  `implementation-plan.md`, nhưng CHƯA tạo file
  `eval/datasets/agent_stat/v2.yaml` thật — đúng theo nghĩa đen của "Do not
  implement the app yet". Nếu hiểu sai ý định này, việc tạo file YAML thật
  ở Phase 7 chỉ mất thêm 1 bước nhỏ vì đã có sẵn bảng phân bổ + quy ước.
- **Không đổi code:** không file nào trong `src/`, `eval/datasets/`,
  `tests/`, `.env.example`, `requirements.txt` bị sửa ở lượt này — đúng
  yêu cầu "Do not implement the app yet".

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
