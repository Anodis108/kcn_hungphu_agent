"""LLM client — multi-backend (openai / ollama), key rotation, offline mode.

Ollama expose OpenAI-compatible API — chỉ đổi base_url + api_key giả, phần
gọi model (ChatOpenAI.bind_tools) không đổi. Đổi LLM_BACKEND trong .env là
đủ để chuyển từ OpenAI Cloud sang model local (4GB VRAM, vd. Ollama
qwen2.5:3b-instruct-q4_K_M) mà không sửa code.

Offline mode (không API key / đang pytest): agent tự giả 1 tool_call thay vì
gọi thật — module này không được gọi trong path đó.
"""

from __future__ import annotations

import os
import time
from collections import deque
from dataclasses import dataclass
from functools import lru_cache

from src.config import settings


@dataclass(frozen=True, slots=True)
class _Backend:
    default_base_url: str  # "" = mặc định OpenAI Cloud
    requires_real_key: bool
    dummy_key: str = "not-needed"


_BACKENDS: dict[str, _Backend] = {
    "openai": _Backend(default_base_url="", requires_real_key=True),
    "ollama": _Backend(default_base_url="http://localhost:11434/v1", requires_real_key=False, dummy_key="ollama"),
}


def _get_backend() -> _Backend:
    name = settings.llm_backend.strip().lower()
    if name not in _BACKENDS:
        raise ValueError(f"LLM_BACKEND='{name}' không hợp lệ — chọn: {', '.join(_BACKENDS)}.")
    return _BACKENDS[name]


class _RotatingKeyPool:
    """Round-robin nhiều API key, tự đưa key bị 429 vào cooldown."""

    def __init__(self, keys: list[str]):
        if not keys:
            raise ValueError("Cần ít nhất 1 OPENAI_API_KEYS khi LLM_BACKEND=openai.")
        self._keys = deque(keys)
        self._cooldown: dict[str, float] = {}

    def get_key(self) -> str:
        now = time.time()
        for _ in range(len(self._keys)):
            key = self._keys[0]
            self._keys.rotate(-1)
            if self._cooldown.get(key, 0.0) <= now:
                return key
        return self._keys[0]  # tất cả cooldown -> vẫn thử key đầu, để OpenAI SDK tự retry/raise

    def mark_limited(self, key: str, cooldown_seconds: float = 60.0) -> None:
        self._cooldown[key] = time.time() + cooldown_seconds


@lru_cache(maxsize=1)
def _pool() -> _RotatingKeyPool:
    return _RotatingKeyPool(settings.api_keys)


def use_offline_tools() -> bool:
    """Không key (khi backend=openai) hoặc đang pytest: agent giả 1 tool_call."""
    if bool(os.environ.get("PYTEST_CURRENT_TEST")):
        return True
    backend = _get_backend()
    return backend.requires_real_key and not settings.api_keys


def base_llm():
    from langchain_openai import ChatOpenAI

    backend = _get_backend()
    api_key = _pool().get_key() if backend.requires_real_key else backend.dummy_key
    base_url = settings.llm_base_url or backend.default_base_url or None

    kwargs: dict = {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "api_key": api_key,
        "max_retries": settings.llm_max_retries,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def invoke_with_tools(messages, tools=None):
    llm = base_llm()
    if tools:
        llm = llm.bind_tools(tools)
    return llm.invoke(messages)


def invoke_text(system_prompt: str, user_prompt: str) -> str:
    """Lời gọi LLM đơn giản không tool — dùng cho bước Answer (diễn giải số liệu)."""
    llm = base_llm()
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    return str(response.content or "")
