# ORCA-AGENT-SETUP — một file cho agent tự setup máy

**Đối tượng:** Agent (Orca / Cursor / Claude / Antigravity) trên máy **bất kỳ**.  
**Nhiệm vụ:** Đọc file này → kiểm tra máy → tạo playbook + cài symlink nếu thiếu → sẵn sàng chạy 5 vai.

Không cần zip script sẵn. **File này là nguồn sự thật.** Khi xong, tạo marker `.orca-playbook-installed` trong thư mục chứa file này.

---

## 0. Nguyên tắc cứng

1. Chỉ làm **một** việc setup / **một** role tại một thời điểm; sau mỗi bước in lệnh đã chạy + kết quả.
2. **Thích ứng máy:** phát hiện OS, `$HOME`, binary Orca, PATH — không hard-code path user trừ khi path đó tồn tại trên máy.
3. Token fallback **luôn**: `claude → cursor → antigravity` khi hết token.
4. Claude: sau mỗi task Claude → stop + logout; task Claude kế → login lại rồi mới launch.
5. Logout khi **tắt app Orca** (không mỗi tab agent), trừ lifecycle Claude theo task ở trên.
6. Logout **không** reset quota Anthropic.
7. Không commit credentials / `.credentials.json` vào git.
8. **Session Cursor (tuỳ chọn):** ưu tiên reuse pane/session đang mở khi tiện; **không bắt buộc** cấm spawn worker/tab mới — spawn khi role cần (Test writer / Reviewer-5a) hoặc user yêu cầu.
9. **SDD theo guide tiếng Việt:** đọc + làm theo `Spec Driven Development Guide - Vietnamese.md` (cạnh repo / copy theo máy). Spec sống **chỉ** 4 file trong `specs/`; **một phase/task một lần**; sau mỗi lần triển khai → tick plan + `specs/change-log.md` + cách test.
10. **Cổng review mỗi feature (§6c):** Implement → Review vs acceptance → Fix-only nếu Blocked → `Approved` rồi mới task kế. Cấm nhảy task khi chưa Approved.
11. Playbook này là **template mọi project** trên máy (không chỉ FGS); FGS chỉ là repo mang file đi.
12. **Coordinator (ô Spec/Cursor) chỉ điều phối:** phân loại câu hỏi → dispatch đúng role (§15b). Không tự đọc docs/repo để tổng kết thay Explorer; không code thay Implementer; không viết spec thay Planner — trừ khi việc đó là meta-setup khung Orca hoặc không thuộc role nào. **Không** bỏ qua cổng §6c.
13. **Mọi agent phải báo về Coordinator khi xong** (§15c): ghi `specs/agent-reports/*` + `worker_done` (khi có dispatch). Chỉ in trong pane = **chưa xong**. Coordinator bắt buộc đọc report rồi mới đưa hướng đi tiếp.
14. **Auto-wake Coordinator (§15e) — bắt buộc:** pane Cursor thường **không** nhận `worker_done` thành turn mới. Sau mỗi `worker-start`, Coordinator **phải** chạy `orca-coord-watch --run <runId> --terminal <coordTerm> --workdir <project>`. Không chờ user nhắc / paste ảnh.
15. **Verify sau task lớn** (§18): tool check trước; AI không thay lint/typecheck/unit; review đối kháng + bằng chứng; eval metric khi có ground truth.
16. **Tên tab/session Orca bắt buộc** theo bảng §15d (vd. `03 Planner (Claude)`). Mỗi lần `agent launch` / tạo pane / rename: đặt đúng title đó — không để tên mặc định agent.

---

## 1. Probe máy (chạy trước)

Agent chạy và ghi lại:

```bash
uname -s
echo "HOME=$HOME"
command -v orca || true
command -v orca-ide || true
ls "$HOME/.orca/cli/bin/orca" 2>/dev/null || true
echo "ORCA_CLI_COMMAND=${ORCA_CLI_COMMAND:-}"
test -d "$HOME/.local/bin" && echo HAS_LOCAL_BIN=1
```

**Chọn `ORCA` binary theo thứ tự:**

1. `$ORCA_CLI_COMMAND` nếu set và executable  
2. `$HOME/.orca/cli/bin/orca`  
3. `orca-ide` trên PATH  
4. `orca` trên PATH (cẩn thận Linux: tránh nhầm GNOME screen reader — ưu tiên `orca-ide` / path `.orca/cli`)

Nếu **không có Orca CLI** → dừng setup playbook orchestration; vẫn ghi `AGENTS.md` rules vào báo cáo và bảo user cài Orca trước.

**Thư mục playbook đích:**

```text
$ORCA_PLAYBOOK_HOME  nếu set
ngược lại:  $HOME/orca/playbooks
```

Gọi đó là `PLAYBOOK`.

---

## 2. Tạo cây playbook (nếu chưa đủ)

Tạo:

