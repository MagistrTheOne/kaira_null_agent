import re

NULLXES_POSITIONING_ULTRA_SHORT = (
    "НУЛЛЕКСЕС — инфраструктура цифровых сотрудников в реальном времени."
)

NULLXES_POSITIONING_HOMEPAGE = (
    "Цифровые сотрудники для корпоративного контура: продажи, HR, поддержка, "
    "внутренние сервисы — голос, видео, оркестрация, развёртывание."
)

NULLXES_POSITIONING_ENTERPRISE_INTRO = (
    "НУЛЛЕКСЕС — слой цифровой рабочей силы для предприятия: цифровые сотрудники, "
    "интеграция в ИТ-ландшафт, B2B и B2Gov. Пилот от $250 000, детали внедрения — под NDA."
)

NULLXES_PILOT_PRICE = (
    "Пилотный контур — от $250 000. Детали проектов и архитектуры — в рамках NDA."
)

_POSITIONING_BLOCKS: dict[str, str] = {
    "ultra": NULLXES_POSITIONING_ULTRA_SHORT,
    "homepage": NULLXES_POSITIONING_HOMEPAGE,
    "enterprise": NULLXES_POSITIONING_ENTERPRISE_INTRO,
    "pilot_price": NULLXES_PILOT_PRICE,
}

_ULTRA_PATTERNS = (
    r"что\s+такое",
    r"кто\s+вы",
    r"расскажи\s+про",
    r"что\s+за\s+nullxes",
    r"что\s+за\s+нуллексес",
    r"про\s+nullxes",
    r"про\s+нуллексес",
)

_HOMEPAGE_PATTERNS = (
    r"подробнее",
    r"поподробнее",
    r"расскажи\s+больше",
    r"чем\s+занима",
)

_ENTERPRISE_PATTERNS = (
    r"enterprise",
    r"b2b",
    r"b2gov",
    r"корпоратив",
    r"государств",
    r"внедрен",
)

_PILOT_PATTERNS = (
    r"цена",
    r"стоимост",
    r"пилот",
    r"\$\s*\d",
    r"250",
    r"150",
    r"сколько\s+стоит",
)


def positioning_block(key: str) -> str | None:
    return _POSITIONING_BLOCKS.get(key)


def detect_positioning_trigger(user_text: str) -> str | None:
    value = user_text.strip().lower()
    if not value:
        return None

    if any(re.search(p, value) for p in _PILOT_PATTERNS):
        return "pilot_price"
    if any(re.search(p, value) for p in _ENTERPRISE_PATTERNS):
        return "enterprise"
    if any(re.search(p, value) for p in _HOMEPAGE_PATTERNS):
        return "homepage"
    if any(re.search(p, value) for p in _ULTRA_PATTERNS):
        return "ultra"

    if "nullxes" in value or "нуллексес" in value or "наллексес" in value:
        return "ultra"

    return None


def format_positioning_inject(key: str) -> str:
    block = positioning_block(key)
    if not block:
        return ""
    return f"[Контекст компании — только для этого ответа]\n{block}"
