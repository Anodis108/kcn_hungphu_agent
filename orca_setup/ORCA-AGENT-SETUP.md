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
8. **Session Cursor (tuỳ chọn):** ưu tiên reuse pane khi tiện; spawn khi role cần (Test writer / Reviewer-5a). **Pre-gather (§0.8 / `_PRE_GATHER.md`):** phase lớn / diff·log·ảnh nặng → **Antigravity** (factual only: filtered diff, sanitized test/smoke, regex checklist) → `*-pre-gather.md` → **5a Cursor** verdict. Fix-only nhỏ → bỏ qua AG. AG **không** `Approved`|`Blocked`.
9. **SDD theo guide tiếng Việt:** đọc + làm theo `Spec Driven Development Guide - Vietnamese.md` (cạnh repo / copy theo máy). Spec lõi **4 file** trong `specs/` (+ living: `task-delta`, gap, handoff, agent-reports); **một phase/task một lần**; sau mỗi lần triển khai → tick plan + `specs/change-log.md` + **`specs/task-delta.md`** (**Task** = làm gì/mục đích + đổi gì + link `#L…` **chỉ** chỗ sửa; click **phải** nhảy đúng dòng đã đổi — cấm lazy `#L1` trên file đã edit; **không** dán before/after; cấm chỉ ghi số phase) + cách test; đổi quy ước playbook → sync `orca_setup/`.
10. **Cổng review mỗi feature (§6c):** Implement → Review vs acceptance → Fix-only nếu Blocked → `Approved` rồi mới task kế. Cấm nhảy task khi chưa Approved.
11. Playbook này là **template mọi project** trên máy (không chỉ FGS); FGS chỉ là repo mang file đi.
12. **Coordinator (ô Spec/Cursor) chỉ điều phối:** phân loại câu hỏi → dispatch đúng role (§15b). **Ưu tiên agent trong quy ước:** task mà role canonical làm được → dùng đúng agent đó (Implementer=Antigravity, 5a=Cursor, Planner/5b=Claude, …); không thay vì “thông minh hơn” trừ user Explicit hoặc agent quy ước không launch được. Không tự đọc docs/repo để tổng kết thay Explorer; không code thay Implementer; không viết spec/plan thay Planner (kể cả sau khi user *Approve* design trong grill) — trừ meta-setup khung Orca hoặc user Explicit bảo Coordinator làm. **Hotfix / ops / “sửa nhanh trong chat” cũng vậy:** Coord **cấm** tự patch code; phải `worker-start` **Implementer** → **Reviewer** (§6c) đủ vòng (Fix-only nếu Blocked) rồi mới coi xong — trừ user Explicit *Coord tự làm*. **Không** bỏ qua cổng §6c.
13. **Mọi agent phải báo về Coordinator khi xong** (§15c): ghi `specs/agent-reports/*` + `worker_done` (khi có dispatch). Chỉ in trong pane = **chưa xong**. Coordinator bắt buộc đọc report rồi mới đưa hướng đi tiếp.
14. **Auto-wake Coordinator (§15e) — bắt buộc:** pane Cursor thường **không** nhận `worker_done` thành turn mới. Sau mỗi `worker-start`, Coordinator **phải** chạy `orca-coord-watch --run <runId> --terminal <coordTerm> --workdir <project>`. Không chờ user nhắc / paste ảnh.
15. **Vòng điều phối đến hết nhiệm vụ (§15f) — bắt buộc:** khi nhận wake/report → tóm tắt user → **ngay** dispatch bước tiếp (đúng role) → lặp cho đến khi hết checklist wave / user Explicit dừng. Cấm dừng giữa chừng chỉ vì “đã báo một lần”.
16. **Lane song song có điều kiện (§15g):** được nhân bản Implementer (04a/04b…) **chỉ khi** plan có `parallel_ok` + `touches` không giao; mỗi lane vẫn đủ cổng §6c. Fail-closed nếu overlap. Shared specs = một writer sau Approved.
17. **Verify sau task lớn** (§18): tool check trước; AI không thay lint/typecheck/unit; review đối kháng + bằng chứng; eval metric khi có ground truth.
18. **Tên tab/session Orca bắt buộc** theo bảng §15d (vd. `03 Planner (Claude)`). Mỗi lần `agent launch` / tạo pane / rename: đặt đúng title đó — không để tên mặc định agent. Nhân bản Implementer: `04a Implementer (Antigravity)`, `04b Implementer (Antigravity)`.
19. **Skill theo role (§15g Skill matrix):** Coord Cursor = `using-superpowers` + orchestration; Planner Claude = **`grill-me`** rồi plan; Implementer AG = **`ponytail`**; Reviewer = verify (+ `ponytail-review` nếu AG). Skill không tự cross-runtime — ghi trong `roles/*.md` + brief.
20. **`turn_start_unobserved` / stall:** không để lane đứng im. Sau ~1–2 phút vẫn `start_unknown`/idle → abandon + retry canonical khác hoặc Cursor overflow; sau re-auth AG → probe rồi **giao việc ngay**.

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
| **Tự review plan** | Planner | Guide VN bước 3 — tiêu chí chất lượng (§6d); **không** cố định số đầu mục; report `plan_self_review: pass` trước khi Implement |
| Implement 1 task | Implementer | Chỉ 1 `[ ]`; trước code: tóm tắt what/files/how-test; sau: tick + `change-log` + **`task-delta`** (Task = làm gì + links `#L…`; không paste diff) + lệnh test |
| Test acceptance | Test writer | Map acceptance → test; song song Implementer trên cùng task |
| Review | Reviewer 5a → (tuỳ) 5b | So `product-spec` + `test-plan`: pass / fail / missing; `Approved` \| `Blocked` + bằng chứng |
| Fix | Implementer / Test | **Chỉ** lỗi của task hiện tại; cập nhật `change-log`; **không** mở task mới |
| Lặp | Coordinator | Chỉ khi `Approved` → dispatch unchecked task tiếp theo |
| Gap tracker | Implementer / Reviewer | Khi `Approved` hạng mục gắn G\*: cập nhật hàng tương ứng trong `specs/gap-analysis-quy-trinh-product-agent.md` (§0 Protocol) |