```text
$PLAYBOOK/
  multi-agent-role-setup.md   # có thể copy nội dung tóm tắt từ §8–§11
  roles/01-explorer.md … 05-reviewer.md
  roles/_REPORT_BACK.md       # bắt buộc ghép vào mọi worker spec (§15c)
  roles/_VERIFY.md            # §18 — ghép vào roles 3/4/5a/5b
  bin/agent-fallback
  bin/claude-session
  bin/orca-quit-logout
  bin/orca-open
  bin/orca-roles-run
  bin/orca-claude-after-task
  bin/orca-coord-watch          # §15e — auto-wake Coordinator (bắt buộc)
  bin/orca-coord-drain          # §15e — drain inbox + reports khi turn bắt đầu
  desktop/orca-with-logout.desktop
  logs/
```

Materialize từng file từ **§12 Script bodies** bên dưới (write đúng nội dung, `chmod +x` mọi file trong `bin/`).

Idempotent: nếu file đã có và marker mới hơn 1 ngày, hỏi user trước khi ghi đè — mặc định **cập nhật** từ file này khi user/agent đang chạy setup lại.

---

## 3. Cài symlink + desktop (theo máy)

```bash
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
ln -sfn "$PLAYBOOK/bin/orca-open"              "$HOME/.local/bin/orca-open"
ln -sfn "$PLAYBOOK/bin/claude-session"         "$HOME/.local/bin/claude-session"
ln -sfn "$PLAYBOOK/bin/agent-fallback"         "$HOME/.local/bin/agent-fallback"
ln -sfn "$PLAYBOOK/bin/orca-roles-run"         "$HOME/.local/bin/orca-roles-run"
ln -sfn "$PLAYBOOK/bin/orca-quit-logout"       "$HOME/.local/bin/orca-quit-logout"
ln -sfn "$PLAYBOOK/bin/orca-claude-after-task" "$HOME/.local/bin/orca-claude-after-task"
ln -sfn "$PLAYBOOK/bin/orca-coord-watch"       "$HOME/.local/bin/orca-coord-watch"
ln -sfn "$PLAYBOOK/bin/orca-coord-drain"       "$HOME/.local/bin/orca-coord-drain"
cp "$PLAYBOOK/desktop/orca-with-logout.desktop" "$HOME/.local/share/applications/"
# Sửa Exec= trong .desktop thành đường dẫn tuyệt đối $PLAYBOOK/bin/orca-open trên máy này
```

**PATH:** nếu `$HOME/.local/bin` chưa có trong PATH của shell user, append vào `~/.bashrc` hoặc `~/.zshrc` (detect `$SHELL`) **một lần** (không trùng dòng).

**Linux:** `update-desktop-database ~/.local/share/applications` nếu lệnh tồn tại.  
**macOS:** bỏ qua update-desktop-database; user mở `orca-open` từ terminal.

---

## 4. Smoke trên máy này

```bash
"$PLAYBOOK/bin/agent-fallback" status
"$PLAYBOOK/bin/claude-session" status
"$PLAYBOOK/bin/orca-roles-run" --brief "smoke" --dry-run --workdir "$(pwd)"
```

Ghi kết quả vào báo cáo. Không `account rm` / archive credentials trong smoke trừ khi user yêu cầu.

---

## 5. Marker hoàn tất

Trong thư mục chứa file setup này (thường `videosynopsis-fgs/`):

```bash
printf 'installed=%s\nplaybook=%s\norca=%s\n' "$(date -Iseconds)" "$PLAYBOOK" "$ORCA" > .orca-playbook-installed
```

---

## 6. Kiến trúc vận hành (DAG bắt buộc)

Đây là **quy trình hoạt động** của agent — khớp bảng phân vai + vòng Claude logout.

```text
New feature request
        │
        ▼
1 Explorer (Antigravity, nặng)
        │
        ▼
  REPO_DIGEST.md
        │
        ▼
2 Planner (Claude plan-mode, nhẹ) ──after Claude task──► Stop Claude + logout
        │                                                      │
        ▼                                                      │ next Claude task
  specs/ (4 file: product + plan + test-plan + change-log)
  + review MVP spec (Planner pass 2 / user) trước khi code
        │                                         Login Claude + launch
        │
        └────────── per unchecked task (lặp đến hết plan) ──────────┐
                    │                                                 │
        ┌───────────┴───────────┐                                     │
        ▼                       ▼                                     │
3 Implementer            4 Test writer                                │
  (một task [ ] thôi)     (acceptance của task đó)                    │
        │                       │                                     │
        └──────────┬────────────┘                                     │
                   ▼                                                  │
            5a Reviewer Cursor                                        │
               vs product-spec + test-plan                            │
                   │                                                  │
            Approved?──no──► Fix-only (3/4) ──► 5a lại                │
                   │ yes                                              │
                   ▼                                                  │
            5b Reviewer Claude (khi cần)                              │
               ──after Claude──► Stop + logout                        │
                   │                                                  │
            Approved?──no──► Fix-only ──► 5a/5b lại                   │
                   │ yes                                              │
                   ▼                                                  │
            Task đóng → task [ ] tiếp theo ───────────────────────────┘
                   │
                   ▼
                 Done (hết plan / MVP)
```

**Thứ tự cứng**

