from dataclasses import dataclass, field

from kaira.modes import KairaMode


@dataclass
class KairaSessionContext:
    mode: KairaMode = KairaMode.PUBLIC
    operator_enabled: bool = False
    magister_active: bool = False
    last_user_utterance: str = ""
    injected_positioning_keys: set[str] = field(default_factory=set)