Coordinator **cấm** bỏ qua cổng review. Worker **cấm** tự nhảy sang task kế trong cùng một turn sau khi implement. Coordinator kiểm tra gap tracker đã khớp trước khi mở task kế liên quan G\*.

**Cổng plan:** Coordinator **cấm** `worker-start` Implementer cho wave mới nếu Planner report thiếu `plan_self_review: pass` (trừ user Explicit *bỏ qua self-review plan*).

---

## 6d. Tự review Implementation Plan (bắt buộc — số mục không cố định)

Nguồn: guide VN **Bước 3** (đã sửa: ví dụ 7 phase chỉ là greenfield mẫu).

| | |
|--|--|
| **Khi nào** | Mỗi lần Planner viết/đổi `specs/implementation-plan.md` cho một wave / tính năng |
| **Ai** | Planner (rồi user có thể Approve); không phải Implementer tự “review plan bằng cách code” |
| **Số phase / `[ ]`** | Do **scope lần đó** — không ép N mục, không copy list Project setup→ngrok |

**Tiêu chí pass (sửa plan đến khi đạt):**

1. Chỉ việc in-scope; out-of-scope / Non-goals không thành `[ ]`.
2. Mỗi `[ ]` một slice kiểm chứng được.
3. Có acceptance hoặc cách test.
4. Có files/touches; song song thì đủ §15g metadata.
5. `depends` / thứ tự rõ.
6. Không đổi kiến trúc lén.
7. MVP — cắt nice-to-have khỏi wave hiện tại.

