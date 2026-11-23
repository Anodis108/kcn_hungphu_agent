# orca_setup — gói markdown mang máy khác

Cho agent / bạn: **bắt đầu từ `ORCA-AGENT-SETUP.md`**.

| File | Việc |
|------|------|
| `ORCA-AGENT-SETUP.md` | Nguồn sự thật: setup máy + DAG + SDD loop (§6c) + auto-wake (§15e) + verify + merge |
| `OPEN-IN-ORCA.md` | 3 bước mở trên máy cá nhân |
| `AGENTS.md` | Rule ngắn trỏ về setup |
| `Spec Driven Development Guide - Vietnamese.md` | Guide SDD (specs/) |
| `multi-agent-role-setup.md` | Tóm tắt vận hành multi-role |
| `roles/*.md` | Role 01–05 + `_REPORT_BACK` + `_VERIFY` |
| `bin/orca-coord-watch` | Auto-wake Coordinator khi `worker_done` / report mới |
| `bin/orca-coord-drain` | Drain inbox + reports đầu turn Coordinator |
| `SESSION-TITLES.md` | Tên tab bắt buộc (`03 Planner (Claude)`, …) |

**Nằm ngoài gói (tuỳ máy):** các script playbook khác (`agent-fallback`, `claude-session`, …) nếu chưa có ở `$HOME/orca/playbooks/bin/` — copy từ máy lab hoặc materialize theo §12. Orca CLI, login agent, GPU/fixture.

Trên máy mới: copy cả `videosynopsis-fgs/` (hoặc ít nhất `orca_setup/` + `orca-playbook/bin/`) → bảo agent đọc `orca_setup/ORCA-AGENT-SETUP.md` và setup.
