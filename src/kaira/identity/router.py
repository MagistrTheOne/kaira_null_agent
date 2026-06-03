from kaira.identity.dialogue import (
    DIALOGUE_GOAL,
    OBJECTIONS,
    PRIORITY,
    QUALIFICATION,
)
from kaira.identity.kernel import KAIRA_CORE_KERNEL, NULLXES_BRAND_CANONICAL_RU
from kaira.identity.runtime import RUNTIME_BEHAVIOR, TERMINOLOGY_COMPACT
from kaira.identity.voice import MODE_VOICE_DELTA, VOICE_STYLE
from kaira.modes import KairaMode

_MODE_RUNTIME_DELTA: dict[KairaMode, str] = {
    KairaMode.MAGISTER: "Magister Protocol активен — обращение «Маг».",
    KairaMode.CRITICAL: "Режим критичности: без необязательных side-effects.",
}

_SALES_MODES = {KairaMode.PUBLIC, KairaMode.DEMO}


def build_instructions(mode: KairaMode = KairaMode.PUBLIC) -> str:
    parts = [
        KAIRA_CORE_KERNEL,
        VOICE_STYLE,
        MODE_VOICE_DELTA.get(mode, ""),
    ]
    if mode in _SALES_MODES:
        parts.extend([DIALOGUE_GOAL, QUALIFICATION, OBJECTIONS, PRIORITY])
    parts.extend(
        [
            TERMINOLOGY_COMPACT,
            RUNTIME_BEHAVIOR,
            _MODE_RUNTIME_DELTA.get(mode, ""),
            f"Бренд: {NULLXES_BRAND_CANONICAL_RU}.",
        ]
    )
    return "\n\n".join(part for part in parts if part.strip())


def build_kaira_instructions() -> str:
    return build_instructions(KairaMode.PUBLIC)


KAIRA_INSTRUCTIONS = build_kaira_instructions()
