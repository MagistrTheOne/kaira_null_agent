import base64

import pytest

from kaira.vision import (
    image_content_from_bytes,
    image_content_from_screenshot_value,
    user_message_text,
    vision_enabled,
    vision_image_topic,
)


def test_vision_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KAIRA_VISION_ENABLED", raising=False)
    assert vision_enabled() is False


def test_vision_enabled_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KAIRA_VISION_ENABLED", "enabled")
    assert vision_enabled() is True
    monkeypatch.setenv("KAIRA_VISION_IMAGE_TOPIC", "kaira-images")
    assert vision_image_topic() == "kaira-images"


def test_user_message_text_multimodal() -> None:
    text = user_message_text(["Привет", "мир"])
    assert text == "Привет мир"


def test_image_content_from_bytes() -> None:
    raw = b"\x89PNG\r\n\x1a\n"
    content = image_content_from_bytes(raw, mime_type="image/png")
    assert content.type == "image_content"
    assert content.image.startswith("data:image/png;base64,")
    assert base64.b64decode(content.image.split(",", 1)[1]) == raw


def test_image_content_from_screenshot_base64() -> None:
    payload = base64.b64encode(b"fakepng").decode("ascii")
    content = image_content_from_screenshot_value(payload)
    assert content is not None
    assert "base64," in str(content.image)


def test_image_content_from_screenshot_data_url() -> None:
    data_url = "data:image/jpeg;base64,abc"
    content = image_content_from_screenshot_value(data_url)
    assert content is not None
    assert content.image == data_url


def test_image_content_from_screenshot_empty() -> None:
    assert image_content_from_screenshot_value(None) is None
    assert image_content_from_screenshot_value("   ") is None
