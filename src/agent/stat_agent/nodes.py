from __future__ import annotations

from datetime import date
from functools import lru_cache

from langgraph.graph import END

from ..import context, memory
from .._llm import _llm_with_tools
from .states import StatState
from .tools import TOOLS

CORE_INSTRUCTIONS = (
    "Bạn chỉ thấy MỘT PHẦN tool phù hợp nhất với câu hỏi hiện tại, không phải "
    "toàn bộ tool hệ thống có. "
)


def _system_prompt() -> str:
    return (
        "Bạn là trợ lý cá nhân tiếng Việt, thân thiện và ngắn gọn. "
        + CORE_INSTRUCTIONS
    )
    
async def agent_node(state: StatState) -> dict:
    
    def _detect_repetition(state: StatState, window: int = 4) -> bool:
        """True nếu `window` tool call gần nhất giống hệt nhau — dấu hiệu agent bị kẹt."""
        recent_calls = [
            m.tool_calls[0]
            for m in state["messages"][-window:]
            if getattr(m, "tool_calls", None)
        ]
        if len(recent_calls) < window:
            return False
        return len({str(c) for c in recent_calls}) == 1
    
    def _latest_human_query(messages: list) -> str:
        """Tìm tin nhắn user gần nhất làm query cho tool retrieval.

        Giữa 1 vòng agent⇄tools, message cuối có thể là tool result (không phải
        câu hỏi) — nên phải quét ngược tìm đúng message role "human"/"user", không
        chỉ lấy messages[-1].
        """
        for m in reversed(messages):
            if context._role_of(m) in ("human", "user"):
                return context._text_of(m)
        return ""
    
    history = context.sliding_window(state["messages"])
    messages = [{"role": "system", "content": _system_prompt()}] + history

    if _detect_repetition(state):
        messages = messages + [
            {
                "role": "system",
                "content": "Bạn đang lặp lại cùng 1 hành động. Hãy thử cách tiếp cận hoàn toàn khác.",
            }
        ]

    messages = context.reinject_instructions(messages, CORE_INSTRUCTIONS)

    query = _latest_human_query(state["messages"])
    llm = await _llm_with_tools(query, tools=TOOLS)
    response = await llm.ainvoke(messages)
    return {"messages": [response]}

