"""Configuration for LLM and MCP connection."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_env(key: str, default: str) -> str:
    return os.getenv(f"MINIPS_{key}", default)


@dataclass(frozen=True)
class Settings:
    llm_base_url: str = _get_env("LLM_BASE_URL", "http://localhost:8080/v1")
    llm_api_key: str = _get_env("LLM_API_KEY", "local")
    llm_model: str = _get_env("LLM_MODEL", "qwen2.5-7b-instruct")
    mcp_url: str = _get_env("MCP_URL", "http://localhost:3000/sse")
    max_steps: int = int(_get_env("MAX_STEPS", "10"))
    request_timeout: float = float(_get_env("REQUEST_TIMEOUT", "60"))


def get_settings() -> Settings:
    return Settings(
        llm_base_url=_get_env("LLM_BASE_URL", "http://localhost:8080/v1"),
        llm_api_key=_get_env("LLM_API_KEY", "local"),
        llm_model=_get_env("LLM_MODEL", "qwen2.5-7b-instruct"),
        mcp_url=_get_env("MCP_URL", "http://localhost:3000/sse"),
        max_steps=int(_get_env("MAX_STEPS", "10")),
        request_timeout=float(_get_env("REQUEST_TIMEOUT", "60")),
    )
