import json
from typing import Any

from services.firecrawl import (
    FirecrawlServiceError,
    firecrawl_available,
    firecrawl_search,
)
from services.news import (
    NewsBrief,
    NewsServiceError,
    _normalise_sources,
    tavily_search_raw,
)


async def search_web(query: str) -> NewsBrief:
    """Web search for companies, markets, and current briefs — voice-ready summary."""
    normalized = query.strip()
    if not normalized:
        raise NewsServiceError("search query is empty")

    if firecrawl_available():
        try:
            data = await firecrawl_search(normalized, limit=5)
            results = data.get("results") or []
            snippets = _collect_snippets(results)
            answer = " ".join(snippets)[:1200] or "По запросу ничего не нашла."
            return NewsBrief(
                query=normalized,
                answer=answer,
                sources=_normalise_sources(results),
            )
        except FirecrawlServiceError:
            pass

    raw = await tavily_search_raw(normalized, search_depth="basic")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NewsServiceError("Tavily returned invalid JSON") from exc

    answer = str(data.get("answer") or "").strip()
    if not answer:
        snippets = _collect_snippets(data.get("results") or [], tavily=True)
        answer = " ".join(snippets)[:900] or "По запросу ничего не нашла."

    return NewsBrief(
        query=normalized,
        answer=answer[:1200],
        sources=_normalise_sources(data.get("results") or []),
    )


def _collect_snippets(
    results: list[dict[str, Any]], *, tavily: bool = False
) -> list[str]:
    snippets: list[str] = []
    for item in results[:3]:
        if tavily:
            value = str(item.get("content") or item.get("title") or "").strip()
        else:
            value = str(
                item.get("markdown")
                or item.get("description")
                or item.get("title")
                or ""
            ).strip()
        if value:
            snippets.append(value)
    return snippets
