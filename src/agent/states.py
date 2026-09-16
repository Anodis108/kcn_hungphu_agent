from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AssistantState(TypedDict, total=False):
    """State xuyên suốt ReAct loop: agent ⇄ tools.

    `Annotated[list, add_messages]` — reducer tự APPEND message mới thay vì
    ghi đè, giữ lịch sử hội thoại qua nhiều vòng agent → tools → agent.

    total=False: `user_id` optional để giữ tương thích ngược với Bài 2 (các
    lời gọi cũ chỉ truyền messages vẫn chạy — recall/store bỏ qua nếu thiếu).
    """

    messages: Annotated[list, add_messages]
    user_id: str  