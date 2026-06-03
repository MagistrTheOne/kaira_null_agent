from agents.kaira_operator import KairaOperatorAgent
from agents.kaira_public import KairaPublicAgent
from kaira.modes import KairaMode
from kaira.session_context import KairaSessionContext
from runtime.room_memory import KairaRoomMemory
from tools.registry import PUBLIC_TOOL_NAMES, expected_tool_names


def test_operator_mode_disabled_tool_surface() -> None:
    names = expected_tool_names(KairaMode.PUBLIC, operator_enabled=False)
    assert names == PUBLIC_TOOL_NAMES


def test_public_agent_tool_count() -> None:
    ctx = KairaSessionContext(mode=KairaMode.PUBLIC, operator_enabled=False)
    memory = KairaRoomMemory(room_name="test")
    agent = KairaPublicAgent(ctx, memory)
    tool_ids = {tool.id for tool in agent.tools}
    assert tool_ids == PUBLIC_TOOL_NAMES
    assert "search_web" in tool_ids
    assert "browser_research" in tool_ids


def test_operator_agent_has_search_tools() -> None:
    ctx = KairaSessionContext(mode=KairaMode.OPERATOR, operator_enabled=True)
    memory = KairaRoomMemory(room_name="test")
    agent = KairaOperatorAgent(ctx, memory)
    tool_ids = {tool.id for tool in agent.tools}
    assert "web_search" in tool_ids
    assert "get_news_brief" in tool_ids
