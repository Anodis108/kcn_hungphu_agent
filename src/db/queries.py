"""Các câu SQL tham số hoá — mỗi hàm ứng với 1 tool trong src/agent/tools.py
(Phase 4).

Toàn bộ dùng placeholder %s (psycopg2 tự escape) — không nối chuỗi giá trị
người dùng vào SQL. Model chỉ chọn tool + điền tham số, KHÔNG tự sinh SQL cho
các câu hỏi khớp tool (an toàn + chính xác hơn Text-to-SQL tự do với model
nhỏ — xem README). Tool SQL fallback (Phase 4) sẽ có validate chặt riêng,
cho câu hỏi không khớp tool nào.

Aggregate CHẠY TRỰC TIẾP trên bảng raw (plate_event/zone_event), KHÔNG dùng
materialized view `plate_dashboard.pd_*` — job aggregate của mart đó đã
ngừng cập nhật (dừng ở 2026-09-07, raw data vẫn tiếp tục tới hiện tại) nên
mart không đáng tin. Nếu team backend sửa lại job aggregate, cân nhắc đọc
`pd_flow_daily`/`pd_vehicle_mix` cho khoảng thời gian dài (nhiều tháng) để
nhanh hơn — raw table vẫn ổn ở volume hiện tại nhờ index theo event_time.
"""

from __future__ import annotations

from src.config import settings
from src.db.connection import get_connection

_VEHICLE_TYPES = {"BUS", "CAR", "MOTORCYCLE", "TRUCK"}
_DIRECTIONS = {"IN", "OUT"}


def _org_filter() -> tuple[str, tuple]:
    if settings.db_organization_id:
        return "organization_id = %s", (settings.db_organization_id,)
    return "1=1", ()


_GROUP_COLUMNS = {
    "vehicle_type": "vehicle_type",
    "direction": "direction",
    "manufacturer": "manufacturer",
}


def count_vehicle_flow(
    date_from: str,
    date_to: str,
    direction: str | None,
    vehicle_type: str | None,
    group_by: str = "vehicle_type,direction",
) -> dict:
    """Đếm lượt xe ra/vào theo khoảng thời gian, group theo 1+ cột trong
    {vehicle_type, direction, manufacturer} (mặc định vehicle_type,direction).
    group_by="manufacturer" trả lượt xe theo hãng — nên kèm vehicle_type=CAR
    vì hãng xe chỉ có ý nghĩa với ô tô.

    GIỚI HẠN SCHEMA: vehicle_type chỉ có 4 giá trị (BUS/CAR/MOTORCYCLE/TRUCK)
    — DB KHÔNG phân loại ô tô theo số chỗ ngồi (5/7/9/16/29/40 chỗ). Câu hỏi
    kiểu "bao nhiêu xe 7 chỗ" không trả lời chính xác được bằng dữ liệu hiện
    có; Answer (Phase 4) cần nêu rõ giới hạn này thay vì bịa số theo số chỗ."""
    group_cols = [c.strip() for c in group_by.split(",") if c.strip()]
    invalid = [c for c in group_cols if c not in _GROUP_COLUMNS]
    if invalid or not group_cols:
        return {"error": f"group_by chỉ nhận {sorted(_GROUP_COLUMNS)}, nhận '{group_by}'."}

    org_sql, org_params = _org_filter()
    clauses = [org_sql, "event_time >= %s", "event_time < %s"]
    params: list = list(org_params) + [date_from, date_to]

    if direction:
        d = direction.strip().upper()
        if d not in _DIRECTIONS:
            return {"error": f"direction phải là IN/OUT, nhận '{direction}'."}
        clauses.append("direction = %s")
        params.append(d)

    if vehicle_type:
        v = vehicle_type.strip().upper()
        if v not in _VEHICLE_TYPES:
            return {"error": f"vehicle_type phải thuộc {sorted(_VEHICLE_TYPES)}, nhận '{vehicle_type}'."}
        clauses.append("vehicle_type = %s")
        params.append(v)

    if "manufacturer" in group_cols:
        clauses.append("manufacturer IS NOT NULL")

    select_cols = ", ".join(group_cols)
    sql = f"""
        SELECT {select_cols}, count(*) AS so_luot
        FROM plate_event
        WHERE {" AND ".join(clauses)}
        GROUP BY {select_cols}
        ORDER BY so_luot DESC
        LIMIT {settings.db_max_rows};
    """
    with get_connection(settings.db_name_its) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {
        "columns": [*group_cols, "so_luot"],
        "rows": [list(r) for r in rows],
        "row_count": len(rows),
    }


def trace_plate(plate_text: str, date_from: str | None, date_to: str | None) -> dict:
    """Lịch sử di chuyển (camera, thời điểm, chiều ra/vào) của 1 biển số."""
    if not plate_text or not plate_text.strip():
        return {"error": "Thiếu plate_text."}
    normalized = "".join(ch for ch in plate_text.upper() if ch.isalnum())

    org_sql, org_params = _org_filter()
    clauses = [org_sql, "normalized_license_plate = %s"]
    params: list = list(org_params) + [normalized]

    if date_from:
        clauses.append("event_time >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("event_time < %s")
        params.append(date_to)

    sql = f"""
        SELECT event_time, camera_code, camera_name, direction, vehicle_type
        FROM plate_event
        WHERE {" AND ".join(clauses)}
        ORDER BY event_time DESC
        LIMIT {settings.db_max_rows};
    """
    with get_connection(settings.db_name_its) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {
        "columns": ["event_time", "camera_code", "camera_name", "direction", "vehicle_type"],
        "rows": [[str(v) for v in r] for r in rows],
        "row_count": len(rows),
    }


def zone_intrusion_by_hour(date_from: str, date_to: str, zone_code: str | None = None) -> dict:
    """Số lượt xâm nhập khu vực hàng rào ảo, theo từng giờ — tìm khung giờ nhiều nhất."""
    org_sql, org_params = _org_filter()
    clauses = [org_sql, "event_time >= %s", "event_time < %s"]
    params: list = list(org_params) + [date_from, date_to]

    if zone_code:
        clauses.append("zone_name_cached = %s")
        params.append(zone_code)

    sql = f"""
        SELECT date_trunc('hour', event_time) AS gio, count(*) AS so_luot
        FROM zone_event
        WHERE {" AND ".join(clauses)}
        GROUP BY 1
        ORDER BY so_luot DESC
        LIMIT {settings.db_max_rows};
    """
    with get_connection(settings.db_name_fence) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {
        "columns": ["gio", "so_luot"],
        "rows": [[str(v) for v in r] for r in rows],
        "row_count": len(rows),
    }


def list_zones() -> dict:
    """Liệt kê camera/khu vực hợp lệ — tránh agent đoán sai giá trị lọc."""
    its_sql = "SELECT DISTINCT camera_code, camera_name FROM plate_event ORDER BY 1;"
    fence_sql = "SELECT DISTINCT zone_name_cached, camera_name FROM zone_event ORDER BY 1;"

    with get_connection(settings.db_name_its) as conn, conn.cursor() as cur:
        cur.execute(its_sql)
        its_rows = cur.fetchall()
    with get_connection(settings.db_name_fence) as conn, conn.cursor() as cur:
        cur.execute(fence_sql)
        fence_rows = cur.fetchall()

    return {
        "camera_its": [list(r) for r in its_rows],
        "khu_vuc_hang_rao": [list(r) for r in fence_rows],
    }
