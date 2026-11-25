"""Hermetic trace tests: trace payload formatting, redaction, and trace sampling."""

from contextlib import contextmanager
import pytest
from src.domain.observability.redaction import redact_text
from src.domain.observability.tracing import _get_langfuse, llm_io_payload, slim_state
from src.shared.settings import Settings, settings


# --- Sourced from test_trace_payload.py ---

def test_redact_masks_sk_and_bearer():
    s = redact_text("Bearer SECRETTOKEN123 and sk-abcdef0123456789xyz")
    assert "SECRETTOKEN123" not in s
    assert "sk-abcdef0123456789xyz" not in s
    assert "Bearer" in s or "***" in s


def test_redact_truncates():
    s = redact_text("x" * 100, max_chars=20)
    assert s.endswith("…[truncated]")
    assert len(s) < 40


def test_slim_state_drops_heavy_fields():
    snap = slim_state({
        "question": "q",
        "intent": "query_data",
        "sql": "SELECT 1",
        "error": "",
        "repair_count": 0,
        "rows": [{"a": 1}],
        "events": [{"node_id": "x"}],
        "chart_png_base64": "aaa",
        "messages": [],
        "schema_excerpt": "CREATE TABLE...",
        "orchestrator_step_index": 1,
        "respond_mode": "stat",
        "selected_tables": ["plate_event"],
    })
    assert snap["question"] == "q"
    assert snap["row_count"] == 1
    assert "rows" not in snap
    assert "events" not in snap
    assert "chart_png_base64" not in snap
    assert "schema_excerpt" not in snap


def test_llm_io_payload_has_full_text_not_lens():
    p = llm_io_payload("sys", "usr", "out")
    assert p["input"]["system"] == "sys"
    assert p["input"]["user"] == "usr"
    assert p["output"]["text"] == "out"
    assert "system_len" not in p["input"]


def test_invoke_text_traces_full_prompts(monkeypatch):
    captured: dict = {}

    class _FakeResp:
        content = "hello"
        response_metadata = {}

    class _FakeLlm:
        def invoke(self, _messages):
            return _FakeResp()

    import src.infra.llm.completion as completion_mod
    import src.domain.observability.tracing as tracing_mod

    monkeypatch.setattr(completion_mod, "base_llm", lambda **_kw: _FakeLlm())

    @contextmanager
    def _fake_trace_step(_parent, _name, input=None, metadata=None, as_type="span"):
        box: dict = {"_span": object(), "input": input, "metadata": dict(metadata or {})}
        captured["start_input"] = input
        yield box
        captured["box"] = box

    monkeypatch.setattr(tracing_mod, "trace_step", _fake_trace_step)
    monkeypatch.setattr(tracing_mod, "current_span", lambda: object())
    monkeypatch.setattr(tracing_mod, "extract_token_usage", lambda _r: {})
    monkeypatch.setattr(tracing_mod, "add_request_tokens", lambda _u: None)
    text = completion_mod.invoke_text("sys-prompt", "user-prompt", substep="llm_text")
    assert text == "hello"
    assert "system_len" not in captured["start_input"]
    assert captured["start_input"]["system"] == "sys-prompt"
    assert captured["box"]["output"]["text"] == "hello"


# --- Sourced from test_trace_sampling.py ---

def test_trace_sample_rate_default():
    s = Settings()
    assert s.trace_sample_rate == 1.0


def test_trace_sample_rate_zero():
    s = Settings(TRACE_SAMPLE_RATE=0.0)
    assert s.trace_sample_rate == 0.0

    s_str = Settings(TRACE_SAMPLE_RATE="0")
    assert s_str.trace_sample_rate == 0.0


def test_trace_sample_rate_fractional():
    s = Settings(TRACE_SAMPLE_RATE="0.45")
    assert s.trace_sample_rate == 0.45


def test_trace_sample_rate_out_of_bounds_warns_and_defaults():
    with pytest.warns(UserWarning, match="out of range"):
        s_high = Settings(TRACE_SAMPLE_RATE="1.5")
    assert s_high.trace_sample_rate == 1.0

    with pytest.warns(UserWarning, match="out of range"):
        s_low = Settings(TRACE_SAMPLE_RATE="-0.2")
    assert s_low.trace_sample_rate == 1.0


def test_trace_sample_rate_invalid_string_warns_and_defaults():
    with pytest.warns(UserWarning, match="Invalid TRACE_SAMPLE_RATE"):
        s = Settings(TRACE_SAMPLE_RATE="not_a_number")
    assert s.trace_sample_rate == 1.0


def test_get_langfuse_passes_sample_rate(monkeypatch):
    captured: dict = {}

    class FakeLangfuse:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    import langfuse

    monkeypatch.setattr(langfuse, "Langfuse", FakeLangfuse)

    # Test default
    monkeypatch.setattr(settings, "trace_sample_rate", 1.0)
    _get_langfuse()
    assert captured.get("sample_rate") == 1.0

    # Test custom rate (e.g. 0.0)
    monkeypatch.setattr(settings, "trace_sample_rate", 0.0)
    _get_langfuse()
    assert captured.get("sample_rate") == 0.0

    # Test custom rate (e.g. 0.25)
    monkeypatch.setattr(settings, "trace_sample_rate", 0.25)
    _get_langfuse()
    assert captured.get("sample_rate") == 0.25