Report Planner: `plan_self_review: pass` (+ bullet nếu đã rewrite). Chi tiết: `roles/02-planner.md`.

---

## 6b. Phân vai chi tiết (bảng chuẩn)

| # | Session | AI | Mức token | Việc làm |
|---|---------|-----|-----------|----------|
| 1 | Explorer | **Antigravity** (context lớn / Gemini Flash High) | **Nặng** | Đọc cả repo; tạo `REPO_DIGEST.md`: cấu trúc, module chính, conventions, chỗ cần sửa / rủi ro, cách chạy-test. **Không sửa production code.** |
| 2 | Planner | **Claude Code (plan-mode)** → fallback cursor→antigravity | **Nhẹ** | Đọc digest + then-chốt; cập nhật **4 file** `specs/`; review MVP spec + **tự review plan §6d** (`plan_self_review: pass`). Số phase theo scope — không cố định. **Không implement.** Xong → logout Claude. |
| 3 | Implementer (1–2 session) | **Antigravity** trên **worktree riêng** (`new-child`) | **Nặng nhất** | **Một** task `[ ]` mỗi vòng; test/lint xanh; sau đó **dừng** chờ review — không tự mở task kế. Fix-only khi Reviewer `Blocked`. |
| 4 | Test writer | **Cursor** → fallback antigravity | **Vừa** | Test từ acceptance của **cùng** task; song song 3 được. Không nhảy task khi chưa Approved. |
| 5a | Reviewer round 1 | **Cursor** → fallback antigravity | **Vừa** | So product-spec + test-plan (+ digest pre-gather nếu có); `Approved`\|`Blocked`. Gate §6c. |
| 5a′ | Pre-gather (trước 5a) | **Antigravity** | **Vừa** | Chỉ factual (`_PRE_GATHER.md`); phase lớn bắt buộc cân nhắc; Fix-only nhỏ skip. |
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
3. Sau mỗi lần triển khai: tick checklist, cập nhật `specs/change-log.md` + prepend `specs/task-delta.md` (**Task** = làm gì/mục đích + đổi gì + links `#L…` nhảy đúng dòng đã sửa — cấm lazy `#L1`; không paste before/after); nếu đổi quy ước → sync `orca_setup/`; nêu lệnh test.
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
  task-delta.md            # living: Task=làm gì + đổi gì + links #L… (chỉ chỗ lệch vs main; không paste diff)
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
| Test writer / Reviewer-5a | Cursor | Reuse pane nếu có; spawn khi cần |
| Pre-gather (diff lọc / log sạch / checklist máy / ảnh) | **Antigravity** → `*-pre-gather.md` | Trước 5a Cursor; không thay Approved\|Blocked (`_PRE_GATHER.md`) |

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

Coordinator **không làm thay** việc thuộc role khác. **Giao đúng agent đúng nhiệm vụ** — user không cần nhắc lại mỗi lần.

Mỗi câu hỏi / yêu cầu của user:

1. **Phân loại** → chọn đúng role (§6b + bảng dưới).
2. **Dispatch** vào pane/agent đó (`worker-start --terminal …` hoặc `terminal send` / orchestration `send`).
3. **Bật `orca-coord-watch`** (§15e) rồi end turn chờ wake.
4. Khi wake: tóm tắt ngắn cho user → **dispatch bước tiếp** (§15f) — không tự đọc lại cả repo để trả lời thay role.
5. **Chỉ tự trả lời** khi: meta khung Orca/playbook/setup máy; **grill fallback** nếu Planner Claude không available; hoặc không khớp role nào; hoặc user Explicit yêu cầu Coordinator làm. **Grill wave mới ưu tiên 03 Planner (Claude) + `grill-me`.**

