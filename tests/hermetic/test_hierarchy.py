"""Hermetic hierarchy tests: skeleton AssistantState + root graph + subgraphs."""

from langgraph.checkpoint.memory import MemorySaver

from src.domain.agents.analytics.graph import build_analytics_graph
from src.domain.agents.graph import build_graph
from src.domain.agents.knowledge.graph import build_knowledge_graph
from src.domain.agents.state import AssistantState


# --- Sourced from test_v16_hierarchy_skeleton.py ---

def test_assistant_state_has_root_fields():
    keys = set(AssistantState.__annotations__)
    for k in ("question", "user_id", "session_id", "intent", "next_team", "final_answer"):
        assert k in keys


def test_build_graph_callable():
    g = build_graph(checkpointer=MemorySaver())
    assert g is not None


def test_root_graph_is_canonical():
    import src.domain.agents.graph as root
    import src.domain.agents.graph as vms

    assert root.build_graph is not None
    g1 = root.build_graph(checkpointer=MemorySaver())
    assert "guardrail_input" in g1.get_graph().nodes
    assert "top_supervisor" in g1.get_graph().nodes
    assert vms._build_graph is root._build_graph


def test_route_greeting_to_synth():
    from src.domain.agents.nodes import route_from_top

    assert route_from_top({"intent": "chat", "next_team": "synth"}) == "synth"


def test_route_multi_continues_to_team():
    from src.domain.agents.nodes import route_from_top

    assert route_from_top({"next_team": "analytics_team"}) == "analytics_team"


# --- Sourced from test_v16_analytics_subgraph.py ---

def test_analytics_graph_has_sql_nodes():
    g = build_analytics_graph()
    nodes = set(g.get_graph().nodes)
    for n in ("retrieve_schema", "generate_sql", "validate_sql", "repair_sql", "execute_sql"):
        assert n in nodes


# --- Sourced from test_v16_knowledge_subgraph.py ---

def test_knowledge_graph_nodes():
    nodes = set(build_knowledge_graph().get_graph().nodes)
    assert "retrieve_docs" in nodes
    assert "answer_from_docs" in nodes
