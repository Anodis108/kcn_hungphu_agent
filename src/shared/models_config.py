"""Models configuration loader with multi-provider fallback support.

Reads config/models.yaml (or defaults to environment variables in settings).
Never stores secret strings directly — only environment variable references.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from src.shared.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config/models.yaml")


class ModelTarget(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    base_url_env: str = "LLM_BASE_URL"
    api_key_env: str = "OPENAI_API_KEYS"
    timeout: float = 15.0

    @property
    def base_url(self) -> str | None:
        if self.base_url_env:
            val = os.getenv(self.base_url_env, "").strip()
            if val:
                return val
        if self.provider == "self_hosted":
            return settings.model_base_url or None
        return settings.effective_base_url

    @property
    def api_key(self) -> str:
        if self.api_key_env:
            val = os.getenv(self.api_key_env, "").strip()
            if val:
                # Nếu là danh sách keys cách nhau bởi dấu phẩy
                return val.split(",")[0].strip()
        if self.provider == "self_hosted":
            return settings.model_api_key or "not-needed"
        return settings.api_keys[0] if settings.api_keys else "not-needed"


class ModelsConfig(BaseModel):
    primary: ModelTarget = Field(default_factory=ModelTarget)
    fallbacks: list[ModelTarget] = Field(default_factory=list)

    def all_targets(self) -> list[ModelTarget]:
        return [self.primary] + self.fallbacks


_cached_config: ModelsConfig | None = None


def get_default_models_config() -> ModelsConfig:
    """Fallback về cài đặt hiện tại trong settings/.env khi không có models.yaml."""
    primary = ModelTarget(
        provider=settings.llm_backend,
        model=settings.effective_model,
        base_url_env="LLM_BASE_URL" if settings.llm_backend == "openai" else "MODEL_BASE_URL",
        api_key_env="OPENAI_API_KEYS" if settings.llm_backend == "openai" else "MODEL_API_KEY",
        timeout=float(settings.llm_request_timeout_s or 15.0),
    )
    return ModelsConfig(primary=primary, fallbacks=[])


def load_models_config(config_path: Path | str | None = None) -> ModelsConfig:
    """Tải cấu hình models từ file YAML. Nếu file không tồn tại, trả về default từ settings."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_file():
        return get_default_models_config()

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            return get_default_models_config()
        return ModelsConfig.model_validate(raw)
    except Exception as exc:
        logger.warning("Lỗi đọc file models config tại %s (%s). Sử dụng cấu hình mặc định.", path, exc)
        return get_default_models_config()


def get_model_targets() -> list[ModelTarget]:
    """Danh sách các targets (primary + fallbacks) có thứ tự ưu tiên."""
    global _cached_config
    if _cached_config is None:
        _cached_config = load_models_config()
    return _cached_config.all_targets()


def reset_models_config_cache() -> None:
    global _cached_config
    _cached_config = None
