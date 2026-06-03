"""Tool surface registry by session mode and operator env."""

from kaira.modes import KairaMode

PUBLIC_TOOL_NAMES = frozenset(
    {
        "operator_status",
        "activate_magister_protocol",
        "deactivate_magister_protocol",
        "search_web",
        "browser_research",
    }
)

OPERATOR_TOOL_NAMES = PUBLIC_TOOL_NAMES | frozenset(
    {
        "tavily_search",
        "get_news_brief",
        "web_search",
        "scrape_website",
        "spotify_search_track",
        "spotify_play",
        "browser_research",
        "browser_action",
        "inspect_current_screen_or_browser_state",
    }
)


def expected_tool_names(mode: KairaMode, *, operator_enabled: bool) -> frozenset[str]:
    if not operator_enabled:
        return PUBLIC_TOOL_NAMES
    if mode in {KairaMode.OPERATOR, KairaMode.MAGISTER}:
        return OPERATOR_TOOL_NAMES
    return PUBLIC_TOOL_NAMES
