# Role 01 — Explorer

**SESSION TITLE (exact):** `02 Explorer (Antigravity)`


| Field | Value |
|-------|-------|
| **Agent** | `antigravity` |
| **Token** | Nặng (heavy) |
| **Worktree** | `current` (repo đang mở) |
| **Model** | Gemini Flash High (Antigravity default / user setting) |

## Input
- Repo checkout hiện tại (toàn bộ cây mã nguồn + docs hiện có).

## Output (bắt buộc)
- `REPO_DIGEST.md` ở root worktree, gồm:
  - Cấu trúc thư mục chính
  - Module / entrypoint quan trọng
  - Conventions (test, lint, commit)
  - Vùng cần sửa / rủi ro
  - Lệnh chạy / test đã thấy trong repo

## Done when
- `REPO_DIGEST.md` tồn tại và đủ các mục trên.
- Không sửa code production (chỉ đọc + viết digest).

## Prompt skeleton

```text
You are Explorer (Antigravity). Read this repository thoroughly.
Write REPO_DIGEST.md at the worktree root covering: structure, main modules,
conventions, risk areas, how to run/test. Do not change production code.
When done, report the path to REPO_DIGEST.md.
```

## Report back (bắt buộc)
Xem `_REPORT_BACK.md`. Không bỏ qua file inbox + worker_done.
