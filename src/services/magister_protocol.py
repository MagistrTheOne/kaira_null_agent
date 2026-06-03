import os
import re
from dataclasses import dataclass

DEFAULT_MAGISTER_PHRASE = "Кайра, Маг на связи, активируй секретный протокол"
DEFAULT_MAGISTER_DEACTIVATE_PHRASE = "Кайра, закрой секретный протокол"


@dataclass(frozen=True)
class MagisterProtocolResult:
    matched: bool
    mode: str
    response: str


def _normalize_phrase(value: str) -> str:
    lowered = value.casefold().replace("ё", "е")
    return re.sub(r"[^a-zа-я0-9]+", " ", lowered).strip()


def magister_phrase() -> str:
    return os.getenv("KAIRA_MAGISTER_PHRASE", DEFAULT_MAGISTER_PHRASE).strip()


def magister_deactivate_phrase() -> str:
    return os.getenv(
        "KAIRA_MAGISTER_DEACTIVATE_PHRASE",
        DEFAULT_MAGISTER_DEACTIVATE_PHRASE,
    ).strip()


def is_magister_activation(command: str) -> bool:
    return _normalize_phrase(command) == _normalize_phrase(magister_phrase())


def is_magister_deactivation(command: str) -> bool:
    return _normalize_phrase(command) == _normalize_phrase(magister_deactivate_phrase())


def activate_magister_protocol(command: str) -> MagisterProtocolResult:
    if not is_magister_activation(command):
        return MagisterProtocolResult(
            matched=False,
            mode="public",
            response="Секретный протокол не активирован. Фраза не совпала.",
        )

    return MagisterProtocolResult(
        matched=True,
        mode="magister",
        response="Маг на связи. Секретный протокол активирован. Я убрала шум и держу контур.",
    )


def deactivate_magister_protocol(command: str) -> MagisterProtocolResult:
    if not is_magister_deactivation(command):
        return MagisterProtocolResult(
            matched=False,
            mode="magister",
            response="Секретный протокол остаётся активным. Команда закрытия не совпала.",
        )

    return MagisterProtocolResult(
        matched=True,
        mode="public",
        response="Протокол закрыт. Возвращаюсь в публичный executive-режим.",
    )