1. Không Planner trước khi có `REPO_DIGEST.md`.
2. Không Implementer / Test writer trước khi có **SPEC_PLAN** = `specs/product-spec.md` + `specs/implementation-plan.md` (alias cũ `SPEC.md`+`PLAN.md` vẫn chấp nhận) **và** spec đã qua bước review MVP (guide VN bước 2).
3. Implementer/Test chỉ làm **một** unchecked task trong `implementation-plan.md` mỗi vòng (guide VN).
4. **3 ∥ 4** chạy song song trên **cùng một** task (independent).
5. **5a** sau khi cả 3 và 4 xong (hoặc đủ artifact để review).
6. **5b** sau 5a khi cần; Claude chỉ đọc filtered diff + logic nhạy cảm.
7. **Cổng review (bắt buộc):** không dispatch task `[ ]` kế cho đến khi 5a (và 5b nếu đã mở) trả `Approved`. `Blocked` → Fix-only cùng task → review lại (guide VN bước 6→7→8).
8. Mỗi lần xong task Claude (2 hoặc 5b): **Stop Claude + logout**; lần Claude sau: **Login + launch**.

Chạy DAG: `orca-roles-run --brief "..."` (sau setup).  
Hoặc orchestration thủ công đúng agent đã `agent-fallback resolve`.

---

## 6c. Vòng lặp SDD mỗi feature (ép agent — guide VN)

Nguồn: `Spec Driven Development Guide - Vietnamese.md` trong gói này (và bản handbook trong repo nếu có).

**Spec sống chỉ ở 4 file:** `product-spec.md`, `implementation-plan.md`, `test-plan.md`, `change-log.md`. Không đẻ `docs/superpowers/plans/…` hay SPEC phụ trừ khi user Explicit.

| Bước | Ai | Việc |
|------|-----|------|
| Plan + review MVP | Planner (+ user/Coordinator xác nhận) | Viết/chỉnh 4 file; làm rõ acceptance; **chưa code** |
| Implement 1 task | Implementer | Chỉ 1 `[ ]`; trước code: tóm tắt what/files/how-test; sau: tick + `change-log` + lệnh test |
| Test acceptance | Test writer | Map acceptance → test; song song Implementer trên cùng task |
| Review | Reviewer 5a → (tuỳ) 5b | So `product-spec` + `test-plan`: pass / fail / missing; `Approved` \| `Blocked` + bằng chứng |
| Fix | Implementer / Test | **Chỉ** lỗi của task hiện tại; cập nhật `change-log`; **không** mở task mới |
| Lặp | Coordinator | Chỉ khi `Approved` → dispatch unchecked task tiếp theo |
| Gap tracker | Implementer / Reviewer | Khi `Approved` hạng mục gắn G\*: cập nhật hàng tương ứng trong `specs/gap-analysis-quy-trinh-product-agent.md` (§0 Protocol) |

Coordinator **cấm** bỏ qua cổng review. Worker **cấm** tự nhảy sang task kế trong cùng một turn sau khi implement. Coordinator kiểm tra gap tracker đã khớp trước khi mở task kế liên quan G\*.

---

## 6b. Phân vai chi tiết (bảng chuẩn)

| # | Session | AI | Mức token | Việc làm |
|---|---------|-----|-----------|----------|
| 1 | Explorer | **Antigravity** (context lớn / Gemini Flash High) | **Nặng** | Đọc cả repo; tạo `REPO_DIGEST.md`: cấu trúc, module chính, conventions, chỗ cần sửa / rủi ro, cách chạy-test. **Không sửa production code.** |
| 2 | Planner | **Claude Code (plan-mode)** → fallback cursor→antigravity | **Nhẹ** | Chỉ đọc `REPO_DIGEST.md` + vài file then chốt; viết/cập nhật **4 file** `specs/` theo guide VN (§14b). Pass review MVP (rõ, đơn giản) trước khi code. **Không implement.** Xong → logout Claude. |
| 3 | Implementer (1–2 session) | **Antigravity** trên **worktree riêng** (`new-child`) | **Nặng nhất** | **Một** task `[ ]` mỗi vòng; test/lint xanh; sau đó **dừng** chờ review — không tự mở task kế. Fix-only khi Reviewer `Blocked`. |
| 4 | Test writer | **Cursor** → fallback antigravity | **Vừa** | Test từ acceptance của **cùng** task; song song 3 được. Không nhảy task khi chưa Approved. |
| 5a | Reviewer round 1 | **Cursor** → fallback antigravity | **Vừa** | So product-spec + test-plan: pass/fail/missing; `Approved`\|`Blocked`. Gate sang task kế (§6c). |
| 5b | Reviewer round 2 | **Claude Code** → fallback | **Nhẹ** | Filtered diff + logic nhạy cảm. Xong → logout Claude. Cũng là cổng `Approved`\|`Blocked`. |

**Output bắt buộc theo bước:** `REPO_DIGEST.md` → `specs/` (4 file) → (lặp) code/tests một task → review Approved → task kế → Done.  
*(Alias cũ `SPEC.md`/`PLAN.md` = nội dung tương đương `specs/product-spec.md` + `specs/implementation-plan.md` — ưu tiên layout guide VN.)*

---

## 7. Token fallback