| Loại câu hỏi / việc | Giao cho | Không giao Coordinator |
|---------------------|----------|------------------------|
| Đọc docs/`specs/`/repo → tổng kết đã làm gì, acceptance, tìm thành phẩm/artifact ở đâu | **02 Explorer (Antigravity)** | ❌ tự grep/đọc thay |
| Viết/sửa `specs/*`, `implementation-plan`, Non-goals, budget, chốt MVP **sau Approve design** | **03 Planner (Claude)** | ❌ viết plan/spec thay (Approve ≠ Coordinator được code docs) |
| Hotfix / bug / ops “sửa nhanh” (kể cả 1 file FE/compose/env wire) | **04 Implementer** rồi **05 Reviewer** (§6c; Fix-only nếu Blocked) | ❌ Coord tự patch “cho nhanh” |
| Implement / sửa production code theo **một** task `[ ]` | **04 Implementer (Antigravity)** | ❌ code thay |
| Viết/sửa tests từ acceptance | **05 Test writer (Cursor)** | ❌ viết test thay |
| So diff vs product-spec, thiếu edge case; sanity docs/plan trước code nếu `next_hint` yêu cầu | **06 Reviewer-5a (Cursor)** | ❌ review thay |
| Pre-gather factual (diff/log/checklist) trước review lớn | **Antigravity** (`_PRE_GATHER.md`) rồi 5a | ❌ AG không verdict |
| Review logic nhạy cảm / filtered diff | **07 Reviewer-5b (Claude)** | ❌ review thay |
| Grill wave mới với user (`grill-me`) | **03 Planner (Claude)** ưu tiên | Coord chỉ grill **fallback** |
| Approve sau grill; setup pane; `coord-watch`; logout Claude; tóm tắt + dispatch | **Coordinator** (được phép) | — |
| Câu mơ hồ | Hỏi user **một** câu làm rõ **hoặc** chọn role gần nhất + ghi giả định khi dispatch | ❌ ôm hết |

**Ví dụ bắt buộc:**  
User: *“kiểm tra `specs/` đã xong chưa, thành phẩm ở đâu?”*  
→ Coordinator **dispatch Explorer**, không tự đọc `specs/` + `find Synopsis.mp4` rồi trả lời.

User: *“Approve”* sau grill  
→ Coordinator **dispatch Planner** materialize `implementation-plan` / product-spec — **không** tự ghi plan.

User: *“hotfix / bật lại Langfuse / bỏ cột UI / sửa compose”*  
→ Coordinator **dispatch Implementer** (1 task rõ touches) → bật `coord-watch` → khi xong **dispatch Reviewer-5a** → chỉ khi `Approved` mới báo user xong (Fix-only nếu Blocked). **Không** tự `StrReplace`/`Write` code trong pane Coord.

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
| A2 | Implementer / Test | Prepend `specs/task-delta.md`: **Task** mô tả làm gì (cấm chỉ `21.4`) + đổi gì + links `#L…` **nhảy đúng dòng đã sửa** (cấm lazy `#L1` trên file edit); thiếu mô tả/`#L`/`#L` lệch = chưa xong; đổi quy ước → sync `orca_setup/` |
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
5. Đưa hướng đi tiếp (một câu rõ: role nào / việc gì) và **dispatch ngay** nếu còn việc trong nhiệm vụ user (§15f).
6. **Cổng SDD (§6c):** sau Implement/Test → (phase lớn: **AG pre-gather** trước) → **Reviewer-5a** (không phải task kế). Sau `Blocked` → Fix-only cùng task. Sau `Approved` → mới được unchecked task tiếp theo.
7. Claude xong (Planner/5b): `orca-claude-after-task --run <runId>` trước khi launch Claude lần sau.

**`orca-roles-run`:** mỗi role spec phải kết thúc bằng khối REPORT_BACK (script materialize từ §12 phải `cat` `_REPORT_BACK.md` vào cuối spec).

---

## 15f. Vòng điều phối đến hết nhiệm vụ (bắt buộc — lab)

