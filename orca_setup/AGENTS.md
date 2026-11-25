# AGENTS.md

## Setup máy mới / thiếu playbook

Đọc và làm theo:

**[ORCA-AGENT-SETUP.md](ORCA-AGENT-SETUP.md)**

Probe máy → cài `$HOME/orca/playbooks` (roles từ `orca_setup/roles/`, scripts từ `orca-playbook/bin/` hoặc §12) → symlink → smoke → marker `.orca-playbook-installed`.

Nếu `.orca-playbook-installed` đã có: bỏ qua setup trừ khi user bảo cập nhật.

## Vận hành sau setup

- Fallback: `claude → cursor → antigravity` (`agent-fallback`)
- Claude xong task: `orca-claude-after-task --run <id>`
- Mở Orca: `orca-open`
- DAG: `orca-roles-run --brief "..."`
- **Đúng role (§15b):** Explorer đọc/tổng kết · Planner spec/plan (cả sau Approve) · Implementer code · Test writer test · Reviewer review · Coordinator chỉ điều phối (+ grill fallback). **Hotfix/ops cũng Implementer→Reviewer (§6c)** — Coord cấm tự patch trừ user Explicit.
- **Skill matrix (§15g):** Coord=`using-superpowers`+orchestration (+grill **fallback**); **Planner Claude=`grill-me` rồi plan** (ưu tiên); Implementer=`ponytail`; **Reviewer-5a=`cursor`**; phase lớn → **AG `_PRE_GATHER`** (diff/log/checklist factual) rồi Cursor verdict; Fix-only nhỏ skip AG. Stall/`start_unknown` → retry/reassign, không để idle.
- **Quota / re-auth Antigravity (§15g overflow):** sau login account mới, Coord probe canonical pane rồi **giao việc ngay** (không để 04a/04b/04c idle); login phải nằm **trong đúng tab** bị quota.
- **SDD loop (§6c):** Plan → **tự review plan §6d** (`plan_self_review: pass`; số phase theo scope, không copy cứng ví dụ guide) → Implement (1 task) → tick plan + `change-log` + **`specs/task-delta.md`** (**Task** = làm gì + đổi gì + links `#L…` **nhảy đúng dòng đã sửa**; cấm lazy `#L1` trên file edit; không dán before/after) → nếu đổi quy ước thì sync **`orca_setup/`** → Review (Blocked nếu `#L` lệch) → Fix nếu Blocked → `Approved` rồi task kế. Áp dụng cả **hotfix** (Implement → Review → Approved), không rút gọn “Coord sửa luôn”.
- **Auto-wake (§15e):** sau mỗi `worker-start` → `orca-coord-watch`. Khi `[ORCA auto-wake]` → drain + đọc report + **dispatch tiếp** (không chờ nhắc).
- **Đến hết mission (§15f):** lặp wake→tóm tắt→dispatch đến hết checklist / user dừng; bỏ qua wake trùng.
- **Lane song song (§15g):** nhân bản Implementer (04a/04b/04c) chỉ khi `parallel_ok` + `touches` không giao; mỗi lane vẫn Review→Approved. Pane overflow (quota/retry) → handoff log → canonical → **close**.

Chi tiết: `ORCA-AGENT-SETUP.md` — không nhân bản quy tắc ở đây.
