from services.firecrawl import FirecrawlConfig, firecrawl_available


def test_firecrawl_availability_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    assert firecrawl_available() is False
    assert FirecrawlConfig.from_env() is None


def test_firecrawl_config_uses_env_key(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")

    config = FirecrawlConfig.from_env()

    assert config is not None
    assert config.api_key == "fc-test"
    assert firecrawl_available() is True
