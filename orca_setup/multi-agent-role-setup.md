# Orca multi-agent roles + Claude logout — setup lại từ đầu

Playbook toàn máy. Đường dẫn gốc: `/home/atin/orca/playbooks/`.

Dùng cho **mọi project** Orca. Không gắn riêng một repo.

---

## 0. Giới hạn cần nhớ

| Sự thật | Ý nghĩa |
|---------|---------|
| Orca **không** có native “quit → logout” | Dùng wrapper `orca-open` |
| `orca account rm` không xóa **system** credentials | Claude hệ thống nằm ở `~/.claude/.credentials.json` |
| Logout **không** reset quota Anthropic 5h/tuần | Chỉ ngắt session / buộc login lại |
| `account add` Claude thường cần browser | Có bước người khi `claude-session start` |

### Token fallback (bắt buộc)

Trong **mọi** trường hợp chọn agent:

```text
claude  →  (hết token)  →  cursor  →  (hết token)  →  antigravity
```

- Ngưỡng mặc định: `usedPercent >= 95` (session hoặc weekly). Đổi bằng `AGENT_FALLBACK_THRESHOLD`.
- Cursor thường **không** có % trong `orca account list` → khi UI báo hết token:  
  `agent-fallback mark-exhausted cursor`
- Tool: `bin/agent-fallback` (`resolve` / `status` / `mark-exhausted` / `clear-exhausted`).

---

## 1. Prerequisites

- Orca runtime chạy được: `orca status --json`
- Agents: **antigravity**, **claude**, **cursor** (đúng id Orca)
- CLI: `/home/atin/.orca/cli/bin/orca` (hoặc `ORCA_CLI_COMMAND`)

Kiểm tra:

```bash
orca status --json | head
orca account list --json | head
ls /home/atin/orca/playbooks/bin
```

---

## 2. Cài playbook (một lần / máy)

Nếu thư mục chưa có (máy mới), copy lại cây này:

```text
/home/atin/orca/playbooks/
├── multi-agent-role-setup.md    ← file này
├── roles/
│   ├── 01-explorer.md
│   ├── 02-planner.md
│   ├── 03-implementer.md
│   ├── 04-test-writer.md
│   └── 05-reviewer.md
├── bin/
│   ├── agent-fallback
│   ├── claude-session
│   ├── orca-claude-after-task
│   ├── orca-roles-run
│   ├── orca-quit-logout
│   └── orca-open
├── desktop/
│   └── orca-with-logout.desktop
└── logs/
```

Cài symlink + desktop:

```bash
chmod +x /home/atin/orca/playbooks/bin/*
mkdir -p ~/.local/bin ~/.local/share/applications
ln -sfn /home/atin/orca/playbooks/bin/orca-open           ~/.local/bin/orca-open
ln -sfn /home/atin/orca/playbooks/bin/claude-session      ~/.local/bin/claude-session
ln -sfn /home/atin/orca/playbooks/bin/agent-fallback      ~/.local/bin/agent-fallback
ln -sfn /home/atin/orca/playbooks/bin/orca-roles-run      ~/.local/bin/orca-roles-run
ln -sfn /home/atin/orca/playbooks/bin/orca-quit-logout    ~/.local/bin/orca-quit-logout
ln -sfn /home/atin/orca/playbooks/bin/orca-claude-after-task ~/.local/bin/orca-claude-after-task
cp /home/atin/orca/playbooks/desktop/orca-with-logout.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications 2>/dev/null || true
# Đảm bảo ~/.local/bin nằm trong PATH
grep -q '.local/bin' ~/.bashrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

---

## 3. Năm vai (khớp bảng phân công)

| # | Session | AI | Token | Việc |
|---|---------|-----|-------|------|
| 1 | Explorer | Antigravity | Nặng | Đọc repo → `REPO_DIGEST.md` |
| 2 | Planner | Claude (plan) | Nhẹ | Digest → `specs/` (guide VN) → **logout Claude** |
| 3 | Implementer | Antigravity | Nặng nhất | Worktree `new-child`, **một** task `[ ]` rồi dừng chờ review |
| 4 | Test writer | Cursor | Vừa | Test từ acceptance **cùng** task (song song 3) |
| 5a | Reviewer | Cursor | Vừa | pass/fail/missing vs spec → `Approved`\|`Blocked` (cổng SDD) |
| 5b | Reviewer | Claude | Nhẹ | Filtered diff → **logout Claude** |

**Cổng SDD (bắt buộc):** Implement → Review → Fix-only nếu Blocked → `Approved` → mới task kế. Chi tiết: `ORCA-AGENT-SETUP.md` §6c.

Chi tiết prompt: `roles/0N-*.md`.

---

## 3b. Kiểm tra / ép fallback

```bash
agent-fallback status
agent-fallback resolve claude    # in ra agent thật sẽ dùng
agent-fallback mark-exhausted claude   # giả lập hết token Claude → sẽ ra cursor
agent-fallback resolve claude
agent-fallback mark-exhausted cursor   # tiếp → antigravity
agent-fallback resolve claude
agent-fallback clear-exhausted         # xóa mọi mark thủ công
```

`orca-roles-run` tự gọi `agent-fallback resolve` trước mỗi role có preferred agent.

---

## 4. Claude lifecycle (sau mỗi nhiệm vụ Claude)

### Trước khi launch Claude

```bash
claude-session start
# Nếu đã logout: interactive `orca account add --agent claude`
# hoặc khôi phục archive system credentials
```

### Sau khi Claude worker xong

```bash
# Có Run id:
claude-session stop --yes --run run_XXXX --archive-system