**Yêu cầu user:** khi agent xong, Coordinator **phải** nhận tín hiệu và **tiếp tục** đưa hướng / dispatch cho đến khi hoàn thành nhiệm vụ (vd. hết wave checklist), không chờ user nhắc lại.

```text
user mission (vd. wave v19)
        │
        ▼
  dispatch đúng role + orca-coord-watch
        │
        ▼
  [ORCA auto-wake] / report mới
        │
        ▼
  drain → đọc report → tóm tắt user
        │
        ├─ còn task / cổng review? ──yes──► dispatch role kế (đúng bảng §15b)
        │                                      │
        │                                      └── lặp
        └─ hết checklist hoặc user Explicit dừng ──► báo Done / hỏi merge (§17)
```

**Luật cứng**

1. **Không dừng** sau một `worker_done` nếu `implementation-plan` (hoặc brief user) còn `[ ]` thuộc mission đang chạy — trừ Blocked chờ user, hoặc user bảo dừng.
2. Mỗi wake: **một** hướng đi tiếp rõ (role + task id) + `worker-start` (hoặc nói rõ đang chờ user quyết định gì).
3. **Wake trùng:** cùng `message id` / cùng report file đã xử lý → **không** dispatch lại; nêu trạng thái hiện tại (vd. Implementer đang chạy) và tiếp tục chờ wake đúng.
4. `next_hint` trong report là gợi ý; Coordinator vẫn phải kiểm tra cổng §6c + bảng §15b trước khi chọn role.
5. Mission Done chỉ khi: hết `[ ]` trong scope đã Approve, hoặc user Explicit *xong / dừng / đủ rồi*.
6. Khi plan có lane `parallel_ok` sẵn sàng (§15g): sau Approved task blocker, **được** `worker-start` nhiều Implementer cùng lúc (mỗi lane một pane) — vẫn mỗi lane một Review sau đó.

---

## 15g. Lane song song có điều kiện (nhân bản Implementer — giữ chất lượng)

**Mục tiêu:** tăng tốc bằng nhiều task **độc lập** cùng lúc, **không** bỏ cổng SDD, **không** đụng file chung.

### Khi nào được song song

Planner (hoặc Coordinator khi user Explicit *áp §15g*) gắn metadata trên mỗi phase trong `implementation-plan.md`:

```markdown
- **parallel_group:** P1
- **parallel_ok:** yes
- **touches:** `resource/eval/run.py`, `resource/eval/results/baseline.json`
- **depends:** 19.5
```

| Trường | Nghĩa |
|--------|--------|
| `parallel_ok` | `yes` mới được mở cùng lane khác; thiếu/`no` → tuần tự |
| `touches` | Glob/path agent **được phép** sửa; ngoài list = scope creep |
| `parallel_group` | Cùng group + `depends` thỏa → Coordinator được fan-out |
| `depends` | Task id phải `Approved` trước khi mở lane |

**Fail-closed:** nếu hai task cùng group mà `touches` giao nhau (cùng file/dir “nóng” như `agent_turn.py`, `graph.py`, `implementation-plan` checklist dòng đang sửa) → **không** song song; chạy tuần tự.

### Luật cứng chất lượng

1. **Mỗi lane** vẫn: Implement (đúng 1 phase) → Reviewer-5a → Fix-only nếu Blocked → `Approved`. Cấm “gộp review” nhiều lane một lần.
2. **Không** song song Fix-only với task khác nếu `touches` giao.
3. **Shared specs** (`implementation-plan` tick, `change-log`, `gap-analysis`, `session-handoff`): worker **không** tranh chấp — ghi note trong report; **Coordinator** (hoặc Implementer lane xong sau cùng, tuần tự) merge tick/`[x]` + gap sau từng `Approved`. Prefer: mỗi Implementer chỉ tick phase của mình bằng patch hẹp một hunk; nếu conflict → lane sau rebase/retry.
4. **Test writer** vẫn ∥ Implementer **trong cùng lane/task** (như §6); không bắt Test writer chạy cross-lane.
5. **Reviewer:** ưu tiên 1 Reviewer xử lý tuần tự theo lane xong trước; được nhân `06a`/`06b` chỉ khi hai diff thật sự tách và user/plan cho phép.
6. **Pane:** `04a` / `04b` (Antigravity) — launch thêm nếu chưa có; title đúng §15d/§0.18. Report file vẫn `specs/agent-reports/*-04-implementer.md` (timestamp khác nhau).
7. Mặc định **1 Implementer**; fan-out chỉ khi ≥2 task `parallel_ok` + `depends` done + `touches` disjoint.

