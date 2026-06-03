import pytest

from services.news import NewsServiceError
from services.web_search import search_web


@pytest.mark.asyncio
async def test_search_web_requires_query() -> None:
    with pytest.raises(NewsServiceError):
        await search_web("   ")


@pytest.mark.asyncio
async def test_search_web_uses_firecrawl(monkeypatch) -> None:
    async def fake_search(query: str, *, limit: int = 5):
        assert query == "Acme Corp"
        return {
            "query": query,
            "results": [
                {
                    "title": "Acme overview",
                    "url": "https://example.com/acme",
                    "description": "Acme builds widgets.",
                }
            ],
        }

    monkeypatch.setattr("services.web_search.firecrawl_available", lambda: True)
    monkeypatch.setattr("services.web_search.firecrawl_search", fake_search)

    brief = await search_web("Acme Corp")
    assert "Acme" in brief.answer
    assert brief.sources[0]["url"] == "https://example.com/acme"
