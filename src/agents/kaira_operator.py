import json
from typing import Optional

from livekit.agents import RunContext, ToolError, function_tool

from agents.kaira_public import KairaPublicAgent
from kaira.modes import KairaMode
from kaira.session_context import KairaSessionContext
from kaira.vision import image_content_from_screenshot_value, vision_enabled
from runtime.policy_gate import enforce_operator_policy
from runtime.room_memory import KairaRoomMemory
from services.audit import write_audit_event
from services.firecrawl import (
    FirecrawlServiceError,
    firecrawl_scrape,
    firecrawl_search,
)
from services.mcp_executor import (
    McpExecutorError,
    browser_research,
    browser_screenshot,
    browser_snapshot,
    execute_browser_action,
)
from services.news import NewsServiceError, get_news_brief, tavily_search_raw
from services.spotify import SpotifyServiceError, play_track, search_tracks
from services.vision_evidence import normalize_vision_evidence


class KairaOperatorAgent(KairaPublicAgent):
    def __init__(
        self,
        kaira_ctx: KairaSessionContext,
        memory: KairaRoomMemory,
    ) -> None:
        kaira_ctx.mode = KairaMode.OPERATOR
        super().__init__(kaira_ctx, memory)

    def _gate(self) -> None:
        if self._kaira_ctx.mode == KairaMode.CRITICAL:
            enforce_operator_policy(
                self._policy_command(),
                allow_in_critical=False,
            )
            return
        enforce_operator_policy(self._policy_command())

    @function_tool(name="tavily_search")
    async def tavily_search(
        self,
        context: RunContext,
        query: str,
        search_depth: Optional[str] = None,
    ) -> str | None:
        """Search public web data for enterprise and market context."""

        context.disallow_interruptions()
        self._gate()
        try:
            return await tavily_search_raw(query, search_depth or "basic")
        except NewsServiceError as exc:
            raise ToolError(f"error: {exc!s}") from exc

    @function_tool(name="get_news_brief")
    async def get_news_brief_tool(
        self,
        context: RunContext,
        topic: str,
        region: Optional[str] = None,
        search_depth: Optional[str] = None,
    ) -> str:
        """Concise news or market briefing."""

        context.disallow_interruptions()
        self._gate()
        try:
            brief = await get_news_brief(
                topic,
                region=region or "RU",
                search_depth=search_depth or "basic",
            )
            write_audit_event(
                command=topic,
                action="news_brief",
                decision="allow",
                tool="get_news_brief",
                status="ok",
                evidence={"query": brief.query, "sources": brief.sources[:3]},
            )
            return brief.to_voice_summary()
        except NewsServiceError as exc:
            write_audit_event(
                command=topic,
                action="news_brief",
                decision="allow",
                tool="get_news_brief",
                status="error",
                evidence={"error": str(exc)},
            )
            raise ToolError(f"error: {exc!s}") from exc

    @function_tool(name="web_search")
    async def web_search_tool(
        self,
        context: RunContext,
        query: str,
        limit: Optional[int] = None,
    ) -> str:
        """Search the public web (Firecrawl)."""

        context.disallow_interruptions()
        self._gate()
        try:
            data = await firecrawl_search(query, limit=limit or 5)
            results = data.get("results") or []
            write_audit_event(
                command=query,
                action="web_search",
                decision="allow",
                tool="firecrawl_search",
                status="ok",
                evidence={"resultCount": len(results)},
            )
            return json.dumps(
                {"query": query, "results": results[:5]}, ensure_ascii=False
            )
        except FirecrawlServiceError as exc:
            write_audit_event(
                command=query,
                action="web_search",
                decision="allow",
                tool="firecrawl_search",
                status="error",
                evidence={"error": str(exc)},
            )
            raise ToolError(f"firecrawl_not_ready: {exc!s}") from exc

    @function_tool(name="scrape_website")
    async def scrape_website_tool(
        self,
        context: RunContext,
        url: str,
    ) -> str:
        """Scrape a public website and return markdown."""

        context.disallow_interruptions()
        self._gate()
        try:
            data = await firecrawl_scrape(url)
            write_audit_event(
                command=url,
                action="scrape_website",
                decision="allow",
                tool="firecrawl_scrape",
                status="ok",
                evidence={"url": url, "chars": len(data.get("markdown", ""))},
            )
            return json.dumps(
                {"url": url, "markdown": data.get("markdown", "")},
                ensure_ascii=False,
            )
        except FirecrawlServiceError as exc:
            write_audit_event(
                command=url,
                action="scrape_website",
                decision="allow",
                tool="firecrawl_scrape",
                status="error",
                evidence={"error": str(exc)},
            )
            raise ToolError(f"firecrawl_not_ready: {exc!s}") from exc

    @function_tool(name="spotify_search_track")
    async def spotify_search_track_tool(
        self,
        context: RunContext,
        query: str,
    ) -> str:
        """Search Spotify tracks."""

        context.disallow_interruptions()
        self._gate()
        try:
            tracks = await search_tracks(query)
            write_audit_event(
                command=query,
                action="spotify_search",
                decision="allow",
                tool="spotify_search_track",
                status="ok",
                evidence={"resultCount": len(tracks)},
            )
            return json.dumps({"tracks": tracks}, ensure_ascii=False)
        except SpotifyServiceError as exc:
            raise ToolError(f"spotify_not_ready: {exc!s}") from exc

    @function_tool(name="spotify_play")
    async def spotify_play_tool(
        self,
        context: RunContext,
        query: str,
    ) -> str:
        """Search and play a Spotify track."""

        context.disallow_interruptions()
        self._gate()
        try:
            track = await play_track(query)
            write_audit_event(
                command=query,
                action="spotify_play",
                decision="allow",
                tool="spotify_play",
                status="ok",
                evidence={"track": track},
            )
            return json.dumps({"playing": track}, ensure_ascii=False)
        except SpotifyServiceError as exc:
            raise ToolError(f"spotify_not_ready: {exc!s}") from exc

    @function_tool(name="browser_research")
    async def browser_research_tool(
        self,
        context: RunContext,
        query: str,
        objective: Optional[str] = None,
    ) -> str:
        """Browser-backed research via MCP executor."""

        context.disallow_interruptions()
        self._gate()
        try:
            result = await browser_research(query, objective)
            write_audit_event(
                command=query,
                action="browser_research",
                decision="allow",
                tool="browser_research",
                status="ok",
                evidence={"objective": objective or "research"},
            )
            return result
        except McpExecutorError as exc:
            raise ToolError(f"mcp_browser_not_ready: {exc!s}") from exc

    @function_tool(name="browser_action")
    async def browser_action_tool(
        self,
        context: RunContext,
        action: str,
        query: Optional[str] = None,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        objective: Optional[str] = None,
    ) -> str:
        """Execute a typed browser action."""

        context.disallow_interruptions()
        self._gate()
        allowed_actions = {
            "navigate",
            "snapshot",
            "click",
            "fill",
            "screenshot",
            "run_test_flow",
        }
        if action not in allowed_actions:
            raise ToolError(f"browser_action_not_allowed: {action}")

        try:
            result = await execute_browser_action(
                action,
                query=query,
                url=url,
                selector=selector,
                text=text,
                objective=objective,
                timeout_seconds=90 if action == "run_test_flow" else 45,
            )
            write_audit_event(
                command=query or url or action,
                action=f"browser_{action}",
                decision="allow",
                tool="browser_action",
                status="ok",
                evidence={"objective": objective, "hasResult": bool(result)},
            )
            return json.dumps(result, ensure_ascii=False)
        except McpExecutorError as exc:
            raise ToolError(f"mcp_browser_not_ready: {exc!s}") from exc

    @function_tool(name="inspect_current_screen_or_browser_state")
    async def inspect_current_screen_or_browser_state_tool(
        self,
        context: RunContext,
        objective: Optional[str] = None,
    ) -> str:
        """Inspect browser evidence from snapshot and screenshot."""

        context.disallow_interruptions()
        self._gate()
        try:
            snapshot = await browser_snapshot(objective)
            screenshot = await browser_screenshot(objective)
            screenshot_value = screenshot.get("screenshot") or screenshot.get("image")
            evidence = normalize_vision_evidence(
                {
                    **snapshot,
                    "screenshot": screenshot_value,
                }
            )
            if vision_enabled():
                image = image_content_from_screenshot_value(
                    str(screenshot_value) if screenshot_value is not None else None
                )
                if image is not None:
                    caption = objective or (
                        "Скриншот браузера для анализа. Опиши, что видно, кратко."
                    )
                    await self.inject_user_vision_message(image, caption)
            write_audit_event(
                command=objective or "inspect_current_screen_or_browser_state",
                action="vision_inspect",
                decision="allow",
                tool="inspect_current_screen_or_browser_state",
                status="ok",
                evidence={
                    "hasScreenshot": evidence.has_screenshot,
                    "hasSnapshot": evidence.has_snapshot,
                    "url": evidence.url,
                },
            )
            return evidence.to_voice_summary()
        except McpExecutorError as exc:
            raise ToolError(f"vision_evidence_not_ready: {exc!s}") from exc


def create_operator_agent(
    kaira_ctx: KairaSessionContext,
    memory: KairaRoomMemory,
) -> KairaOperatorAgent:
    return KairaOperatorAgent(kaira_ctx, memory)
