"""Deep-link UI Navigation — Whitelist paths & query builder (Phase 19.8).

Cung cấp khả năng điều hướng deep-link từ structured plan / bộ lọc truy vấn
sang các màn hình chức năng của hệ thống VMS (vd. /dashboard/traffic, /devices, ...).
Mọi path lạ ngoài whitelist đều bị loại bỏ để đảm bảo an toàn.
"""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any
import urllib.parse

import yaml

logger = logging.getLogger(__name__)

# Root dự án
_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_PATH = _ROOT / "config" / "ui_navigate.yaml"

# Danh sách path mặc định được duyệt
DEFAULT_WHITELIST_PATHS: set[str] = {
    "/dashboard",
    "/dashboard/traffic",
    "/devices",
    "/monitoring",
    "/playback",
    "/map",
    "/events",
    "/security/alerts",
    "/security/intrusion",
    "/zones",
    "/reports",
}


def normalize_path(path: str) -> str:
    """Chuẩn hóa đường dẫn: thêm '/' ở đầu, bỏ '/' dư thừa ở cuối, viết thường."""
    if not path or not isinstance(path, str):
        return ""
    p = path.strip()
    if not p:
        return ""
    if not p.startswith("/"):
        p = "/" + p
    p = p.rstrip("/")
    return p if p else "/"


def load_whitelist_paths(config_path: Path | str | None = None) -> set[str]:
    """Đọc danh sách whitelist từ file cấu hình config/ui_navigate.yaml.
    
    Nếu file không tồn tại hoặc lỗi, fallback về DEFAULT_WHITELIST_PATHS.
    """
    cfg = Path(config_path) if config_path else _CONFIG_PATH
    if not cfg.exists():
        return set(DEFAULT_WHITELIST_PATHS)

    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "whitelist_paths" in data:
            paths = set()
            for p in data["whitelist_paths"]:
                norm = normalize_path(str(p))
                if norm:
                    paths.add(norm)
            return paths or set(DEFAULT_WHITELIST_PATHS)
    except Exception as exc:
        logger.warning("Không thể đọc whitelist từ %s: %s, dùng danh sách mặc định", cfg, exc)

    return set(DEFAULT_WHITELIST_PATHS)


def is_whitelisted_path(path: str, whitelist: set[str] | None = None) -> bool:
    """Kiểm tra một đường dẫn có nằm trong whitelist hay không."""
    if not path:
        return False
    norm = normalize_path(path)
    allowed = whitelist if whitelist is not None else load_whitelist_paths()
    return norm in allowed


def build_query_string(filters: dict[str, Any] | None) -> str:
    """Chuyển đổi dictionary bộ lọc thành chuỗi query parameters URL-encoded.
    
    - Loại bỏ các giá trị None, rỗng hoặc khoảng trắng.
    - Sắp xếp key để đảm bảo tính nhất quán (deterministic).
    - Mã hóa an toàn ký tự đặc biệt / tiếng Việt bằng urllib.parse.urlencode.
    """
    if not filters or not isinstance(filters, dict):
        return ""

    clean_params: list[tuple[str, str]] = []
    for k in sorted(filters.keys()):
        val = filters[k]
        if val is None:
            continue
        if isinstance(val, (list, tuple, set)):
            for item in sorted(str(x) for x in val if x is not None):
                s = str(item).strip()
                if s:
                    clean_params.append((str(k), s))
        else:
            s = str(val).strip()
            if s:
                clean_params.append((str(k), s))

    if not clean_params:
        return ""

    return urllib.parse.urlencode(clean_params)


def build_ui_navigate(
    path: str,
    filters: dict[str, Any] | None = None,
    whitelist: set[str] | None = None,
) -> dict[str, str] | None:
    """Tạo đối tượng ui_navigate {path, query}.
    
    Nếu path không nằm trong whitelist, trả về None (path ngoài whitelist → bỏ).
    """
    norm = normalize_path(path)
    if not is_whitelisted_path(norm, whitelist=whitelist):
        logger.info("Path %s không nằm trong whitelist -> bỏ ui_navigate", path)
        return None

    query = build_query_string(filters)
    return {"path": norm, "query": query}


