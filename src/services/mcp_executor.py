import os
from dataclasses import dataclass
from typing import Any

import aiohttp
from livekit.agents import utils


class McpExecutorError(RuntimeError):
    pass


@dataclass(frozen=True)
class McpExecutorConfig:
    endpoint: str
    token: str | None = None

    @classmethod
    def from_env(cls) -> "McpExecutorConfig | None":
        endpoint = os.getenv("KAIRA_MCP_BROWSER_ENDPOINT", "").strip()
        if not endpoint:
            return None
        return cls(
            endpoint=endpoint,
            token=os.getenv("KAIRA_MCP_BROWSER_TOKEN", "").strip() or None,
        )


def mcp_browser_available() -> bool:
    return McpExecutorConfig.from_env() is not None


async def execute_browser_action(
    action: str,
    *,
    query: str | None = None,
    url: str | None = None,
    selector: str | None = None,
    text: str | None = None,
    objective: str | None = None,
    timeout_seconds: int = 45,
) -> dict[str, Any]:
    config = McpExecutorConfig.from_env()
    if not config:
        raise McpExecutorError("MCP browser contour is not configured")

    headers = {"Content-Type": "application/json"}
    if config.token:
        headers["Authorization"] = f"Bearer {config.token}"

    session = utils.http_context.http_session()
    async with session.post(
        config.endpoint,
        headers=headers,
        json={
            "action": action,
            "query": query,
            "url": url,
            "selector": selector,
            "text": text,
            "objective": objective or "research",
            "source": "KAIRA-NULLXES",
        },
        timeout=aiohttp.ClientTimeout(total=timeout_seconds),
    ) as resp:
        if resp.status >= 400:
            raise McpExecutorError(f"MCP browser HTTP {resp.status}")
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await resp.json()
            if isinstance(payload, dict):
                return payload
            return {"result": payload}
        return {"result": await resp.text()}


async def browser_research(query: str, objective: str | None = None) -> str:
    payload = await execute_browser_action(
        "research",
        query=query,
        objective=objective,
    )
    return str(payload.get("summary") or payload.get("result") or payload)


async def browser_navigate(url: str, objective: str | None = None) -> dict[str, Any]:
    return await execute_browser_action("navigate", url=url, objective=objective)


async def browser_snapshot(objective: str | None = None) -> dict[str, Any]:
    return await execute_browser_action("snapshot", objective=objective)


async def browser_click(selector: str, objective: str | None = None) -> dict[str, Any]:
    return await execute_browser_action("click", selector=selector, objective=objective)


async def browser_fill(
    selector: str,
    text: str,
    objective: str | None = None,
) -> dict[str, Any]:
    return await execute_browser_action(
        "fill",
        selector=selector,
        text=text,
        objective=objective,
    )


async def browser_screenshot(objective: str | None = None) -> dict[str, Any]:
    return await execute_browser_action("screenshot", objective=objective)


async def browser_run_test_flow(
    objective: str,
    query: str | None = None,
) -> dict[str, Any]:
    return await execute_browser_action(
        "run_test_flow",
        query=query,
        objective=objective,
        timeout_seconds=90,
    )