Chuỗi cố định: **claude → cursor → antigravity**.

- Ngưỡng: `AGENT_FALLBACK_THRESHOLD` (mặc định **95** = `usedPercent` session/weekly).
- Cursor ít khi có % → khi UI báo hết: `agent-fallback mark-exhausted cursor`
- Xem: `agent-fallback status` / `resolve <preferred>`

---

## 8. Claude lifecycle (nhánh bên phải sơ đồ §6)

Gắn đúng 2 điểm trên DAG:

| Thời điểm | Hành động |
|-----------|-----------|
| Trước **2 Planner** hoặc **5b** (khi resolved agent vẫn là `claude`) | `claude-session start` (= Login Claude + launch) |
| Sau **2** hoặc **5b** `worker_done` | `orca-claude-after-task --run <runId>` (= Stop Claude + logout) |

```text
claude-session start
# ... worker_done ...
orca-claude-after-task --run <runId>
# = claude-session stop --yes --run <runId> --archive-system
```

- Managed account ưu tiên (`orca account add --agent claude`).
- Nếu chỉ có system `~/.claude/.credentials.json`: `stop` **archive** file đó; `start` restore archive hoặc login lại.
- `orca account rm` **không** xóa system credentials — vì vậy cần archive.
- Nếu Planner/5b đã fallback sang cursor/antigravity → **không** gọi Claude login/logout cho hop đó.

---

## 9. Logout khi tắt Orca

User mở app qua:

```bash
orca-open
```

Khi runtime/app dừng → `orca-quit-logout` → clear Claude (primary).  
`--all-logout` chỉ ghi chú Antigravity/Cursor (best-effort).

---

## 10. Lệnh hàng ngày (sau setup)

```bash
orca-open
agent-fallback status
cd <project>
orca-roles-run --brief "mô tả việc"
# sau Planner / Reviewer-Claude:
orca-claude-after-task --run "$(jq -r .runId .orca-roles-run-state.json)"
```

---

## 11. Troubleshooting ngắn

| Hiện tượng | Cách xử lý |
|------------|------------|
| Không tìm thấy `orca` | Cài Orca; dùng `orca-ide` hoặc `$HOME/.orca/cli/bin/orca` |
| Claude vẫn chạy sau stop | Kiểm tra còn `~/.claude/.credentials.json` không; `stop --archive-system` |
| Quota vẫn đầy sau logout | Đúng — logout không reset quota |
| Fallback không nhảy | `mark-exhausted <agent>`; hạ `AGENT_FALLBACK_THRESHOLD` để test |
| Desktop Exec sai path | Sửa `.desktop` → `$PLAYBOOK/bin/orca-open` tuyệt đối |

---

## 12. Script bodies — agent WRITE các file này vào `$PLAYBOOK`

Khi materialize: thay shebang giữ `#!/usr/bin/env bash`. Trong script, `PLAYBOOK_ROOT` = `dirname("$0")/..` đã đủ (không hard-code user).

### 12.1 `bin/agent-fallback`

Agent: nếu file chưa có trên máy lab đã cài, **copy từ**  
`$HOME/orca/playbooks/bin/agent-fallback`  
nếu tồn tại; **không thì** clone logic:

- Chain: `claude`, `cursor`, `antigravity`
- `resolve preferred`: bỏ qua agent exhausted
- Exhausted khi: mark file `$PLAYBOOK/logs/exhausted-agents.txt`, hoặc `usedPercent >= THRESHOLD` từ `orca account list --json` → `rateLimits.<provider>`, hoặc error/status khớp `rate limit|quota|exhaust|429`
- Lệnh: `resolve|check|status|mark-exhausted|clear-exhausted`
- **Quan trọng:** đọc JSON account list qua file tạm — **không** pipe JSON vào python đang dùng heredoc stdin

(Tham chiếu triển khai đầy đủ đã có trên máy nguồn: `/home/atin/orca/playbooks/bin/agent-fallback` — nếu agent đang ở máy đó, `cp` file này sang `$PLAYBOOK/bin/`.)

### 12.2 Các bin còn lại

Ưu tiên **copy nguyên file** từ một trong các nguồn (theo thứ tự):

1. Cùng repo: `orca_setup/roles/*.md` (gói MD này) + `orca-playbook/bin/*` (script, cạnh `orca_setup/`)  
2. `$HOME/orca/playbooks/bin/*`  
3. Máy nguồn lab: `/home/atin/orca/playbooks/bin/*` nếu path tồn tại  

Files cần có:

- `claude-session` — start/stop/status; stop archive system creds khi cần  
- `orca-quit-logout` — gọi `claude-session stop --yes --archive-system`  
- `orca-open` — `orca open` rồi poll `orca status` until not running → quit-logout  
- `orca-roles-run` — DAG 5 vai; mỗi role `agent-fallback resolve`; Claude start chỉ khi resolved=`claude`  
- `orca-claude-after-task` — wrapper stop  
- `orca-coord-watch` — §15e auto-wake Coordinator (copy từ `orca_setup/bin/`)  
- `orca-coord-drain` — §15e drain inbox/reports đầu turn  