# Hoặc helper:
orca-claude-after-task --run run_XXXX
```

Hành vi `stop`:

1. `worker-stop` các dispatch Claude trên Run (nếu có `--run`)
2. `orca account rm` mọi managed Claude account
3. Nếu chỉ còn system auth → **archive** `~/.claude/.credentials.json` → `*.playbook-archived.*`

`start` sẽ restore archive gần nhất hoặc chạy `account add`.

### Kiểm tra

```bash
claude-session status
```

---

## 5. Logout khi tắt Orca (lựa chọn A)

**Không** mở Orca trực tiếp nếu muốn auto logout. Dùng:

```bash
orca-open
# hoặc launcher desktop: "Orca (playbook quit-logout)"
```

Khi process/runtime Orca dừng → `orca-quit-logout` → Claude cleared.

Thêm best-effort Antigravity/Cursor notes:

```bash
orca-open --all-logout
# hoặc
orca-quit-logout --all
```

---

## 6. Chạy DAG trên project bất kỳ

```bash
cd /path/to/your/project   # Orca-managed worktree
orca-roles-run --brief "Mô tả tính năng / bug cần làm"

# Chỉ in lệnh (không spawn):
orca-roles-run --brief "..." --dry-run
```

Coordinator:

1. **Giao đúng agent đúng việc** (§15b): Approve design → Planner viết plan; không tự viết `implementation-plan` / không code thay Implementer.
2. **Ngay sau `worker-start`:** `orca-coord-watch --run <runId> --terminal <coordTerm> --workdir <project>` (§15e).
3. Khi nhận `[ORCA auto-wake]`: `orca-coord-drain` → đọc report → tóm tắt user → **dispatch tiếp đến hết mission** (§15f). Không chờ user nhắc. Wake trùng → không dispatch lại.
4. **§15g:** nếu plan có ≥2 task `parallel_ok` + `depends` xong + `touches` disjoint → được `worker-start` nhiều Implementer (04a/04b); mỗi lane vẫn Review riêng. Overlap touches → tuần tự.
4. Sau role **2** và **5b**: chạy `orca-claude-after-task --run <runId>`.
5. State file: `.orca-roles-run-state.json` trong workdir.  
   *(Lưu ý: `orca-coord-watch` peek inbox — không thay `orchestration check` của agent.)*

---

## 7. Chuyển Claude sang managed account (khuyến nghị)

Hiện máy có thể đang dùng system `~/.claude/.credentials.json`.

```bash
orca account add --agent claude
orca account select --agent claude --account <id|email>
claude-session status
```

Sau đó `stop` dùng `account rm` sạch hơn; vẫn kết hợp `--archive-system` nếu system file còn.

---

## 8. Troubleshooting

| Triệu chứng | Xử lý |
|-------------|--------|
| `stop` rồi Claude vẫn chạy được | Kiểm tra `~/.claude/.credentials.json` còn không; chạy lại với `--archive-system` |
| `start` đòi browser | Đúng thiết kế — hoàn tất login rồi tiếp |
| Quota vẫn đầy sau logout | Bình thường — logout không reset Anthropic window |
| `worker-start` tạo session Cursor thừa | Chỉ dùng `orca-roles-run` / dispatch vào terminal sẵn có; không `worker-start --agent cursor` ngoài vai 4/5a |
| `new-child` bị từ chối | Cập nhật Orca; script đã truyền `--name impl-HHMMSS` |
| Antigravity vẫn login sau quit | Cần sign-out trong Settings > AI Provider Accounts (`--all` chỉ nhắc) |

---

## 9. Smoke checklist sau khi setup

```bash
claude-session status
claude-session stop --dry-run --yes --archive-system
orca-quit-logout --dry-run
cd /path/to/project && orca-roles-run --brief "smoke" --dry-run
ls ~/.local/bin/orca-open ~/.local/share/applications/orca-with-logout.desktop
```

Ghi Notes: dry-run phải in rõ `would mv ...credentials.json` và 5 worker-start (explorer→reviewer-claude).

---

## 10. Copy-paste nhanh cho project mới

```bash
cd /path/to/project
orca-roles-run --brief "YOUR REQUEST HERE"
# ... khi Planner (Claude) xong:
orca-claude-after-task --run "$(jq -r .runId .orca-roles-run-state.json)"
# ... khi Reviewer Claude xong:
orca-claude-after-task --run "$(jq -r .runId .orca-roles-run-state.json)"
```

Mở Orca hàng ngày:

```bash
orca-open
```

---

## 11. Liên kết từ repo cụ thể

Repo research có thể trỏ tới playbook:

`docs/orca/README.md` → `/home/atin/orca/playbooks/multi-agent-role-setup.md`

Không commit secrets / credentials vào Git.

## Smoke Notes (2026-11-20)

- `claude-session status`: system credentials PRESENT; no managed Claude accounts.
- `orca-quit-logout --dry-run`: would archive `~/.claude/.credentials.json`.
- `orca-roles-run --dry-run`: emits worker-start for roles 1–5b with Claude start gates.
- Symlinks installed under `~/.local/bin/`; desktop `orca-with-logout.desktop` installed.
- Fallback: `mark-exhausted claude` → resolve `cursor`; + `cursor` → resolve `antigravity`; `clear-exhausted` → `claude` again.
