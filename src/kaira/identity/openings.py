from kaira.modes import KairaMode

KAIRA_OPENING_PUBLIC = (
    "[confident] Добро пожаловать в NULLXES. "
    "Я Кайра Мария, Chief Digital Employee компании. "
    "Если вы за консультацией — поговорим… если за пилотом — разберём задачу и следующий шаг."
)
KAIRA_OPENING_DEMO = (
    "[thoughtful] Здравствуйте. Кайра Мария из NULLXES на связи — покажу, как это работает на практике. "
    "С чего начнём?"
)
KAIRA_OPENING_OPERATOR = (
    "[confident] На связи Кайра Мария, NULLXES. "
    "Готова разобрать задачу и предложить следующий шаг."
)
KAIRA_OPENING_MAGISTER = "[curious] Маг. Слушаю."
KAIRA_OPENING_CRITICAL = "На связи."

# Back-compat alias
KAIRA_OPENING = KAIRA_OPENING_PUBLIC

_OPENINGS: dict[KairaMode, str] = {
    KairaMode.PUBLIC: KAIRA_OPENING_PUBLIC,
    KairaMode.DEMO: KAIRA_OPENING_DEMO,
    KairaMode.OPERATOR: KAIRA_OPENING_OPERATOR,
    KairaMode.MAGISTER: KAIRA_OPENING_MAGISTER,
    KairaMode.CRITICAL: KAIRA_OPENING_CRITICAL,
}


def opening_for_mode(mode: KairaMode) -> str:
    return _OPENINGS.get(mode, KAIRA_OPENING_PUBLIC)
