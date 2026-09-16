"""LLM client dùng chung cho 4 pattern multi-agent — Module II, Bài 6.

Tách riêng khỏi nodes.py (agent đơn, Bài 2-5) vì multi-agent không cần tool
retrieval (Bài 4) — mỗi agent con ở đây chỉ bind ĐÚNG tool của domain mình
(xem tools.py: TOOL_GROUPS), không phải chọn lọc qua embedding similarity.
"""

from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def base_llm():
    """Client chưa bind tool, cache 1 lần — giống app/agent_m2/nodes.py:_base_llm.

    Truyền thẳng api_key từ settings.api_keys[0] (không để ChatOpenAI tự đọc
    biến môi trường OPENAI_API_KEY số ít — repo dùng OPENAI_API_KEYS số nhiều).
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.api_keys[0] if settings.api_keys else None,
    )

async def _llm_with_tools(query: str, tools: list) -> object:
    """Bind LLM với top-k tool liên quan tới `query` (Bài 4, Section 2: Tool
    Retrieval) — KHÔNG bind cố định toàn bộ tool mỗi lượt, giảm token + tăng
    độ chính xác chọn tool (bài học: >20 tool độ chính xác giảm mạnh).

    async vì retrieve_relevant_tools cần await MCP client (Section 4) ở lần
    load tool đầu tiên (sau đó có cache, nhưng hàm vẫn giữ chữ ký async cho
    nhất quán — awaiting một future đã resolve gần như free)."""
    
    relevant = tools  
    # relevant = await retrieve_relevant_tools(query, k=settings.agent_tool_retrieval_k)
    return base_llm().bind_tools(relevant)