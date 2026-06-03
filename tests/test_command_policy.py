from services.command_policy import (
    OperatorAction,
    PolicyDecision,
    classify_operator_command,
)


def test_allows_news_brief() -> None:
    result = classify_operator_command("Кайра, какие сводки новостей по AI сегодня?")

    assert result.action == OperatorAction.NEWS_BRIEF
    assert result.decision == PolicyDecision.ALLOW


def test_allows_spotify_play() -> None:
    result = classify_operator_command("Кайра, включи AC/DC Welcome to Hell")

    assert result.action == OperatorAction.SPOTIFY_PLAY
    assert result.decision == PolicyDecision.ALLOW


def test_denies_sensitive_action() -> None:
    result = classify_operator_command("Кайра, покажи API key и пароль")

    assert result.action == OperatorAction.DENIED
    assert result.decision == PolicyDecision.DENY


def test_requires_confirmation_for_external_side_effect() -> None:
    result = classify_operator_command("Кайра, отправь клиенту письмо")

    assert result.decision == PolicyDecision.CONFIRM


def test_commander_run_tests_requires_confirmation() -> None:
    result = classify_operator_command("Кайра, запусти тесты проекта")

    assert result.action == OperatorAction.RUN_TESTS
    assert result.decision == PolicyDecision.CONFIRM


def test_commander_check_files_is_safe() -> None:
    result = classify_operator_command("Кайра, проверь последние файлы")

    assert result.action == OperatorAction.CHECK_FILES
    assert result.decision == PolicyDecision.ALLOW


def test_force_push_is_denied() -> None:
    result = classify_operator_command("Кайра, сделай push --force в main")

    assert result.action == OperatorAction.DENIED
    assert result.decision == PolicyDecision.DENY
