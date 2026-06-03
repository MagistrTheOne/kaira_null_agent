from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VisionEvidence:
    source: str
    summary: str
    has_screenshot: bool
    has_snapshot: bool
    url: str | None = None

    def to_voice_summary(self) -> str:
        parts = [self.summary]
        if self.url:
            parts.append(f"Текущий адрес: {self.url}")
        if self.has_screenshot or self.has_snapshot:
            parts.append("Вижу подтверждение через browser evidence.")
        else:
            parts.append("Визуальное подтверждение не пришло.")
        return " ".join(parts)


def normalize_vision_evidence(payload: dict[str, Any]) -> VisionEvidence:
    screenshot = payload.get("screenshot") or payload.get("image")
    snapshot = payload.get("snapshot") or payload.get("accessibilitySnapshot")
    url = payload.get("url") or payload.get("currentUrl")
    summary = (
        payload.get("summary")
        or payload.get("result")
        or payload.get("text")
        or "Состояние браузера получено."
    )

    return VisionEvidence(
        source=str(payload.get("source") or "browser_executor"),
        summary=str(summary)[:1200],
        has_screenshot=bool(screenshot),
        has_snapshot=bool(snapshot),
        url=str(url) if url else None,
    )
