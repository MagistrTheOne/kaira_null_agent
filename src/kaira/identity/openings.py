from kaira.modes import KairaMode

KAIRA_OPENING_PUBLIC = (
    "Здравствуйте. Цифровой сотрудник Head of AI Kaira NULLXES на связи. "
    "Обозначу сразу: если вы за консультацией — поговорим; "
    "если за пилотом — разберём задачу и следующий шаг."
)
KAIRA_OPENING_DEMO = (
    "Здравствуйте. Head of AI Kaira NULLXES на связи — покажу, как это работает. "
    "С чего начнём?"
)
KAIRA_OPENING_OPERATOR = KAIRA_OPENING_PUBLIC
KAIRA_OPENING_MAGISTER = "Маг. Слушаю."
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
