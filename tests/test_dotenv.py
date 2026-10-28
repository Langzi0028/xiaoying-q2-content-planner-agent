from __future__ import annotations

from content_planner.config import load_llm_config, load_project_dotenv


def test_project_dotenv_loads_gateway_configuration_when_environment_is_empty(
    tmp_path, monkeypatch
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "LLM_BASE_URL=https://proxy.example/v1",
                "LLM_API_KEY=dotenv-key",
                "LLM_MODEL=dotenv-model",
                "LLM_API_MODE=chat_completions",
            ]
        ),
        encoding="utf-8",
    )
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_API_MODE"):
        monkeypatch.delenv(name, raising=False)

    load_project_dotenv(dotenv_path)
    config = load_llm_config()

    assert config.is_configured is True
    assert config.base_url == "https://proxy.example/v1"
    assert config.model == "dotenv-model"
    assert config.mode == "chat_completions"


def test_process_environment_takes_precedence_over_project_dotenv(tmp_path, monkeypatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "LLM_MODEL=dotenv-model\nLLM_BASE_URL=https://proxy.example/v1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_MODEL", "pycharm-model")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    load_project_dotenv(dotenv_path)

    assert load_llm_config().model == "pycharm-model"
    assert load_llm_config().base_url == "https://proxy.example/v1"
