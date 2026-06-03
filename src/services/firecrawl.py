import os
from dataclasses import dataclass
from typing import Any

import aiohttp
from livekit.agents import utils

FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v2"


class FirecrawlServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class FirecrawlConfig:
    api_key: str
    base_url: str = FIRECRAWL_BASE_URL

    @classmethod
    def from_env(cls) -> "FirecrawlConfig | None":
        api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            base_url=os.getenv("FIRECRAWL_BASE_URL", FIRECRAWL_BASE_URL).rstrip("/"),
        )


def firecrawl_available() -> bool:
    return FirecrawlConfig.from_env() is not None


async def _post_firecrawl(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    config = FirecrawlConfig.from_env()
    if not config:
        raise FirecrawlServiceError("FIRECRAWL_API_KEY is not configured")

    session = utils.http_context.http_session()
    async with session.post(
        f"{config.base_url}{path}",
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=aiohttp.ClientTimeout(total=timeout_seconds),
    ) as resp:
        if resp.status >= 400:
            raise FirecrawlServiceError(f"Firecrawl HTTP {resp.status}")
        data = await resp.json()
        if isinstance(data, dict):
            return data
        raise FirecrawlServiceError("Firecrawl returned invalid payload")


def _extract_markdown(data: dict[str, Any]) -> str:
    if isinstance(data.get("markdown"), str):
        return data["markdown"]
    nested = data.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("markdown"), str):
        return nested["markdown"]
    return ""


async def firecrawl_scrape(url: str) -> dict[str, Any]:
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
    }
    data = await _post_firecrawl("/scrape", payload)
    return {
        "url": url,
        "markdown": _extract_markdown(data)[:5000],
        "raw": data,
    }


async def firecrawl_search(query: str, *, limit: int = 5) -> dict[str, Any]:
    payload = {
        "query": query,
        "limit": max(1, min(limit, 10)),
        "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
    }
    data = await _post_firecrawl("/search", payload)
    return {
        "query": query,
        "results": data.get("data") or data.get("results") or [],
        "raw": data,
    }


async def firecrawl_extract(
    url: str, schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {"urls": [url]}
    if schema:
        payload["schema"] = schema
    return await _post_firecrawl("/extract", payload, timeout_seconds=45)
