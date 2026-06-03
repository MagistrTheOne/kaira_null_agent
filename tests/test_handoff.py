from runtime.session_hooks import should_handoff_to_operator


def test_handoff_when_operator_enabled() -> None:
    assert should_handoff_to_operator(
        "Кайра, найди новости по AI", operator_enabled=True
    )


def test_no_handoff_when_disabled() -> None:
    assert not should_handoff_to_operator(
        "Кайра, найди новости", operator_enabled=False
    )


def test_no_handoff_on_greeting() -> None:
    assert not should_handoff_to_operator("Привет", operator_enabled=True)
