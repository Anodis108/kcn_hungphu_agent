"""Tests for Phase 19.4 (G1): config/models.yaml and provider fallback."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from src.infra.llm.completion import invoke_text, invoke_with_tools
from src.main import app
from src.shared.models_config import (
    DEFAULT_CONFIG_PATH,
    ModelsConfig,
    ModelTarget,
    load_models_config,
    reset_models_config_cache,
)


@pytest.fixture(autouse=True)
def reset_cache():
    reset_models_config_cache()
    yield
    reset_models_config_cache()


def test_models_yaml_contains_no_secrets():
    """Đảm bảo config/models.yaml không chứa chuỗi secret/API key thật (chỉ tên env)."""
    assert DEFAULT_CONFIG_PATH.is_file(), "config/models.yaml phải tồn tại"
    content = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")

    # Không chứa pattern khóa bí mật thật
    assert "sk-" not in content
    assert "ghp_" not in content
    assert "eyJ" not in content  # JWT tokens

    # Phải có primary và fallbacks
    assert "primary:" in content
    assert "fallbacks:" in content
    assert "base_url_env:" in content
    assert "api_key_env:" in content


def test_models_config_loader_missing_file_falls_back_to_env(tmp_path, monkeypatch):
    """Khi file models.yaml không tồn tại, loader dùng settings/env."""
    monkeypatch.setattr("src.shared.settings.settings.llm_backend", "openai")
    monkeypatch.setattr("src.shared.settings.settings.llm_model", "gpt-4o-mini")

    non_existent = tmp_path / "does_not_exist.yaml"
    cfg = load_models_config(non_existent)
    assert cfg.primary.provider == "openai"
    assert cfg.primary.model == "gpt-4o-mini"
    assert len(cfg.fallbacks) == 0


def test_models_fallback_on_primary_failure(caplog, monkeypatch):
    """Khi primary thất bại (connect/5xx/timeout), tự động gọi fallback và log llm_fallback_used."""
    test_cfg = ModelsConfig(
        primary=ModelTarget(provider="openai", model="primary-model"),
        fallbacks=[ModelTarget(provider="self_hosted", model="fallback-model")],
    )
    monkeypatch.setattr("src.shared.models_config.load_models_config", lambda *args, **kwargs: test_cfg)
    reset_models_config_cache()

    calls = []

    class FakeChatLLM:
        def __init__(self, model: str):
            self.model = model

        def invoke(self, messages, *args, **kwargs):
            calls.append(self.model)
            if self.model == "primary-model":
                raise RuntimeError("500 Internal Server Error: Primary model is down")
            res = MagicMock()
            res.content = "Answer from fallback model"
            res.response_metadata = {}
            res.usage_metadata = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
            return res

    def fake_base_llm(model_override=None, **kwargs):
        return FakeChatLLM(model=model_override)

    monkeypatch.setattr("src.infra.llm.completion.base_llm", fake_base_llm)

    with caplog.at_level(logging.WARNING):
        out = invoke_text(
            system_prompt="sys",
            user_prompt="user",
            substep=None,
        )
        assert out == "Answer from fallback model"
        assert calls == ["primary-model", "fallback-model"]
        assert "llm_fallback_used" in caplog.text
        assert "primary-model failed" in caplog.text


def test_api_models_endpoint_returns_supported_models():
    """Endpoint GET /api/models vẫn hoạt động ổn định và liệt kê các models từ config."""
    client = TestClient(app)
    resp = client.get("/api/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "supported_models" in data
    assert len(data["supported_models"]) >= 1
    # Chứa model từ primary/fallbacks
    model_ids = [m["id"] for m in data["supported_models"]]
    assert "gpt-4o-mini" in model_ids or any("Qwen" in mid for mid in model_ids)


def test_chat_stream_fallback_on_primary_failure(caplog, monkeypatch):
    """Khi primary thất bại trong chat_stream, tự động chuyển sang fallback và log llm_fallback_used."""
    from src.infra.llm.completion import chat_stream

    test_cfg = ModelsConfig(
        primary=ModelTarget(provider="openai", model="primary-stream-model"),
        fallbacks=[ModelTarget(provider="self_hosted", model="fallback-stream-model")],
    )
    monkeypatch.setattr("src.shared.models_config.load_models_config", lambda *args, **kwargs: test_cfg)
    reset_models_config_cache()

    calls = []

    class FakeChunk:
        def __init__(self, content):
            self.content = content

    class FakeChatLLM:
        def __init__(self, model: str):
            self.model = model

        def stream(self, messages, *args, **kwargs):
            calls.append(self.model)
            if self.model == "primary-stream-model":
                raise RuntimeError("503 Service Unavailable: Stream endpoint down")
            yield FakeChunk("Token 1 ")
            yield FakeChunk("Token 2")

    def fake_base_llm(model_override=None, **kwargs):
        return FakeChatLLM(model=model_override)

    monkeypatch.setattr("src.infra.llm.completion.base_llm", fake_base_llm)

    with caplog.at_level(logging.WARNING):
        stream = chat_stream(
            system_prompt="sys",
            user_prompt="user",
        )
        tokens = list(stream)
        assert tokens == ["Token 1 ", "Token 2"]
        assert calls == ["primary-stream-model", "fallback-stream-model"]
        assert "llm_fallback_used" in caplog.text
        assert "primary-stream-model failed" in caplog.text

