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


class TestMistralEndpoint:

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        for name, value in dotenv_values(ENV_EXAMPLE).items():
            monkeypatch.setenv(name, value or "")

    def test_it_defaults_to_the_eu_endpoint(self, monkeypatch):
        """
        Without MISTRAL_API_ENDPOINT, requests go to Mistral's EU endpoint
        """
        monkeypatch.delenv("MISTRAL_API_ENDPOINT")
        config = get_llamaindex_instance().config
        assert config.mistral_endpoint == "https://api.eu.mistral.ai"

    def test_env_example_uses_the_eu_endpoint(self):
        """
        env.example configures Mistral's EU endpoint
        """
        config = get_llamaindex_instance().config
        assert config.mistral_endpoint == "https://api.eu.mistral.ai"

    def test_the_endpoint_can_be_overridden(self, monkeypatch):
        """
        MISTRAL_API_ENDPOINT selects another endpoint
        """
        monkeypatch.setenv("MISTRAL_API_ENDPOINT", "https://api.mistral.ai")
        config = get_llamaindex_instance().config
        assert config.mistral_endpoint == "https://api.mistral.ai"

    def test_summaries_use_the_configured_endpoint(self, mocker, monkeypatch):
        """
        The language model used for summaries is created with the endpoint
        """
        monkeypatch.setenv("MISTRAL_API_ENDPOINT", "https://example.test")
        mistral = mocker.patch("ddlh.rag.llamaindex.MistralAI")
        mocker.patch("ddlh.rag.llamaindex.get_response_synthesizer")

        get_llamaindex_instance().synthesize("prompt", nodes=[])

        assert mistral.call_args.kwargs["endpoint"] == "https://example.test"

    def test_embeddings_use_the_configured_endpoint(self, monkeypatch):
        """
        Both the sync and async embedding clients use the endpoint
        """
        monkeypatch.setenv("MISTRAL_API_ENDPOINT", "https://example.test")

        embedding = get_llamaindex_instance().embedding_model

        assert embedding._mistralai_client._endpoint == "https://example.test"
        assert embedding._mistralai_async_client._endpoint == "https://example.test"
