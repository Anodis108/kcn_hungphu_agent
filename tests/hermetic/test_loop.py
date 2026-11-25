"""Tests for Phase 19.3 (G5/G8): Loop protection, recursion_limit, SUPERVISOR_MAX_HOPS."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from langgraph.errors import GraphRecursionError
from src.application.agent_turn import AgentTurnService, TurnInput
from src.api.models.schemas import ChatRequest
from src.domain.agents.graph import _prepare_turn, Agent_Input, Agent_Output
from src.domain.agents.nodes.supervisor import (
    SUPERVISOR_MAX_HOPS,
    orchestrator_node,
    route_orchestrator,
)
from src.domain.agents.state import AgentState
from src.domain.authz.access_context import AccessContext
from src.infra.llm.schemas import OrchestratorPlan, OrchestratorStep
from src.shared.settings import settings


def test_prepare_turn_sets_recursion_limit(monkeypatch):
    """Config truyền cho graph phải chứa recursion_limit từ settings."""
    monkeypatch.setattr("src.shared.settings.settings.graph_recursion_limit", 30)
    inp = Agent_Input(question="Test question")
    _, _, config, _, _ = _prepare_turn(inp, "sess_1", "user_1", None)
    assert config["recursion_limit"] == 30


def test_supervisor_max_hops_stops_infinite_loop():
    """Khi iteration_count vượt SUPERVISOR_MAX_HOPS (6), route_orchestrator route sang 'respond'."""
    plan = OrchestratorPlan(
        steps=[
            OrchestratorStep(agent="query_data", sub_question="step 1"),
            OrchestratorStep(agent="query_data", sub_question="step 2"),
        ],
        is_multi=True,
    )

    # Dưới giới hạn hops
    state_below: AgentState = {
        "iteration_count": 3,
        "orchestrator_multi_active": True,
        "orchestrator_plan": plan,
        "orchestrator_step_index": 0,
    }
    assert route_orchestrator(state_below) == "query_data"

    # Vượt giới hạn hops (> 6)
    state_exceeded: AgentState = {
        "iteration_count": 7,
        "orchestrator_multi_active": True,
        "orchestrator_plan": plan,
        "orchestrator_step_index": 0,
    }
    assert route_orchestrator(state_exceeded) == "respond"


def test_orchestrator_node_increments_iteration_count():
    """Mỗi lần qua orchestrator_node (supervisor), iteration_count tăng 1."""
    state: AgentState = {
        "question": "Hôm nay có sự kiện gì?",
        "iteration_count": 2,
    }
    with patch("src.domain.agents.nodes.plan.is_multi_question", return_value=False):
        out = orchestrator_node(state)
        assert out.get("iteration_count") == 3
        # Event meta cũng mang iteration_count
        assert out["events"][0]["meta"]["iteration_count"] == 3


def test_agent_turn_process_catches_graph_recursion_error(monkeypatch):
    """AgentTurnService.process bắt GraphRecursionError và trả về câu trả lời thân thiện, không 500."""
    svc = AgentTurnService()

    def fake_run_agent(*args, **kwargs):
        raise GraphRecursionError("Recursion limit of 25 reached without hitting a stop condition.")

    monkeypatch.setattr("src.main.run_agent", fake_run_agent)

    inp = TurnInput(question="Câu hỏi quá phức tạp gây lặp")
    res = svc.process(inp)
    assert "Yêu cầu quá phức tạp" in res.answer or "recursion limit" in res.answer.lower()
    assert res.detail.get("status") == "error"


def test_agent_turn_stream_catches_graph_recursion_error(monkeypatch):
    """AgentTurnService.stream_sse_frames xử lý GraphRecursionError thành message lỗi thân thiện."""
    svc = AgentTurnService()

    def fake_stream(*args, **kwargs):
        raise GraphRecursionError("Recursion limit of 25 reached")

    monkeypatch.setattr("src.main.run_agent_stream", fake_stream)

    req = ChatRequest(
        question="Lặp vô tận",
        session_id="sess_loop",
        user_id="user_loop",
    )
    access = AccessContext(user_id="user_loop", effective_org_id=1, role_group="ALL")

    events = list(svc.stream_sse_frames(req, access=access, user_id="user_loop"))
    assert len(events) > 0
    full_output = "".join(events)
    assert "Yêu cầu quá phức tạp" in full_output or "recursion limit" in full_output.lower()


def test_supervisor_hops_recorded_in_events_and_metadata():
    """respond_node ghi supervisor_hops vào event meta."""
    from src.domain.agents.nodes.respond import respond_node

    state: AgentState = {
        "question": "Xin chào",
        "original_question": "Xin chào",
        "respond_mode": "inline",
        "answer": "Xin chào bạn!",
        "iteration_count": 4,
    }
    out = respond_node(state)
    assert out["result"].answer == "Xin chào bạn!"
    assert out["events"][0]["meta"]["supervisor_hops"] == 4
