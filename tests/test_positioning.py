from kaira.identity.positioning import (
    detect_positioning_trigger,
    format_positioning_inject,
    positioning_block,
)


def test_greeting_no_positioning_trigger() -> None:
    assert detect_positioning_trigger("Привет") is None
    assert detect_positioning_trigger("Hello") is None


def test_nullxes_question_triggers_ultra() -> None:
    assert detect_positioning_trigger("Что такое NULLXES?") == "ultra"


def test_pilot_price_trigger() -> None:
    assert detect_positioning_trigger("Сколько стоит пилот?") == "pilot_price"
    block = positioning_block("pilot_price")
    assert block is not None
    assert "250" in block


def test_inject_format() -> None:
    inject = format_positioning_inject("ultra")
    assert "НУЛЛЕКСЕС" in inject
    assert "только для этого ответа" in inject.lower()