Roles markdown: copy từ **`orca_setup/roles/`** (`01`…`05`, `_REPORT_BACK`, `_VERIFY`) vào `$PLAYBOOK/roles/`.  
Bin wake: copy từ **`orca_setup/bin/`** (`orca-coord-watch`, `orca-coord-drain`) nếu chưa có trong `$PLAYBOOK/bin/`.

Desktop file:

```ini
[Desktop Entry]
Type=Application
Name=Orca (playbook quit-logout)
Comment=Launch Orca; on exit run Claude logout playbook
Exec=___ABS_PATH_TO_PLAYBOOK___/bin/orca-open
Terminal=false
Categories=Development;
```

### 12.3 Nếu không copy được (máy trống)

Agent phải **tái tạo** các script theo hành vi §7–§10 (không được bỏ fallback / Claude lifecycle). Có thể đọc bản đầy đủ trong git history hoặc yêu cầu user copy một lần từ máy lab.

---

## 13. Checklist agent (tick khi làm)

- [ ] Probe máy (§1) — ghi ORCA, HOME, OS  
- [ ] Tạo/cập nhật `$PLAYBOOK` (§2)  
- [ ] Symlink + desktop + PATH (§3) — gồm `orca-coord-watch` / `orca-coord-drain`  
- [ ] Smoke (§4)  
- [ ] Marker `.orca-playbook-installed` (§5)  
- [ ] Báo user: dùng `orca-open`, `orca-roles-run`, fallback chain, **§15e auto-wake**  

---

## 14. Phạm vi repo VideoSynopsis-FGS (lab đã chốt trong hội thoại)

Khi làm việc **trong / cạnh** repo này (hoặc parent `video-synopsis/build`), tôn trọng quyết định thí nghiệm:

| Quyết định | Chi tiết |
|------------|----------|
| Quan hệ FGS | **Bọc** baseline (không rewrite thuật toán tube/synopsis/background) |
| MVP | E2E + metrics + seam `run_synopsis` + unit test wrapper |
| Runtime | Library API + CLI mỏng (`python -m video_synopsis` nếu có package parent) |
| Detect/track | YOLO + SFSORT **cứng** (chưa port giả) |
| Success | Có `Synopsis.mp4` + metrics: `wall_s`, `peak_ram_mb` (RSS), `frames_in/out`, `compression_ratio` |
| Môi trường lab | GPU `0` + fixture `Test.mp4` / `best.pt` khi có |
| Seam | Vendor FGS + **in-process** `run_fgs` / `run_fgs_from_args` (import **không** chạy video) |
| TDD | Unit wrapper không GPU; E2E `pytest -m e2e` khi có GPU/fixture |
| Spec-driven | **Bắt buộc theo guide VN** — xem §14b |

Code FGS: `main.py`, `tube.py`, `synopsis.py`, `background.py`, `SFSORT.py`, `best.pt`, `Test.mp4`.

---

## 14b. Spec-Driven Development (nguồn chuẩn)

**Nguồn sự thật SDD:**  
`orca_setup/Spec Driven Development Guide - Vietnamese.md` (trong gói này).  
Trên máy khác: giữ file trong `orca_setup/` hoặc copy ra cạnh `specs/`.

**Nguyên tắc lấy từ guide (rút gọn, không thay thế việc đọc guide):**

1. Viết ý tưởng → chuyển thành spec **trước** khi code; review MVP spec trước khi implement.
2. **Không** nhờ agent build cả feature/app một lần — đọc `specs/` rồi triển khai **một** phase/task unchecked.
3. Sau mỗi lần triển khai: tick checklist, cập nhật `specs/change-log.md`, nêu lệnh test.
4. **Review lặp** so acceptance (pass/fail/missing) → Fix-only nếu cần → `Approved` rồi mới task kế (§6c).
5. Không đổi kiến trúc / thêm lib trừ khi đã sửa spec trước.
6. Chỉ 4 file trong `specs/` — không đẻ plan/spec phụ trừ khi user Explicit.

**Cây `specs/` chuẩn (guide VN):**

```text
specs/
  product-spec.md          # goal, users, in/out scope, acceptance
  implementation-plan.md   # phase nhỏ + checklist
  test-plan.md             # cách test (khuyến nghị)
  change-log.md            # ghi sau mỗi lần triển khai
```

Kèm `AGENTS.md` ở root project (rule hành vi agent — luôn đọc specs trước khi code).

**Map sang DAG Orca:** Planner tạo/chỉnh `specs/*` (không chỉ SPEC.md/PLAN.md lẻ). Implementer/Test writer chỉ làm task unchecked tiếp theo trong `implementation-plan.md`. Reviewer so với `product-spec.md` (+ filtered diff ở 5b).

**Lab hiện có:** parent `video-synopsis/build/specs/` đã theo layout này — dùng path đó khi workdir là build/FGS.

---

## 15. Điều phối session (Orca UI)

