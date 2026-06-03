import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

import aiohttp
from livekit.agents import utils

from services.firecrawl import (
    FirecrawlServiceError,
    firecrawl_available,
    firecrawl_search,
)


class NewsServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class NewsBrief:
    query: str
    answer: str
    sources: list[dict[str, str]]

    def to_voice_summary(self) -> str:
        if not self.sources:
            return self.answer

        source_names = ", ".join(source["title"] for source in self.sources[:3])
        return f"{self.answer}\n\nИсточники: {source_names}"


def _normalise_sources(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for item in results[:5]:
        title = str(item.get("title") or item.get("url") or "source").strip()
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        sources.append({"title": title[:120], "url": url})
    return sources


async def tavily_search_raw(query: str, search_depth: str = "basic") -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise NewsServiceError("TAVILY_API_KEY is not configured")

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "include_answer": True,
        "max_results": 5,
    }

    try:
        session = utils.http_context.http_session()
        timeout = aiohttp.ClientTimeout(total=12)
        async with session.post(
            "https://api.tavily.com/search",
            timeout=timeout,
            json=payload,
        ) as resp:
            if resp.status >= 400:
                raise NewsServiceError(f"Tavily HTTP {resp.status}")
            return await resp.text()
    except NewsServiceError:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        raise NewsServiceError(str(exc)) from exc


async def get_news_brief(
    topic: str,
    *,
    region: str = "RU",
    search_depth: str = "basic",
) -> NewsBrief:
    query = f"{topic.strip()} latest news {region} May 2026"
    if firecrawl_available():
        try:
            data = await firecrawl_search(query, limit=5)
            results = data.get("results") or []
            snippets = [
                str(
                    item.get("markdown")
                    or item.get("description")
                    or item.get("title")
                    or ""
                ).strip()
                for item in results[:3]
                if str(
                    item.get("markdown")
                    or item.get("description")
                    or item.get("title")
                    or ""
                ).strip()
            ]
            answer = " ".join(snippets)[:1200] or "Актуальная сводка не найдена."
            return NewsBrief(
                query=query,
                answer=answer,
                sources=_normalise_sources(results),
            )
        except FirecrawlServiceError:
            pass

    raw = await tavily_search_raw(query, search_depth=search_depth)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NewsServiceError("Tavily returned invalid JSON") from exc

    answer = str(data.get("answer") or "").strip()
    if not answer:
        results = data.get("results") or []
        snippets = [
            str(item.get("content") or item.get("title") or "").strip()
            for item in results[:3]
            if str(item.get("content") or item.get("title") or "").strip()
        ]
        answer = " ".join(snippets)[:900] or "Актуальная сводка не найдена."

    return NewsBrief(
        query=query,
        answer=answer[:1200],
        sources=_normalise_sources(data.get("results") or []),
    )
