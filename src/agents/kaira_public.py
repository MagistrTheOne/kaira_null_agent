import json
from typing import Optional

from livekit.agents import RunContext, ToolError, function_tool

from agents.kaira_base import KairaAgentBase
from kaira.identity.openings import opening_for_mode
from kaira.modes import KairaMode
from kaira.session_context import KairaSessionContext
from runtime.room_memory import KairaRoomMemory
from services.audit import write_audit_event
from services.mcp_executor import (
    McpExecutorError,
    browser_research,
    mcp_browser_available,
)
from services.magister_protocol import (
    activate_magister_protocol,
    deactivate_magister_protocol,
)
from services.news import NewsServiceError
from services.web_search import search_web as search_web_brief


class KairaPublicAgent(KairaAgentBase):
    async def on_enter(self) -> None:
        await super().on_enter()
        await self.session.say(
            opening_for_mode(self._kaira_ctx.mode),
            allow_interruptions=True,
        )

    @function_tool(name="operator_status")
    async def operator_status(self, context: RunContext) -> str:
        """Report which KAIRA operator contours are live."""

        context.disallow_interruptions()
        return json.dumps(self._operator_status_payload(), ensure_ascii=False)

    @function_tool(name="activate_magister_protocol")
    async def activate_magister_protocol_tool(
        self,
        context: RunContext,
        command: str,
    ) -> str:
        """Activate Magister Protocol only if the command matches the secret phrase."""

        context.disallow_interruptions()
        result = activate_magister_protocol(command)
        if result.matched:
            await self.apply_mode(KairaMode.MAGISTER)
        write_audit_event(
            command="[magister_activation_attempt]",
            action="magister_protocol_activate",
            decision="allow" if result.matched else "deny",
            tool="activate_magister_protocol",
            status="ok" if result.matched else "rejected",
            evidence={"mode": result.mode},
        )
        return json.dumps(
            {
                "active": self._kaira_ctx.magister_active,
                "mode": result.mode,
                "response": result.response,
            },
            ensure_ascii=False,
        )

    @function_tool(name="deactivate_magister_protocol")
    async def deactivate_magister_protocol_tool(
        self,
        context: RunContext,
        command: str,
    ) -> str:
        """Deactivate Magister Protocol only if the command matches the phrase."""

        context.disallow_interruptions()
        result = deactivate_magister_protocol(command)
        if result.matched:
            await self.apply_mode(KairaMode.PUBLIC)
        write_audit_event(
            command="[magister_deactivation_attempt]",
            action="magister_protocol_deactivate",
            decision="allow" if result.matched else "deny",
            tool="deactivate_magister_protocol",
            status="ok" if result.matched else "rejected",
            evidence={"mode": result.mode},
        )
        return json.dumps(
            {
                "active": self._kaira_ctx.magister_active,
                "mode": self._kaira_ctx.mode.value,
                "response": result.response,
            },
            ensure_ascii=False,
        )

    @function_tool(name="search_web")
    async def search_web_tool(
        self,
        context: RunContext,
        query: str,
    ) -> str:
        """Search the public web for a company, market, or topic and return a brief Russian summary."""

        context.disallow_interruptions()
        try:
            brief = await search_web_brief(query)
            write_audit_event(
                command=query,
                action="search_web",
                decision="allow",
                tool="search_web",
                status="ok",
                evidence={"sources": brief.sources[:3]},
            )
            return brief.to_voice_summary()
        except NewsServiceError as exc:
            write_audit_event(
                command=query,
                action="search_web",
                decision="allow",
                tool="search_web",
                status="error",
                evidence={"error": str(exc)},
            )
            raise ToolError(f"search_not_ready: {exc!s}") from exc

    @function_tool(name="browser_research")
    async def browser_research_tool(
        self,
        context: RunContext,
        query: str,
        objective: Optional[str] = None,
    ) -> str:
        """Deep browser research for company sites, news, and live web pages."""

        context.disallow_interruptions()
        if not mcp_browser_available():
            raise ToolError("browser_not_ready: MCP browser contour is not configured")
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
            raise ToolError(f"browser_not_ready: {exc!s}") from exc


def create_public_agent(
    kaira_ctx: KairaSessionContext,
    memory: KairaRoomMemory,
) -> KairaPublicAgent:
    return KairaPublicAgent(kaira_ctx, memory)
