"""Cấu hình — đọc từ biến môi trường / file .env. Điểm DUY NHẤT đọc secrets."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── LLM backend ───────────────────────────────────────────────────────
    # "openai" = OpenAI Cloud | "ollama" = model local (4GB VRAM, vd. qwen2.5:3b-instruct)
    # Cả 2 nói OpenAI-compatible API — đổi backend chỉ cần sửa .env, không sửa code.
    llm_backend: str = Field(default="openai", alias="LLM_BACKEND")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    openai_api_keys: str = Field(default="", alias="OPENAI_API_KEYS")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")

    # Bước "Answer" (diễn giải số liệu -> câu tiếng Việt) có thể tắt để trả lời
    # tức thời bằng template dựng sẵn — hữu ích khi model local quá chậm.
    answer_use_llm: bool = Field(default=True, alias="ANSWER_USE_LLM")

    # ── Database nguồn thống kê (Postgres, read-only) ───────────────────────
    # Dùng role riêng CHỈ có quyền SELECT (xem README — mục "Tạo DB role read-only").
    db_host: str = Field(default="", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_name_its: str = Field(default="its", alias="DB_NAME_ITS")
    db_name_fence: str = Field(default="virtual_fence", alias="DB_NAME_FENCE")
    db_organization_id: int = Field(default=0, alias="DB_ORGANIZATION_ID")
    db_query_timeout_s: float = Field(default=5.0, alias="DB_QUERY_TIMEOUT_S")
    db_max_rows: int = Field(default=200, alias="DB_MAX_ROWS")

    # ── Guardrail output (giới hạn độ dài câu trả lời) ──────────────────────
    guardrails_min_answer_len: int = Field(default=5, alias="GUARDRAILS_MIN_ANSWER_LEN")
    guardrails_max_answer_len: int = Field(default=2000, alias="GUARDRAILS_MAX_ANSWER_LEN")

    @property
    def api_keys(self) -> list[str]:
        return [k.strip() for k in self.openai_api_keys.split(",") if k.strip()]

    @property
    def db_configured(self) -> bool:
        return bool(self.db_host and self.db_user)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