def extract_filters_from_question_or_state(
    question: str, state: dict[str, Any] | None = None
) -> tuple[str | None, dict[str, Any]]:
    """Trích xuất đường dẫn dự kiến và bộ lọc (date range, area, device, plate...)
    từ câu hỏi và state hiện tại.
    """
    filters: dict[str, Any] = {}
    path: str | None = None
    q = (question or "").lower()

    # 1. Trích xuất khoảng ngày tháng (vd: 04/09/2026 đến 16/09/2026, hoặc YYYY-MM-DD)
    date_matches = re.findall(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", question or "")
    if len(date_matches) >= 2:
        filters["start_date"] = date_matches[0]
        filters["end_date"] = date_matches[1]
    elif len(date_matches) == 1:
        filters["date"] = date_matches[0]
    elif "hôm nay" in q:
        filters["date_range"] = "today"
    elif "hôm qua" in q:
        filters["date_range"] = "yesterday"

    # 2. Trích xuất biển số xe nếu có (vd: 15K40139, 29A-12345)
    plate_match = re.search(r"\b([0-9]{2}[A-Z][0-9A-Z]?[-\s]?[0-9]{4,5})\b", question or "", re.IGNORECASE)
    if plate_match:
        filters["plate"] = plate_match.group(1).replace(" ", "").replace("-", "")

    # 3. Trích xuất loại phương tiện
    if any(k in q for k in ("xe máy", "motorcycle", "hai bánh")):
        filters["vehicle_type"] = "MOTORCYCLE"
    elif any(k in q for k in ("ô tô", "car", "xe con")):
        filters["vehicle_type"] = "CAR"
    elif any(k in q for k in ("xe tải", "truck")):
        filters["vehicle_type"] = "TRUCK"
    elif any(k in q for k in ("xe buýt", "xe bus", "bus")):
        filters["vehicle_type"] = "BUS"

    # 4. Trích xuất chiều ra/vào
    if "xe vào" in q or "lượt vào" in q or "vào cổng" in q:
        filters["direction"] = "IN"
    elif "xe ra" in q or "lượt ra" in q or "ra cổng" in q:
        filters["direction"] = "OUT"

    # 5. Trích xuất khu vực / cổng / zone
    area_match = re.search(r"(cổng\s+\d+|khu\s+vực\s+[A-Za-z0-9_]+|kcn\s+[^\s,]+)", q)
    if area_match:
        filters["area"] = area_match.group(1).strip()

    # 6. Trích xuất camera / device ID
    dev_match = re.search(r"(cam(?:era)?[\s_]+[A-Za-z0-9_-]+|device[\s_]+[A-Za-z0-9_-]+)", q)
    if dev_match:
        filters["device"] = dev_match.group(1).strip()

    # Xác định path mục tiêu theo nghiệp vụ
    if any(k in q for k in ("devices", "quản lý camera", "thêm camera", "trang thiết bị", "trạng thái camera", "cloud cam")):
        path = "/devices"
    elif any(k in q for k in ("lưu lượng", "xe vào", "xe ra", "biển số", "lịch sử di chuyển", "phương tiện", "ô tô", "xe máy", "hãng xe")):
        path = "/dashboard/traffic"
    elif any(k in q for k in ("xâm nhập", "leo trèo", "vùng cấm", "an ninh")):
        path = "/security/intrusion"
    elif any(k in q for k in ("cháy", "khói", "báo động", "ẩu đả", "khuôn mặt", "nhận diện")):
        path = "/security/alerts"
    elif any(k in q for k in ("dashboard", "tổng quan")):
        path = "/dashboard"

    return path, filters


def resolve_ui_navigate(
    question: str,
    state: dict[str, Any] | None = None,
    whitelist: set[str] | None = None,
) -> dict[str, str] | None:
    """Tự động phân giải và sinh đối tượng ui_navigate cho câu hỏi / state hiện tại.
    
    Nếu đã có sẵn ui_navigate trong state, ưu tiên sử dụng sau khi kiểm tra whitelist.
    Nếu chưa có, suy luận từ câu hỏi và bộ lọc.
    Trả về None nếu không có điều hướng hoặc path ngoài whitelist.
    """
    # 1. Kiểm tra nếu trong state đã có khai báo ui_navigate sẵn
    if state and isinstance(state, dict):
        existing_nav = state.get("ui_navigate")
        if isinstance(existing_nav, dict) and "path" in existing_nav:
            return build_ui_navigate(
                existing_nav["path"],
                filters=existing_nav.get("filters") or existing_nav.get("query_params"),
                whitelist=whitelist,
            )

    # 2. Suy luận từ question & state
    path, filters = extract_filters_from_question_or_state(question, state)
    if not path:
        return None

    return build_ui_navigate(path, filters, whitelist=whitelist)
