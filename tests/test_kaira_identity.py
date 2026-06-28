"""Unit tests for KAIRA identity layer (no LLM)."""

from kaira.identity.kernel import NULLXES_BRAND_CANONICAL_RU, NULLXES_STT_NORMALIZE_FROM
from kaira.identity.openings import KAIRA_OPENING, opening_for_mode
from kaira.identity.positioning import (
    NULLXES_POSITIONING_ENTERPRISE_INTRO,
    NULLXES_POSITIONING_HOMEPAGE,
    NULLXES_POSITIONING_ULTRA_SHORT,
)
from kaira.identity.router import (
    KAIRA_INSTRUCTIONS,
    build_instructions,
    build_kaira_instructions,
)
from kaira.modes import KairaMode


def test_positioning_tiers_non_empty() -> None:
    assert "НУЛЛЕКСЕС" in NULLXES_POSITIONING_ULTRA_SHORT
    assert "цифров" in NULLXES_POSITIONING_HOMEPAGE.lower()
    assert "250" in NULLXES_POSITIONING_ENTERPRISE_INTRO


def test_instructions_enterprise_dialogue() -> None:
    text = build_kaira_instructions()
    assert text == KAIRA_INSTRUCTIONS
    assert len(text) < 9000
    assert NULLXES_BRAND_CANONICAL_RU in text
    assert "KAIRA MARIA NULLXES" in text
    assert "Chief Digital Employee" in text
    assert "цифровой сотрудник" in text
    assert "пилот" in text
    assert "возражения" in text.lower() or "просто бот" in text
    assert "Magister Protocol" in text
    assert "eleven_v3" in text
    assert "чем могу помочь" in text
    assert "наллексес" in NULLXES_STT_NORMALIZE_FROM


def test_positioning_not_in_base_instructions() -> None:
    text = build_instructions(KairaMode.PUBLIC)
    assert NULLXES_POSITIONING_HOMEPAGE not in text
    assert NULLXES_POSITIONING_ENTERPRISE_INTRO not in text
    assert NULLXES_POSITIONING_ULTRA_SHORT not in text


def test_opening_brevity() -> None:
    opening = opening_for_mode(KairaMode.PUBLIC)
    assert opening == KAIRA_OPENING
    assert "Кайра Мария" in opening
    assert "NULLXES" in opening
    assert "[confident]" in opening
    assert "Мамочка Кайра" not in opening
    assert "операционная сущность" not in opening.lower()
    assert "чем могу помочь" not in opening.lower()
    assert "Контур активен" not in opening


def test_magister_instructions_differ() -> None:
    public = build_instructions(KairaMode.PUBLIC)
    magister = build_instructions(KairaMode.MAGISTER)
    assert public != magister
    assert "Маг" in magister
    assert "квалификация" not in magister.lower()


def test_sales_dialogue_not_in_operator_mode() -> None:
    operator = build_instructions(KairaMode.OPERATOR)
    assert "квалификация" not in operator.lower()
    assert "возражения" not in operator.lower()
