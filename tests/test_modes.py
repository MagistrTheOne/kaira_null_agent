from kaira.identity.openings import opening_for_mode
from kaira.identity.router import build_instructions
from kaira.modes import KairaMode


def test_openings_per_mode() -> None:
    assert opening_for_mode(KairaMode.PUBLIC) != opening_for_mode(KairaMode.MAGISTER)
    assert "Маг" in opening_for_mode(KairaMode.MAGISTER)


def test_critical_mode_runtime_hint() -> None:
    text = build_instructions(KairaMode.CRITICAL)
    assert "критичност" in text.lower() or "side-effect" in text.lower()