| Vai | Agent preferred | Ghi chú điều phối |
|-----|-----------------|-------------------|
| Coordinator / Spec | Cursor | **Chỉ điều phối** — xem §15b; sync `specs/` khi cần sau khi role báo xong |
| Explorer | Antigravity | Đọc repo/docs/specs → digest / tổng kết trạng thái / tìm artifact |
| Planner / Reviewer-5b | Claude | Login→làm→logout |
| Implementer | Antigravity | Code theo plan; worktree `new-child` khi nặng |
| Test writer / Reviewer-5a | Cursor | Reuse pane nếu có; spawn session mới **được phép** khi cần |

Ưu tiên inject/dispatch vào pane đang mở khi đủ; spawn worker mới không bị cấm nếu role/workload cần.

---

## 15d. Tên tab / session (bắt buộc — khớp khung lab)

Mọi lần mở khung làm việc hoặc spawn role, **đặt title đúng chuỗi** dưới (copy nguyên, kể cả khoảng trắng / dấu ngoặc):

| # | Tab title (exact) | Agent | Role |
|---|-------------------|-------|------|
| 01 | `01 Spec / Coordinator` | Cursor | Điều phối |
| 02 | `02 Explorer (Antigravity)` | Antigravity | Explorer |
| 03 | `03 Planner (Claude)` | Claude | Planner |
| 04 | `04 Implementer (Antigravity)` | Antigravity | Implementer |
| 05 | `05 Test writer (Cursor)` | Cursor | Test writer |
| 06 | `06 Reviewer-5a (Cursor)` | Cursor | Reviewer 5a |
| 07 | `07 Reviewer-5b (Claude)` | Claude | Reviewer 5b (khi cần; có thể chưa mở sẵn) |

**Cách đặt tên (sau launch):**

```bash
orca terminal rename --terminal term_<id> --title "03 Planner (Claude)"
```

Hoặc `--task-title` / title lúc `agent launch` trùng chuỗi trên.  
Layout gợi ý (như lab): trên trái 01 · trên phải 02|04 · dưới trái 03 · dưới phải 05|06.

Coordinator setup khung: tạo/đổi tên đủ 01–06 trước khi giao việc. Không để tab tên mặc định (`Video Synopsis…`, `Claude`, …).

---

## 15b. Luật điều phối (Coordinator = Cursor Spec)

Coordinator **không làm thay** việc thuộc role khác. Mỗi câu hỏi / yêu cầu của user:

1. **Phân loại** → chọn đúng role (§6b + bảng dưới).
2. **Dispatch** vào pane/agent đó (`worker-start --terminal …` hoặc `terminal send` / orchestration `send`).
3. **Chờ** báo cáo → tóm tắt ngắn cho user (không tự đọc lại cả repo để trả lời thay).
4. **Chỉ tự trả lời** khi: meta về khung Orca/playbook/setup máy, hoặc không khớp role nào, hoặc user Explicit yêu cầu Coordinator làm.

| Loại câu hỏi / việc | Giao cho | Không giao Coordinator |
|---------------------|----------|------------------------|
| Đọc docs/`specs/`/repo → tổng kết đã làm gì, acceptance, tìm thành phẩm/artifact ở đâu | **02 Explorer (Antigravity)** | ❌ tự grep/đọc thay |
| Viết/sửa `specs/*`, chốt scope/plan MVP | **03 Planner (Claude)** | ❌ viết spec thay |
| Implement / sửa production code theo plan | **04 Implementer (Antigravity)** | ❌ code thay |
| Viết/sửa tests từ acceptance | **05 Test writer (Cursor)** | ❌ viết test thay |
| So diff vs product-spec, thiếu edge case | **06 Reviewer-5a (Cursor)** | ❌ review thay |
| Review logic nhạy cảm / filtered diff | **07 Reviewer-5b (Claude)** | ❌ review thay |
| Setup playbook, symlink, logout Claude, mở khung pane, fallback token | **Coordinator** (được phép) | — |
| Câu mơ hồ | Hỏi user **một** câu làm rõ **hoặc** chọn role gần nhất + ghi giả định khi dispatch | ❌ ôm hết |

**Ví dụ bắt buộc:**  
User: *“kiểm tra `specs/` đã xong chưa, thành phẩm ở đâu?”*  
→ Coordinator **dispatch Explorer**, không tự đọc `specs/` + `find Synopsis.mp4` rồi trả lời.

**Dispatch skeleton (Explorer) — luôn nhúng REPORT_BACK:**

```bash
orca orchestration worker-start \
  --terminal term_<explorer> \
  --keep-open \
  --task-title "Explorer: status + deliverables" \
  --spec-file /tmp/spec-with-report-back.md
```

Mọi `--spec` / `--spec-file` **phải** ghép nội dung `roles/_REPORT_BACK.md` (hoặc §15c) vào cuối.

---

## 15c. Vòng báo cáo bắt buộc (mọi agent → Coordinator)

**Vấn đề đã gặp:** agent in kết quả trong pane rồi idle; Coordinator không bị đánh thức → user phải tự thấy.

**Luật cứng (áp dụng tất cả role 01–05b):**

