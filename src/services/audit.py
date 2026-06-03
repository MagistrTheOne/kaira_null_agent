import json
import os
import re
import time
from pathlib import Path
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"fc-[A-Za-z0-9_-]+"),
    re.compile(r"sk-[A-Za-z0-9_-]+"),
    re.compile(r"API[A-Z0-9]+"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)[\"'=:\s]+[^,\s\"'}]+"),
)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_secrets(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if not isinstance(value, str):
        return value

    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def audit_enabled() -> bool:
    return bool(os.getenv("KAIRA_AUDIT_LOG_PATH", "").strip())


def write_audit_event(
    *,
    command: str,
    action: str,
    decision: str,
    tool: str,
    status: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    log_path = os.getenv("KAIRA_AUDIT_LOG_PATH", "").strip()
    if not log_path:
        return

    event = {
        "timestampMs": int(time.time() * 1000),
        "agent": os.getenv("KAIRA_AGENT_NAME", "KAIRA-NULLXES"),
        "command": command,
        "action": action,
        "decision": decision,
        "tool": tool,
        "status": status,
        "evidence": evidence or {},
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(redact_secrets(event), ensure_ascii=False) + "\n")
