from __future__ import annotations

from datetime import date
from functools import lru_cache

from langgraph.graph import END

from app.agent_m2 import context, memory
from .states import AssistantState
from app.agent_m2.tool_selection import retrieve_relevant_tools
from app.config import settings

CORE_INSTRUCTIONS = (
    "Bạn chỉ thấy MỘT PHẦN tool phù hợp nhất với câu hỏi hiện tại, không phải "
    "toàn bộ tool hệ thống có. Với câu hỏi về một khoảng thời gian (vd: 'tuần "
    "này'), tự tính start_date/end_date rồi gọi check_calendar MỘT LẦN DUY "
    "NHẤT — không gọi lặp lại cho từng ngày riêng lẻ."
)


def _system_prompt() -> str:
    # Chèn ngày hiện tại — không có dòng này, model không biết "hôm nay" là
    # ngày nào nên hay bịa năm/tháng sai khi tính "tuần này"/"ngày mai".
    return (
        "Bạn là trợ lý cá nhân tiếng Việt, thân thiện và ngắn gọn. "
        f"Hôm nay là {date.today().isoformat()}. " + CORE_INSTRUCTIONS
    )
    
async def agent_node(state: AssistantState) -> dict:
    
    history = state.get("messages", [])