| Bước | Ai | Việc |
|------|-----|------|
| A | Worker | Viết `specs/agent-reports/<timestamp>-<role>.md` (summary + artifacts + `next_hint`) |
| B | Worker | Cập nhật `specs/session-handoff.md` → **Hoàn thành gần nhất** |
| C | Worker | `orca orchestration send --type worker_done --outcome succeeded\|failed …` khi có Task/Dispatch |
| D | Coordinator | **Bật `orca-coord-watch` ngay sau `worker-start`** (§15e); khi được inject wake: tóm tắt cho user + chọn bước tiếp |
| E | Coordinator | Không chờ user nhắc. Nếu wake trễ: `orca-coord-drain` + đọc `specs/agent-reports/` + inbox Run |

Template đầy đủ: `$PLAYBOOK/roles/_REPORT_BACK.md` (copy từ `orca_setup/roles/_REPORT_BACK.md`).

**Coordinator checklist sau mỗi dispatch:**

1. Ghi dispatchId / runId vào `specs/session-handoff.md` (Đang chạy).
2. **Ngay sau `worker-start` thành công:** chạy `orca-coord-watch` (§15e) — không bỏ bước này.
3. Kết thúc turn để chờ wake inject; khi wake / `orca-coord-drain` → **ưu tiên** đọc report trước khi làm gì khác.
4. Xóa/đánh dấu xong dòng Đang chạy; điền Hoàn thành gần nhất; `task-update --status completed` khi worker_done succeeded.
5. Đưa hướng đi tiếp (một câu rõ: role nào / việc gì) — trừ khi user chỉ hỏi thông tin và chưa muốn làm tiếp.
6. **Cổng SDD (§6c):** sau Implement/Test → hướng tiếp **bắt buộc** là Reviewer-5a (không phải task kế). Sau `Blocked` → Fix-only cùng task. Sau `Approved` → mới được unchecked task tiếp theo.

**`orca-roles-run`:** mỗi role spec phải kết thúc bằng khối REPORT_BACK (script materialize từ §12 phải `cat` `_REPORT_BACK.md` vào cuối spec).

---

## 15e. Auto-wake Coordinator (Cursor pane — bắt buộc)

**Sự thật vận hành:** `worker_done` luôn vào **mailbox của Run**, nhưng pane Coordinator chạy **Cursor** thường **không** tự mở turn mới. User không được là người “đánh thức” bằng cách paste ảnh.

**Công cụ (trong `orca_setup/bin/` → copy sang `$PLAYBOOK/bin/`):**

| Script | Việc |
|--------|------|
| `orca-coord-watch` | Daemon: peek inbox Run + theo dõi `specs/agent-reports/`; khi có `worker_done`/report mới → `orca terminal send --enter` vào pane Coordinator với prompt bắt buộc đọc + phản hồi |
| `orca-coord-drain` | Helper đầu turn: in run-current, status watch, report mới, inbox — Coordinator chạy khi nhận auto-wake |

**Sau mỗi `worker-start` (template cứng):**

```bash
# worker-start ... --json  → lấy runId từ result
orca-coord-watch \
  --run <runId> \
  --terminal term_<coordinator> \
  --workdir "$(pwd)"
# xác nhận: orca-coord-watch --status
```

- Đổi Run / đổi project → chạy lại `orca-coord-watch` (script thay daemon cũ).
- Dừng: `orca-coord-watch --stop`.
- Khi nhận tin `[ORCA auto-wake]`: chạy `orca-coord-drain --run <runId> --workdir <project>` (hoặc tương đương), đọc report, tóm tắt user, dispatch bước tiếp — **không** hỏi lại “đã xong chưa?”.

**Không** coi “end turn và hy vọng Orca native wake Cursor” là đủ trên máy lab dùng Cursor làm Coordinator.

---

## 17. Sau khi xong trên workspace Orca (đóng việc / merge)

Orca thường code trên **worktree/branch riêng** (vd. `…/orca/workspaces/<project>/build` + branch `Anodis/build`), còn **main** nằm ở checkout gốc (vd. `…/dong/…/video-synopsis`).

### Ai quyết định merge?

**Coordinator / agent không tự merge.** Khi việc xong + test xanh, Coordinator **chỉ báo** và hỏi user chọn **một** trong:

1. **Merge local** vào `main` (hoặc base branch) trên máy  
2. **Push branch + mở MR/PR** (GitLab/GitHub) — giữ worktree để sửa theo review  
3. **Giữ nguyên** branch/worktree — user xử lý sau  
4. **Hủy** (discard) — cần user gõ xác nhận rõ

Chỉ khi user Explicit chọn (vd. *“merge local vào main”*, *“cho phép merge”*, *“mở MR”*) thì Coordinator mới thực hiện đúng lựa chọn đó.  
**Push remote** cũng cần Explicit riêng (merge local ≠ đã push).

### Checklist kỹ thuật (sau khi user đã chọn)

1. **Xanh test** trên worktree: `pytest -m "not e2e"` (và E2E nếu thuộc acceptance).
2. **Commit** mọi thay đổi muốn vào main; file chỉ để xem local (video demo lớn, zip) → `resource/` + gitignore hoặc không commit.
3. Nếu user chọn **merge local** — chạy từ checkout **main**:
   ```bash
   cd <main-checkout>
   git checkout main
   git pull --ff-only   # nếu remote có cập nhật
   git merge <feature-branch>   # vd. Anodis/build
   pytest -m "not e2e"          # xác nhận lại trên main
   ```
   Push chỉ khi user bảo push: `git push origin main`
