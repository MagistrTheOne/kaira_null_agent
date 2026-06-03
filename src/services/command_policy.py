from dataclasses import dataclass
from enum import Enum


class OperatorAction(str, Enum):
    NEWS_BRIEF = "news_brief"
    WEB_SEARCH = "web_search"
    SCRAPE_WEBSITE = "scrape_website"
    SPOTIFY_SEARCH = "spotify_search"
    SPOTIFY_PLAY = "spotify_play"
    BROWSER_RESEARCH = "browser_research"
    BROWSER_ACTION = "browser_action"
    CHECK_FILES = "check_files"
    OPEN_PROJECT = "open_project"
    RUN_TESTS = "run_tests"
    SHELL_ACTION = "shell_action"
    PUSH_REPO = "push_repo"
    DELETE_FILE = "delete_file"
    STATUS = "status"
    DENIED = "denied"
    UNKNOWN = "unknown"


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"
    CLARIFY = "clarify"


@dataclass(frozen=True)
class CommandPolicyResult:
    action: OperatorAction
    decision: PolicyDecision
    reason: str

    @property
    def is_allowed(self) -> bool:
        return self.decision == PolicyDecision.ALLOW


_DENIED_MARKERS = (
    "удали",
    "сотри",
    "delete file",
    "remove file",
    "переведи деньги",
    "купи",
    "оплати",
    "force push",
    "push --force",
    "обойди",
    "взлом",
    "укради",
    "пароль",
    "секрет",
    "token",
    "api key",
)

_CONFIRM_MARKERS = (
    "отправь",
    "опубликуй",
    "напиши клиенту",
    "позвони",
    "создай заявку",
    "измени",
    "закрой",
    "запусти тест",
    "run test",
    "открой проект",
    "open project",
    "запусти скрипт",
    "run script",
    "shell",
    "push",
    "git push",
    "submit",
)


def classify_operator_command(command: str) -> CommandPolicyResult:
    value = command.strip().lower()
    if not value:
        return CommandPolicyResult(
            action=OperatorAction.UNKNOWN,
            decision=PolicyDecision.CLARIFY,
            reason="empty_command",
        )

    if any(marker in value for marker in _DENIED_MARKERS):
        return CommandPolicyResult(
            action=OperatorAction.DENIED,
            decision=PolicyDecision.DENY,
            reason="unsafe_or_sensitive_action",
        )

    if "что ты умеешь" in value or "статус" in value or "контур" in value:
        return CommandPolicyResult(
            action=OperatorAction.STATUS,
            decision=PolicyDecision.ALLOW,
            reason="operator_status",
        )

    if "новост" in value or "сводк" in value or "гугл" in value or "найди" in value:
        return CommandPolicyResult(
            action=OperatorAction.NEWS_BRIEF,
            decision=PolicyDecision.ALLOW,
            reason="information_retrieval",
        )

    if "scrape" in value or "соскрейп" in value or "прочитай сайт" in value:
        return CommandPolicyResult(
            action=OperatorAction.SCRAPE_WEBSITE,
            decision=PolicyDecision.ALLOW,
            reason="website_read",
        )

    if "search web" in value or "web search" in value or "поищи в интернете" in value:
        return CommandPolicyResult(
            action=OperatorAction.WEB_SEARCH,
            decision=PolicyDecision.ALLOW,
            reason="web_search",
        )

    if "spotify" in value or "спотиф" in value or "включи" in value or "трек" in value:
        action = (
            OperatorAction.SPOTIFY_PLAY
            if "включи" in value or "play" in value
            else OperatorAction.SPOTIFY_SEARCH
        )
        return CommandPolicyResult(
            action=action,
            decision=PolicyDecision.ALLOW,
            reason="spotify_media_action",
        )

    if "проверь последние файлы" in value or "check files" in value:
        return CommandPolicyResult(
            action=OperatorAction.CHECK_FILES,
            decision=PolicyDecision.ALLOW,
            reason="read_only_project_inspection",
        )

    if "запусти тест" in value or "run test" in value:
        return CommandPolicyResult(
            action=OperatorAction.RUN_TESTS,
            decision=PolicyDecision.CONFIRM,
            reason="local_execution_requires_confirmation",
        )

    if "открой проект" in value or "open project" in value:
        return CommandPolicyResult(
            action=OperatorAction.OPEN_PROJECT,
            decision=PolicyDecision.CONFIRM,
            reason="local_ide_action_requires_confirmation",
        )

    if "git push" in value or "запуш" in value or "push repo" in value:
        return CommandPolicyResult(
            action=OperatorAction.PUSH_REPO,
            decision=PolicyDecision.CONFIRM,
            reason="repository_write_requires_confirmation",
        )

    if "браузер" in value or "открой сайт" in value or "страниц" in value:
        return CommandPolicyResult(
            action=OperatorAction.BROWSER_ACTION,
            decision=PolicyDecision.ALLOW,
            reason="browser_action",
        )

    if any(marker in value for marker in _CONFIRM_MARKERS):
        return CommandPolicyResult(
            action=OperatorAction.UNKNOWN,
            decision=PolicyDecision.CONFIRM,
            reason="external_side_effect_requires_confirmation",
        )

    return CommandPolicyResult(
        action=OperatorAction.UNKNOWN,
        decision=PolicyDecision.CLARIFY,
        reason="not_an_operator_command",
    )
