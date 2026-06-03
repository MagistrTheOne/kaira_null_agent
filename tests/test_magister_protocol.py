from services.magister_protocol import (
    activate_magister_protocol,
    deactivate_magister_protocol,
    is_magister_activation,
)


def test_magister_activation_accepts_configured_phrase(monkeypatch) -> None:
    monkeypatch.setenv(
        "KAIRA_MAGISTER_PHRASE",
        "Кайра, Маг на связи, активируй секретный протокол",
    )

    result = activate_magister_protocol(
        "Кайра, Маг на связи, активируй секретный протокол"
    )

    assert result.matched is True
    assert result.mode == "magister"


def test_magister_activation_tolerates_punctuation(monkeypatch) -> None:
    monkeypatch.setenv(
        "KAIRA_MAGISTER_PHRASE",
        "Кайра, Маг на связи, активируй секретный протокол",
    )

    assert is_magister_activation("Кайра! Маг на связи. Активируй секретный протокол.")


def test_magister_activation_rejects_partial_phrase(monkeypatch) -> None:
    monkeypatch.setenv(
        "KAIRA_MAGISTER_PHRASE",
        "Кайра, Маг на связи, активируй секретный протокол",
    )

    result = activate_magister_protocol("Кайра, активируй протокол")

    assert result.matched is False
    assert result.mode == "public"


def test_magister_deactivation_accepts_configured_phrase(monkeypatch) -> None:
    monkeypatch.setenv(
        "KAIRA_MAGISTER_DEACTIVATE_PHRASE",
        "Кайра, закрой секретный протокол",
    )

    result = deactivate_magister_protocol("Кайра, закрой секретный протокол")

    assert result.matched is True
    assert result.mode == "public"
