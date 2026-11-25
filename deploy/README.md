# Deploy — local-first (Phase 21.3)

Scripts for **immutable image tag = git SHA**, deploy / smoke / rollback on a developer
machine or CI runner. Ported principles from
`resource/knowledge_handbook/llm-engineer-demo/deploy/`, without sudo, systemd, nginx, or GCP.

## Layout

```
deploy/
├── release.sh   # build | deploy <tag> | smoke | rollback | status
├── smoke.py     # /api/health → /ready → optional --ask
├── README.md
└── .state/      # gitignored: .current + .lkg
```

## Demo principles → this repo

| Principle (demo) | Here |
|---|---|
| Image tag = git SHA (immutable) | `chatkcn:<short-sha>` via `release.sh build` |
| Deploy = switch pointer, not rebuild | `release.sh deploy <tag>` runs that tag |
| LKG written **before** switch | `deploy/.state/.lkg` ← previous `.current` |
| Promote on smoke, not “container up” | `release.sh smoke` → `smoke.py` |
| Rollback without rebuild | `release.sh rollback` → previous LKG image |
| Cloud optional / gated | see **Cloud (optional)** below — default off |

## Prerequisites

1. Docker available (no root/sudo required for normal docker group usage).
2. `.env` at repo root — **real** config (symlink/copy from main checkout), not dummy `sk-x`.
   - Example: `ln -sfn /path/to/kcn_hungphu_agent/.env .env`
   - Default `DOCKER_NETWORK=compose`: gắn network compose + `agent_postgres` / `qdrant`.
   - GitHub `cd.yml` smoke: `secrets.OPENAI_API_KEYS` + `MEMORY_ENABLED=false` / empty DB — CI unit hermetic như demo.
3. Python with `httpx` (already pulled via `requirements.txt` / openai stack).
4. Local deps: `docker compose up -d agent_postgres qdrant` trước `release.sh deploy`.
5. (Tuỳ chọn) Langfuse cùng network — file riêng, `down` không đụng app:
   `docker compose -f docker-compose.observability.yml --env-file langfuse/.env up -d`
   → app dùng `LANGFUSE_HOST=http://langfuse-web:3000` (override trong `release.sh` / `docker-compose.yml`).

## Local flow (thật)

```bash
# 0) .env thật từ folder gốc
ln -sfn /home/atin/dong/dong/KCNHungPhu/kcn_hungphu_agent/.env .env

# 0b) Postgres + Qdrant (+ network kcn_hungphu_network)
docker compose up -d agent_postgres qdrant

# 0c) Langfuse (project kcn-hungphu-obs — down riêng được)
docker compose -f docker-compose.observability.yml --env-file langfuse/.env up -d

# 1) Build
./deploy/release.sh build

# 2) Deploy (compose network). PORT≠8000 nếu host đã chiếm 8000.
PORT=8010 ./deploy/release.sh deploy "$(git rev-parse --short HEAD)"

# 3) Smoke + optional live ask
PORT=8010 ./deploy/release.sh smoke
# --ask cần Bearer khi IAM_REQUIRED=true:
SMOKE_BEARER_TOKEN=... python deploy/smoke.py --url http://127.0.0.1:8010 --ask --token "$SMOKE_BEARER_TOKEN"

# 4) status / 5) rollback
PORT=8010 ./deploy/release.sh status
PORT=8010 ./deploy/release.sh rollback

# Tắt chỉ Langfuse (giữ agent DB + chatkcn):
docker compose -f docker-compose.observability.yml --env-file langfuse/.env down
```

State: `deploy/.state/.current` / `.lkg` (gitignored).  
`DOCKER_NETWORK=host` (PORT=8000) khi DB/Qdrant listen trên host localhost.  
`DOCKER_NETWORK=bridge` cho CI-like.

## Cloud (optional)

Cloud push / SSH deploy are **not** enabled by these scripts. When Phase 21.4
workflows land, they stay gated behind repository variables (default skip):

| Variable / secret | Purpose | Default |
|---|---|---|
| `ENABLE_REGISTRY_PUSH` | Push `chatkcn:<sha>` to GHCR from `cd.yml` | `false` / unset → skip |
| `ENABLE_SSH_DEPLOY` | Run `deploy.yml` SSH → VM `release.sh` | `false` / unset → skip |
| `VM_SSH_KEY` / `VM_HOST` / `VM_USER` | Only if SSH deploy is later enabled | — |
| Registry token / WIF | Only if registry push / cloud auth is later enabled | — |

Do **not** turn on registry push and SSH deploy against the same host at once
(two pipelines fighting over the same container). Local `release.sh` remains
the source of truth for deploy / rollback / status even when cloud jobs exist.
