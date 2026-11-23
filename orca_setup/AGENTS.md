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

Chi tiết: `ORCA-AGENT-SETUP.md` — không nhân bản quy tắc ở đây.
