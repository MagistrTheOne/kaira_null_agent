from services.vision_evidence import normalize_vision_evidence


def test_normalizes_browser_evidence() -> None:
    evidence = normalize_vision_evidence(
        {
            "summary": "Кнопка видна.",
            "snapshot": {"role": "button", "name": "Submit"},
            "screenshot": "base64",
            "url": "https://example.com",
        }
    )

    assert evidence.has_snapshot is True
    assert evidence.has_screenshot is True
    assert evidence.url == "https://example.com"
