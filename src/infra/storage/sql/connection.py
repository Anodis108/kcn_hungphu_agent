"""Kết nối Postgres read-only — 5 database nguồn thống kê thật:

    its           — plate_event (lượt ra/vào + biển số + loại xe, camera ITS)
    virtual_fence — zone_event (xâm nhập khu vực hàng rào ảo)
    smart_face    — smf_face_events (nhận diện khuôn mặt) [Phase 2, mới]
    firesmoke     — fire_smoke_event (cháy/khói) [Phase 2, mới]
    anomaly       — anomaly_event (ẩu đả/đám đông/leo trèo/mực nước) [Phase 2, mới]

Dùng role riêng CHỈ có quyền SELECT trên 5 DB này (không phải superuser/dev) —
xem README mục "Tạo DB role read-only" + specs/change-log.md 2026-09-17 (đã
GRANT SELECT cho 3 DB mới trên role agent_readonly có sẵn). Mỗi connection
còn tự set `default_transaction_read_only = on` làm lớp chặn thứ hai ở tầng
DB, độc lập với việc validate SQL ở tầng code (src/agent/tools.py, Phase 4-5).
"""

from __future__ import annotations

import asyncio
import re
from contextlib import contextmanager
from typing import Any, Callable

from src.shared.settings import settings

DEFAULT_SQL_LIMIT = 500
DEFAULT_STATEMENT_TIMEOUT_MS = 5000

_LIMIT_REGEX = re.compile(r"\blimit\s+\d+", re.IGNORECASE)


def enforce_sql_limit(sql: str, default_limit: int = DEFAULT_SQL_LIMIT) -> str:
    """Tự động thêm LIMIT nếu câu lệnh SELECT chưa có LIMIT."""
    cleaned = (sql or "").strip()
    if not cleaned:
        return sql
    # Kiểm tra xem đã có LIMIT chưa
    if not _LIMIT_REGEX.search(cleaned):
        # Bỏ dấu chấm phẩy cuối câu nếu có
        body = cleaned.rstrip().rstrip(";")
        return f"{body} LIMIT {int(default_limit)};"
    return sql


async def run_with_timeout_async(fn: Callable[..., Any], *args: Any, timeout_seconds: float = 5.0, **kwargs: Any) -> Any:
    """Wrapper thực thi tool bất đồng bộ với timeout qua asyncio.wait_for."""
    try:
        return await asyncio.wait_for(asyncio.to_thread(fn, *args, **kwargs), timeout=timeout_seconds)
    except TimeoutError as exc:
        raise TimeoutError(f"Thực thi tool quá thời gian chờ ({timeout_seconds}s).") from exc


def run_with_timeout(fn: Callable[..., Any], *args: Any, timeout_seconds: float = 5.0, **kwargs: Any) -> Any:
    """Wrapper thực thi tool đồng bộ với timeout an toàn."""
    import concurrent.futures
    try:
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(fn, *args, **kwargs)
                return future.result(timeout=timeout_seconds)
        else:
            return asyncio.run(run_with_timeout_async(fn, *args, timeout_seconds=timeout_seconds, **kwargs))
    except (TimeoutError, concurrent.futures.TimeoutError) as exc:
        raise TimeoutError(f"Thực thi tool quá thời gian chờ ({timeout_seconds}s).") from exc


def is_configured() -> bool:
    return settings.db_configured


def _allowed_dbnames() -> set[str]:
    return {
        settings.db_name_its,
        settings.db_name_fence,
        settings.db_name_face,
        settings.db_name_fire,
        settings.db_name_anomaly,
    }


@contextmanager
def get_connection(dbname: str):
    """Context manager — 1 connection Postgres read-only, đóng khi xong.

    `dbname` PHẢI là 1 trong 5 DB đã khai báo (its/virtual_fence/smart_face/
    firesmoke/anomaly) — chặn ở code trước khi mở connection, không dựa hoàn
    toàn vào quyền Postgres của
    role `agent_readonly` (vốn cũng chặn SELECT ở DB khác, nhưng CONNECT vẫn
    qua — xem README mục "Tạo DB role read-only"). Lớp chặn thêm ở đây tránh
    lỗi gõ sai tên DB âm thầm mở connection tới nơi không định trước.

    Không dùng connection pool (psycopg2 pool) ở MVP này — traffic thấp, mỗi
    request 1-2 query ngắn; thêm pool sau nếu cần (đa người dùng, xem
    product-spec.md mục Out of Scope).
    """
    if dbname not in _allowed_dbnames():
        raise ValueError(f"dbname='{dbname}' không hợp lệ — chỉ chấp nhận {sorted(_allowed_dbnames())}.")

    from src.infra.resilience.breaker import get_sql_breaker

    sql_breaker = get_sql_breaker()
    if not sql_breaker.allow_request():
        raise RuntimeError("Dữ liệu tạm thời không khả dụng: Kết nối cơ sở dữ liệu đang gián đoạn (circuit breaker open).")

    import psycopg2

    conn = None
    try:
        tz = (settings.db_timezone or "Asia/Ho_Chi_Minh").strip().strip("'\"")
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            dbname=dbname,
            connect_timeout=5,
            options=f"-c timezone={tz}",
        )
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {int(settings.db_query_timeout_s * 1000)};")
            cur.execute("SET timezone = %s;", (tz,))
        yield conn
        sql_breaker.record_success()
    except Exception:
        sql_breaker.record_failure()
        raise
    finally:
        if conn is not None:
            conn.close()