### Việc Coordinator làm khi fan-out

1. Đọc bảng parallel trong plan; xác nhận `depends` đã Approved.
2. So `touches` — overlap? → tuần tự; không → `worker-start` 04a + 04b (hai spec riêng, ghi rõ `touches` + cấm sửa ngoài list).
3. `orca-coord-watch` một lần cho Run (đủ cho mọi worker_done).
4. Mỗi wake: xử lý **đúng** report đó (review lane đó hoặc merge tick); không bỏ lane kia.
5. Mission chỉ Done khi **mọi** lane trong scope đã Approved (hoặc user dừng).

### Việc Planner làm

Khi viết/chỉnh wave: luôn điền `parallel_ok` / `touches` / `depends` cho từng phase (kể cả `parallel_ok: no`). Không để Coordinator đoán.

### Overflow pane (quota / retry) — ephemerals

Khi phải **spawn pane tạm** (vd. `turn_start_unobserved`, Antigravity quota, Cursor fallback) ngoài bộ title chuẩn §15d:

1. Đặt title rõ: `04a′ overflow (retry)` / `04b′ overflow (cursor-fallback)` — **không** đặt trùng `04a Implementer…` nếu canonical còn sống.
2. Khi task **settle / abandon / hết quota**: ghi `specs/agent-reports/*-overflow-handoff.md` (temp handle → canonical role, artifacts, Approved/Blocked).
3. `orca terminal send` tóm tắt vào **canonical** 04a/04b/04c (hoặc role gốc).
4. **`orca terminal close`** overflow ngay — không giữ duplicate Implementer.
5. Sau re-auth Antigravity:
   - User **đăng nhập lại trong đúng pane** canonical bị quota (logout/`agy` restart trên tab đó — account mới trên máy khác pane không đủ).
   - Coord **probe** ngắn (`worker-start` READY hoặc `agy` một dòng). Còn `Individual quota` → không giao việc; báo user pane chưa re-login.
   - Probe OK → **ngay lập tức** gán việc mở tiếp theo (Fix-only / phase P1 còn trống / peer lane) — **cấm để canonical đứng im** sau khi account đã sống.
   - Overflow Cursor/AG cũ: handoff → close (§ trên); việc chuyển về canonical vừa hồi.

Canonical set mặc định: `01`…`06b` (+ `04c` khi §15g P1 cần 3 lane). Mọi pane ngoài set sau handoff = đóng.

### Skill matrix theo role (bắt buộc ghi trong role + brief)

Skill **không** tự lan giữa Cursor / Claude / Antigravity. Phải (1) cài vào runtime đúng agent, (2) ghi trong `roles/*.md`, (3) Coord nhắc trong brief khi cần.