4. Nếu user chọn **MR/PR**: `git push -u origin <feature-branch>` + tạo MR; **không** xóa worktree.
5. **Đừng xóa Orca worktree** trừ khi user Explicit (`orca worktree rm` / tương đương).
6. **Handoff:** ghi đã merge/MR (sha, lựa chọn user) vào `specs/session-handoff.md`.

**Implementer `new-child`:** merge/cherry-pick child → parent trước; rồi mới áp dụng lựa chọn user (merge parent → main hoặc MR).

---

## 18. Verify sau task lớn

Áp dụng khi xong một phase/feature đáng kể (trước merge/MR hoặc khi user yêu cầu verify).

### 18.1 Review đối kháng (AI / session khác)

- Dùng **session hoặc model khác** Reviewer (ưu tiên 5a Cursor rồi 5b Claude; hoặc pane mới nếu cần ngữ cảnh sạch).
- Nhiệm vụ: **tìm cách bác bỏ** kết quả — không khen chung chung.
- Chỉ báo lỗi ảnh hưởng **correctness / acceptance / regression rủi ro**.
- Bắt buộc kèm **bằng chứng**: lệnh đã chạy + output, test đã chạy, path/dòng code liên quan. User (hoặc Coordinator) kiểm tra bằng chứng, không tin lời suông.

### 18.2 Đo bằng chỉ số trên tập đánh giá (AI/CV/LLM)

- Khi bài toán có thể đo được: dùng **tập đánh giá cố định + ground truth**, tách khỏi data tinh chỉnh prompt / train.
- So các phiên bản trên **cùng một tập** với metric phù hợp (accuracy, recall, mAP, F1, latency, compression_ratio lab, …).
- Lab FGS hiện: E2E + metrics wall/RAM/compression là baseline; **golden video / mAP không bắt buộc** trừ khi `specs/` thêm eval set.

### 18.3 Không dùng AI thay công cụ check truyền thống

- Lint, format, typecheck, unit test, build — **chạy tool** (`pytest`, `ruff`, `mypy`, … tùy repo).
- AI **không** được thay bước đó bằng “đọc code rồi bảo ổn”.
- AI chỉ: điều tra khi tool fail, hoặc review logic/spec sau khi tool đã xanh.

**Thứ tự gợi ý:** tool xanh → (eval metric nếu có) → review đối kháng có bằng chứng → rồi mới hỏi user merge/MR (§17).

**Wire vào playbook (bắt buộc materialize):** copy `orca_setup/roles/_VERIFY.md` + `05-reviewer.md` (và toàn bộ `roles/`) vào `$PLAYBOOK/roles/`; `orca-roles-run` `append_verify` cho roles 3, 4, 5a, 5b.

---

## 16. Ma trận phủ ý tưởng (audit hội thoại)

| Ý tưởng user | Có trong file? | Mục |
|--------------|----------------|-----|
| 5 vai Explorer→Reviewer (bảng phân vai) | Có | §6b |
| DAG + song song Implementer∥Test writer | Có | §6 |
| Review 2 lớp Cursor rồi Claude filtered diff | Có | §6, §6b |
| Claude stop+logout sau task; login lại khi cần | Có | §0.4, §6, §8 |
| Logout khi tắt Orca (không mỗi tab) | Có | §0.5, §9 |
| Logout không reset quota | Có | §0.6, §11 |
| Fallback claude→cursor→antigravity | Có | §0.3, §7 |
| Một file .md để agent tự setup theo máy | Có | toàn file + §1–§5 |
| Playbook dùng lại mọi project | Có | §0.10 |
| Không spawn Cursor mới | **Không bắt buộc** — chỉ ưu tiên reuse | §0.8, §15 |
| SDD theo guide VN (`specs/` + 1 task/lần + change-log) | Có | §0.9, §14b |
| Cổng review mỗi feature (Implement→Review→Fix→Approved→task kế) | Có | §0.10, §6, §6c, §15c |
| Bọc FGS / metrics / GPU fixture / TDD | Có | §14 |
| Coordinator chỉ điều phối; đọc docs/tổng kết → Explorer | Có | §15b |
| Mọi agent báo Coordinator (file inbox + worker_done) | Có | §0.13, §15c |
| Auto-wake Cursor Coordinator (`orca-coord-watch`) | Có | §0.14, §15e |
| Sau xong workspace: test → commit → merge main → (push) → không tự xóa Orca WT | Có | §17 |
| Verify: review đối kháng + bằng chứng; eval metric; không AI thay lint/test | Có | §18 |
| Tên tab `01 Spec / Coordinator` … `06 Reviewer-5a (Cursor)` | Có | §0.16, §15d |
| Interactive login Claude khi start | Có | §8 |
| Materialize scripts + symlink trên máy mới | Có | §2–§3, §12 |

---

*Hết file. Agent chỉ cần file này (+ repo FGS) để setup máy mới và vận hành đúng kiến trúc đã chốt.*
