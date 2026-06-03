from livekit.agents import ToolError

from services.command_policy import (
    CommandPolicyResult,
    PolicyDecision,
    classify_operator_command,
)


class PolicyConfirmationRequired(ToolError):
    """Side-effect requires explicit user confirmation."""


def enforce_operator_policy(
    command: str,
    *,
    allow_in_critical: bool = False,
) -> CommandPolicyResult:
    result = classify_operator_command(command)

    if result.decision == PolicyDecision.DENY:
        raise ToolError(f"policy_denied: {result.reason}")

    if result.decision == PolicyDecision.CONFIRM and not allow_in_critical:
        raise PolicyConfirmationRequired(
            "Нужно явное подтверждение перед этим действием. Сформулируйте «да, выполняй»."
        )

    return result
