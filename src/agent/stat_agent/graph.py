from __future__ import annotations

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent_m2.nodes import (
    agent_node,
    compact_node,
    extract_and_store_node,
    recall_node,
    should_compact_route,
    should_continue,
)
from app.agent_m2.eval import evaluate_run
from app.agent_m2.state import AssistantState
from app.agent_m2.tools import TOOLS
from app.monitoring.tracing import trace_answer

def build_react_subgraph(state_cls, *, tools: list, system_prompt: str, offline_call, seed_fn, pack_fn):
    graph = StateGraph(state_cls)
    graph.add_node("seed", seed_fn)
    graph.add_node("agent", partial(agent_node, tools=tools, system_prompt=system_prompt, offline_call=offline_call))
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("pack", pack_fn)
    
    graph.add_edge(START, "seed")
    graph.add_edge("seed", "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "pack": "pack"})
    graph.add_edge("tools", "agent")
    graph.add_edge("pack", END)
    return graph
