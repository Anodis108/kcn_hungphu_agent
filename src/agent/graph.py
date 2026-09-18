"""Graph Agent — ReAct function-calling trên plate_event/zone_event (Postgres).

    START → seed → agent ⇄ tools → pack → END

1 LLM call (ReAct, thường 1-2 vòng tool) để CHỌN tool + điền tham số — không
tự sinh SQL cho câu hỏi khớp tool (xem src/agent/tools.py).

pack() dựng câu trả lời TEMPLATE (liệt kê số liệu thô) trước, rồi gọi
src/agent/answer.py (LLM call thứ 2, tuỳ chọn qua ANSWER_USE_LLM) để diễn
giải thành câu tiếng Việt tự nhiên — template luôn là fallback khi tắt LLM,
offline, hoặc lời gọi lỗi.

Observability: `run_agent(..., parent_span=)` nhận span cha từ
`trace_answer` (main); agent/tools/pack tạo nested `chon_tool` /
`chay_tool` / `dien_giai`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel

from src.agent.answer import build_answer
from src.agent.react import all_tool_json, build_react_subgraph, fresh_user, parse_tool_output
from src.agent.tools import TOOLS, QueryResult
from src.monitoring.tracing import trace_step

from src.prompts import registry

__all__ = ["run_agent"]


class Agent_Input(BaseModel):
    question: str


class Agent_Output(BaseModel):
    question: str
    answer: str
    query: QueryResult | None = None
    detail: str = ""


class AgentState(TypedDict, total=False):
    question: str
    result: Agent_Output
    messages: Annotated[list, add_messages]
    _trace_span: Any


_TOOL_NAMES = {t.name for t in TOOLS}

# LLM không biết ngày giờ thật (chỉ có kiến thức huấn luyện tới 1 mốc quá
# khứ) — PHẢI tiêm ngày giờ hiện tại vào system prompt, nếu không model sẽ tự
# bịa ngày (đã quan sát thực tế ở atin/: model trả lời bằng ngày trong dữ
# liệu huấn luyện, ra ngoài khoảng dữ liệu thật -> luôn 0 dòng cho câu hỏi
# "hôm nay"). system_prompt PHẢI là callable (đánh giá lại mỗi lượt gọi),
# không phải string cố định build 1 lần lúc compile graph.
# System prompt template được quản lý động qua PromptRegistry (prompts/agent_system).


def _system_prompt() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return registry().render("agent_system", version="production", now=now)


def _seed(state: AgentState) -> dict:
    question = str(state.get("question") or "").strip()
    return fresh_user(f"Câu hỏi: {question}")


def _offline(state: AgentState) -> tuple[str, dict]:
    # Không API key / pytest: đi thẳng qua list_khu_vuc — không gọi OpenAI.
    return "list_khu_vuc", {}


def _template_answer(queries: list[QueryResult]) -> str:
    """Gộp câu trả lời từ 1+ QueryResult — agent có thể gọi NHIỀU tool song
    song trong 1 lượt (vd. count_vehicle_flow(MOTORCYCLE) + (CAR) cho câu hỏi
    hỏi nhiều loại xe cùng lúc); bỏ sót tool nào là mất dữ liệu thật trong
    câu trả lời, đã phát hiện qua test 5 câu hỏi mẫu — xem change-log."""
    errors = [q.error for q in queries if q.error]
    if errors and len(errors) == len(queries):
        return " ".join(errors)

    all_rows: list[tuple[list[str], list]] = []
    for q in queries:
        if q.error:
            continue
        for row in q.rows:
            all_rows.append((q.columns, row))

    if not all_rows:
        return "Không có dữ liệu khớp câu hỏi trong khoảng thời gian/điều kiện đã cho."
    if len(all_rows) == 1 and len(all_rows[0][0]) == 1:
        return f"Kết quả: {all_rows[0][1][0]}"
    lines = [", ".join(f"{c}={v}" for c, v in zip(cols, row)) for cols, row in all_rows[:20]]
    return f"Kết quả ({len(all_rows)} dòng):\n" + "\n".join(lines)


def _pack(state: AgentState) -> dict:
    question = str(state.get("question") or "")
    with trace_step(state.get("_trace_span"), "dien_giai", input=question) as t:
        raw_list = all_tool_json(state, _TOOL_NAMES)
        queries = [q for raw in raw_list if (q := parse_tool_output(raw, QueryResult)) is not None]
        if not queries:
            result = Agent_Output(
                question=question,
                answer="Chưa truy vấn được dữ liệu.",
                detail="không có kết quả tool",
            )
            t["output"] = {"answer": result.answer, "tools": []}
            return {"result": result}

        template = _template_answer(queries)
        answer = build_answer(question, queries, template)
        tools_used = ",".join(dict.fromkeys(q.tool for q in queries))
        result = Agent_Output(
            question=question,
            answer=answer,
            query=queries[-1],
            detail=f"tool: {tools_used}",
        )
        # Chỉ gắn câu trả lời ngắn + tên tool — không dump rows/secrets.
        t["output"] = {"answer": answer[:500], "tools": tools_used}
        return {"result": result}


@lru_cache(maxsize=1)
def _build_graph():
    graph = build_react_subgraph(
        AgentState,
        tools=TOOLS,
        system_prompt=_system_prompt,
        offline_call=_offline,
        seed_fn=_seed,
        pack_fn=_pack,
    )
    return graph.compile()


def run_agent(inp: Agent_Input, parent_span: Any = None) -> Agent_Output:
    """`parent_span`: span cha từ `trace_answer` (main). None = không trace con."""
    question = (inp.question or "").strip()
    return _build_graph().invoke({"question": question, "_trace_span": parent_span})["result"]


def save_graph_visualization(path: str = "graph.png") -> str:
    """Xuất sơ đồ graph ra file — hữu ích để debug/trình bày cấu trúc ReAct
    (seed → agent ⇄ tools → pack). Không phải business logic, chỉ dùng khi
    cần xem lại cấu trúc graph, không gọi trong luồng chạy app.

    Thử vẽ PNG trước (draw_mermaid_png — gọi API mermaid.ink, cần mạng). Nếu
    không có mạng/lỗi, fallback ghi ra Mermaid text thuần (.mmd, không cần
    mạng) — dán vào https://mermaid.live hoặc preview trực tiếp trong
    VSCode/GitHub.

    Returns:
        Đường dẫn file thực sự đã ghi (có thể khác `path` nếu fallback sang .mmd).
    """
    graph = _build_graph().get_graph()

    try:
        png_bytes = graph.draw_mermaid_png()
        with open(path, "wb") as f:
            f.write(png_bytes)
        return path
    except Exception:
        # Offline hoặc mermaid.ink không khả dụng — fallback text thuần, luôn thành công.
        mmd_path = path.rsplit(".", 1)[0] + ".mmd"
        with open(mmd_path, "w", encoding="utf-8") as f:
            f.write(graph.draw_mermaid())
        return mmd_path


if __name__ == "__main__":
    # python -m src.agent.graph
    print(save_graph_visualization("graph.png"))
