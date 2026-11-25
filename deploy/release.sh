#!/usr/bin/env bash
# Local release/rollback for chatkcn (Phase 21.3).
# Image tag = git SHA (immutable). No sudo / no systemd.
#
#   ./deploy/release.sh build
#   ./deploy/release.sh deploy <tag>
#   ./deploy/release.sh smoke
#   ./deploy/release.sh rollback
#   ./deploy/release.sh status
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

IMAGE=chatkcn
CONTAINER=chatkcn-app
PORT="${PORT:-8000}"
# compose = gắn docker-compose network (agent_postgres / qdrant) — khuyến nghị chạy thật local.
# host   = dùng localhost trong .env (cần Postgres :5433 + Qdrant trên host; PORT phải 8000).
# bridge = CI runner / map -p (không resolve localhost host services).
DOCKER_NETWORK="${DOCKER_NETWORK:-compose}"
COMPOSE_NETWORK_NAME="${COMPOSE_NETWORK_NAME:-}"
STATE_DIR="$ROOT/deploy/.state"
CURRENT_FILE="$STATE_DIR/.current"
LKG_FILE="$STATE_DIR/.lkg"
ENV_FILE="$ROOT/.env"
SMOKE_PY="$ROOT/deploy/smoke.py"

log() { echo "==> $*"; }
die() { echo "error: $*" >&2; exit 1; }

ensure_state_dir() {
    mkdir -p "$STATE_DIR"
}

git_sha() {
    git -C "$ROOT" rev-parse --short HEAD
}

read_tag() {
    local f="$1"
    if [ -f "$f" ]; then
        tr -d '[:space:]' <"$f"
    fi
}

wait_ready() {
    local tries="${1:-30}"
    local url="http://127.0.0.1:${PORT}/ready"
    local i
    for i in $(seq "$tries"); do
        if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    return 1
}

stop_container() {
    if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
        log "Stopping $CONTAINER"
        docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
    fi
}

resolve_compose_network() {
    if [ -n "$COMPOSE_NETWORK_NAME" ]; then
        echo "$COMPOSE_NETWORK_NAME"
        return 0
    fi
    local n
    n="$(docker network ls --format '{{.Name}}' | grep -E 'kcn.*network|kcn_network' | grep -v langfuse | head -n1 || true)"
    [ -n "$n" ] || die "compose network not found — run: docker compose up -d agent_postgres qdrant"
    echo "$n"
}

# Parse .env → KEY=VALUE lines for `docker run -e` (giữ nguyên # trong password;
# docker --env-file cắt tại # nếu không quote, còn quote thì pydantic nhận cả dấu ").
load_env_e_args() {
    local src="$1"
    python3 - "$src" <<'PY'
import sys
from pathlib import Path
src = Path(sys.argv[1])
for raw in src.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, val = line.split("=", 1)
    key = key.strip()
    if not key:
        continue
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
        val = val[1:-1]
    # NUL-separated for bash read -d ''
    sys.stdout.buffer.write(f"{key}={val}".encode("utf-8") + b"\0")
PY
}

run_container() {
    local tag="$1"
    [ -f "$ENV_FILE" ] || die "missing $ENV_FILE — copy from main checkout or: cp .env.example .env"
    docker image inspect "${IMAGE}:${tag}" >/dev/null 2>&1 \
        || die "image ${IMAGE}:${tag} not found — run: $0 build (or docker pull)"

    stop_container
    ensure_state_dir

    log "Starting ${IMAGE}:${tag} as $CONTAINER (network=${DOCKER_NETWORK}, port=${PORT})"
    local -a run_args=(run -d --name "$CONTAINER")
    local kv
    while IFS= read -r -d '' kv; do
        run_args+=(-e "$kv")
    done < <(load_env_e_args "$ENV_FILE")

    case "$DOCKER_NETWORK" in
        host)
            if [ "$PORT" != "8000" ]; then
                die "DOCKER_NETWORK=host requires PORT=8000 (image listens on 8000); got PORT=$PORT"
            fi
            run_args+=(--network host)
            ;;
        compose)
            local cnet
            cnet="$(resolve_compose_network)"
            # Override localhost từ .env → service names trên compose network (giống docker-compose.yml).
            # Langfuse: docker-compose.observability.yml join cùng kcn_hungphu_network → DNS langfuse-web.
            run_args+=(
                --network "$cnet"
                -p "${PORT}:8000"
                -e AGENT_DB_HOST=agent_postgres
                -e AGENT_DB_PORT=5432
                -e QDRANT_URL=http://qdrant:6333
                -e LANGFUSE_HOST=http://langfuse-web:3000
                --add-host=host.docker.internal:host-gateway
            )
            ;;
        *)
            run_args+=(--network "$DOCKER_NETWORK" -p "${PORT}:8000" --add-host=host.docker.internal:host-gateway)
            ;;
    esac
    run_args+=("${IMAGE}:${tag}")
    docker "${run_args[@]}" >/dev/null
}

do_build() {
    local sha
    sha="$(git_sha)"
    [ -n "$sha" ] || die "cannot resolve git SHA"
    log "Building ${IMAGE}:${sha}"
    docker build -t "${IMAGE}:${sha}" "$ROOT"
    log "Built ${IMAGE}:${sha}"
    echo "$sha"
}

do_deploy() {
    local tag="${1:-}"
    [ -n "$tag" ] || die "usage: $0 deploy <tag>"
    ensure_state_dir

    local old
    old="$(read_tag "$CURRENT_FILE")"
    log "Deploy ${IMAGE}:${tag} (current: ${old:-none})"

    # Write LKG before switching so rollback always has a target.
    if [ -n "$old" ] && [ "$old" != "$tag" ]; then
        printf '%s\n' "$old" >"$LKG_FILE"
        log "Recorded last-known-good = $old"
    fi

    run_container "$tag"
    printf '%s\n' "$tag" >"$CURRENT_FILE"

    if wait_ready 30; then
        log "Healthy (/ready) with ${IMAGE}:${tag}"
    else
        # Do not auto-rollback: caller runs smoke then decides.
        die "container not ready on :${PORT}/ready after ~60s"
    fi
}

do_smoke() {
    [ -f "$SMOKE_PY" ] || die "missing $SMOKE_PY"
    python "$SMOKE_PY" --url "http://127.0.0.1:${PORT}"
}

do_rollback() {
    ensure_state_dir
    local lkg
    lkg="$(read_tag "$LKG_FILE")"
    [ -n "$lkg" ] || die "no last-known-good in $LKG_FILE — cannot rollback"

    log "Rollback to last-known-good: $lkg"
    run_container "$lkg"
    printf '%s\n' "$lkg" >"$CURRENT_FILE"

    wait_ready 30 || die "rollback finished but /ready still failing"
    log "Rolled back to $lkg and /ready OK"
}

do_status() {
    ensure_state_dir
    echo "current = $(read_tag "$CURRENT_FILE" || true)"
    echo "lkg     = $(read_tag "$LKG_FILE" || true)"
    if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
        echo "container = running ($CONTAINER)"
    elif docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
        echo "container = stopped ($CONTAINER)"
    else
        echo "container = (none)"
    fi
    docker images "$IMAGE" --format '{{.Repository}}:{{.Tag}}  {{.CreatedSince}}' 2>/dev/null || true
}

case "${1:-}" in
    build)    do_build ;;
    deploy)   shift; do_deploy "${1:-}" ;;
    smoke)    do_smoke ;;
    rollback) do_rollback ;;
    status)   do_status ;;
    *) die "usage: $0 {build|deploy <tag>|smoke|rollback|status}" ;;
esac
