import pytest
from livekit.agents import ToolError

from runtime.policy_gate import PolicyConfirmationRequired, enforce_operator_policy
from services.command_policy import PolicyDecision


def test_policy_denies_force_push() -> None:
    with pytest.raises(ToolError, match="policy_denied"):
        enforce_operator_policy("Кайра, сделай push --force в main")


def test_policy_confirms_git_push() -> None:
    with pytest.raises(PolicyConfirmationRequired):
        enforce_operator_policy("Кайра, git push в main")


def test_policy_allows_news() -> None:
    result = enforce_operator_policy("Кайра, какие новости по AI сегодня?")
    assert result.decision == PolicyDecision.ALLOW