| Role | Runtime | Skills bắt buộc | Skills khuyến nghị | Không dùng |
|------|---------|-----------------|--------------------|------------|
| **01 Coord** | Cursor | `using-superpowers` (meta: check skill trước mọi action), `orchestration`, `grill-me` (fallback nếu Planner không grill), `dispatching-parallel-agents`, `finishing-a-development-branch`, `verification-before-completion` | `brainstorming` khi design xanh | `ponytail` viết app; TDD implement |
| **02 Explorer** | Antigravity | (đọc repo) | `ponytail` khi tóm tắt | grill / writing-plans |
| **03 Planner** | **Claude** | **`grill-me`** (interview user trước plan wave mới trừ brief ghi `grill_skipped: Approved`), `writing-plans` / plan_self_review §6d | `brainstorming` nếu scope lớn chưa chốt | implement / review adversarial dài |
| **04 Implementer** | Antigravity | **`ponytail` (full)** mỗi task; `verification-before-completion` | `test-driven-development`, `systematic-debugging` (Fix-only) | grill user; viết wave plan |
| **05 Test** | Cursor | `test-driven-development`, `verification-before-completion` | `using-superpowers` | grill design |
| **06 Reviewer-5a** | Cursor | adversarial checklist; `verification-before-completion` | AG `_PRE_GATHER` trước phase lớn; AG overflow: `ponytail-review` | implement |
| **05′ Pre-gather** | Antigravity | factual only (`_PRE_GATHER.md`) | không verdict | phán Approved/Blocked |
| **07 Reviewer-5b** | Claude | logic/diff nhạy cảm | `grill-me` không — đã qua plan | implement |

**`using-superpowers`:** meta-skill Cursor (“trước mọi việc, invoke skill liên quan”). Gắn **01 Coord** (bắt buộc) + mọi **Cursor** pane (05/06a) khi mở turn. Claude/Antigravity: không có slash Cursor — thay bằng dòng role “trước khi làm, load skill list của runtime (Claude `~/.claude/skills`, AG `~/.gemini/antigravity/skills`) và chạy skill khớp”.

**`grill-me` trên Claude (03):** user ưu tiên Claude thông minh hơn Cursor cho interview. Wave mới: Planner **hỏi từng câu** (design tree) → user trả lời (qua pane / `ask`) → rồi mới viết 4 specs. Coord brief có `grill_skipped: <lý do Explicit>` thì bỏ grill, chỉ `plan_self_review`.

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
- Khi nhận tin `[ORCA auto-wake]`: chạy `orca-coord-drain --run <runId> --workdir <project>` (hoặc tương đương), đọc report, tóm tắt user, **dispatch bước tiếp theo §15f** — **không** hỏi lại “đã xong chưa?” và **không** chờ user paste ảnh / nhắc “tiếp đi”.
- Wake trùng cùng msg/report đã settle → bỏ qua dispatch trùng; báo đang chờ worker nào.

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
| Tự review plan (số mục không cố định) trước Implement | Có | §6c, §6d, roles/02-planner, guide VN bước 3 |
| Bọc FGS / metrics / GPU fixture / TDD | Có | §14 |
| Coordinator chỉ điều phối; đọc docs/tổng kết → Explorer | Có | §15b |
| Mọi agent báo Coordinator (file inbox + worker_done) | Có | §0.13, §15c |
| Auto-wake Cursor Coordinator (`orca-coord-watch`) | Có | §0.14, §15e |
| Đúng role; Approve → Planner; vòng đến hết mission | Có | §0.12, §0.15, §15b, §15f |
| Lane song song `parallel_ok` + `touches` disjoint | Có | §0.16, §15g |
| Wake trùng không dispatch lại | Có | §15f.3, §15e |
| Sau xong workspace: test → commit → merge main → (push) → không tự xóa Orca WT | Có | §17 |
| Verify: review đối kháng + bằng chứng; eval metric; không AI thay lint/test | Có | §18 |
| Tên tab `01 Spec / Coordinator` … `04a`/`04b` Implementer … | Có | §0.18, §15d, §15g |
| Interactive login Claude khi start | Có | §8 |
| Materialize scripts + symlink trên máy mới | Có | §2–§3, §12 |

---

*Hết file. Agent chỉ cần file này (+ repo FGS) để setup máy mới và vận hành đúng kiến trúc đã chốt.*
