# Langfuse (self-hosted)

Stack observability — **project Compose riêng** (`kcn-hungphu-obs`), join cùng network app `kcn_hungphu_network`.  
Nguồn sự thật: [`../docker-compose.observability.yml`](../docker-compose.observability.yml).  
`docker compose down` file obs **không** tắt `agent_postgres` / `qdrant` / app.

## Chạy (từ repo root)

```bash
# 0) Agent infra (tạo kcn_hungphu_network nếu chưa có)
docker compose up -d agent_postgres qdrant

# 1) Langfuse + deps
cp langfuse/.env.example langfuse/.env   # nếu chưa có
docker compose -f docker-compose.observability.yml --env-file langfuse/.env up -d

# Tương thích cũ:
cd langfuse && docker compose --env-file .env up -d
```

Container/volume giữ prefix `kcn_hungphu_langfuse_*`. Web/worker gắn **hai** network: `kcn_hungphu_langfuse_network` (deps) + `kcn_hungphu_network` (app → `http://langfuse-web:3000`).

**Web UI tùy biến:** `langfuse-web` build từ `Dockerfile.web` — latency 3 chữ số thập phân. Sau pull image mới:

```bash
docker compose -f docker-compose.observability.yml --env-file langfuse/.env build langfuse-web
docker compose -f docker-compose.observability.yml --env-file langfuse/.env up -d langfuse-web
```

Clear cache browser cho `http://192.168.1.198:3001` nếu chunk Next cũ.

## Dừng / reset

```bash
# Chỉ tắt obs (app + agent DB vẫn chạy)
docker compose -f docker-compose.observability.yml --env-file langfuse/.env down

# Reset data Langfuse
docker compose -f docker-compose.observability.yml --env-file langfuse/.env down -v
docker compose -f docker-compose.observability.yml --env-file langfuse/.env up -d
```

## Đăng nhập UI

- URL: http://localhost:3001 (host map `3001:3000`)
- Email: `admin@agent-atin.local` / `Atin@123#`
- Project: **agent_ATIN**
- Keys khớp `../.env`: `pk-lf-0c271516-…` / `sk-lf-cda213a6-…`

## Kết nối backend

| Chạy backend | `LANGFUSE_HOST` |
|---|---|
| Compose / `release.sh` (`DOCKER_NETWORK=compose`) | `http://langfuse-web:3000` (override trong compose/release) |
| Host uvicorn | `http://localhost:3001` trong `.env` |
