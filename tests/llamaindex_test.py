from pathlib import Path

import pytest  # type: ignore
from dotenv import dotenv_values

from ddlh.rag.llamaindex import get_llamaindex_instance

ENV_EXAMPLE = Path(__file__).parent.parent / "env.example"


class TestLlamaIndexConfig:

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        for name, value in dotenv_values(ENV_EXAMPLE).items():
            monkeypatch.setenv(name, value or "")

    def test_env_example_uses_the_current_mistral_small_model(self):
        """
        env.example configures the -latest Mistral Small alias
        """
        config = get_llamaindex_instance().config
        assert config.llm_model_name == "mistral-small-latest"

    def test_guardrails_are_enabled_by_env_example(self):
        """
        With env.example's settings, Mistral's safe_prompt guardrails are on
        """
        assert get_llamaindex_instance().config.safe_prompt is True

    def test_env_example_variable_disables_guardrails(self, monkeypatch):
        """
        The guardrails flag named in env.example is the one the app reads
        """
        names = dotenv_values(ENV_EXAMPLE).keys()
        flag = next(name for name in names if "GUARDRAILS" in name)
        monkeypatch.setenv(flag, "1")
        assert get_llamaindex_instance().config.safe_prompt is False
