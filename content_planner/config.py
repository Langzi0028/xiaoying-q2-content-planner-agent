"""Configuration for OpenAI-compatible LangChain model gateways."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class LLMConfig:
    base_url: str | None
    api_key: str | None
    model: str | None
    api_mode: str = "responses"

    def __post_init__(self) -> None:
        if self.api_mode not in {"responses", "chat_completions", "fallback"}:
            raise ValueError(
                "LLM_API_MODE must be responses, chat_completions, or fallback"
            )

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    @property
    def mode(self) -> str:
        """Expose the active request mode used in audit output."""
        return self.api_mode


def load_project_dotenv(dotenv_path: Path | str | None = None) -> bool:
    """Load a root .env file without replacing IDE or shell environment variables."""
    path = Path(dotenv_path) if dotenv_path is not None else PROJECT_ROOT / ".env"
    return load_dotenv(dotenv_path=path, override=False)


def load_llm_config(environ: Mapping[str, str] | None = None) -> LLMConfig:
    """Read gateway configuration without logging or persisting the secret."""
    if environ is None:
        load_project_dotenv()
    source = os.environ if environ is None else environ
    configured = all(
        source.get(name) for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")
    )
    return LLMConfig(
        base_url=source.get("LLM_BASE_URL"),
        api_key=source.get("LLM_API_KEY"),
        model=source.get("LLM_MODEL"),
        api_mode=source.get("LLM_API_MODE", "responses") if configured else "fallback",
    )
