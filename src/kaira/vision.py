"""OpenAI Vision helpers for STT+LLM+TTS (Path A)."""

from __future__ import annotations

import base64
import os
from typing import Any

from livekit.agents import llm

DEFAULT_VISION_IMAGE_TOPIC = "images"
DEFAULT_VISION_INFERENCE_SIZE = 768


def vision_enabled() -> bool:
    value = os.getenv("KAIRA_VISION_ENABLED", "disabled").strip().lower()
    return value in ("enabled", "true", "1", "on")


def vision_image_topic() -> str:
    return os.getenv(
        "KAIRA_VISION_IMAGE_TOPIC", DEFAULT_VISION_IMAGE_TOPIC
    ).strip() or (DEFAULT_VISION_IMAGE_TOPIC)


def vision_inference_size() -> tuple[int | None, int | None]:
    width = os.getenv("KAIRA_VISION_INFERENCE_WIDTH", "").strip()
    height = os.getenv("KAIRA_VISION_INFERENCE_HEIGHT", "").strip()
    if width and height:
        return int(width), int(height)
    return DEFAULT_VISION_INFERENCE_SIZE, DEFAULT_VISION_INFERENCE_SIZE


def user_message_text(content: str | list[Any]) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for part in content:
        if isinstance(part, str):
            parts.append(part)
    return " ".join(parts).strip()


def image_content_from_bytes(
    image_bytes: bytes,
    *,
    mime_type: str = "image/png",
) -> llm.ImageContent:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    width, height = vision_inference_size()
    return llm.ImageContent(
        image=f"data:{mime_type};base64,{encoded}",
        inference_width=width,
        inference_height=height,
        mime_type=mime_type,
    )


def image_content_from_screenshot_value(value: str | None) -> llm.ImageContent | None:
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    width, height = vision_inference_size()
    image_ref = (
        raw if raw.startswith("data:") else f"data:image/png;base64,{raw}"
    )
    return llm.ImageContent(
        image=image_ref,
        inference_width=width,
        inference_height=height,
        mime_type="image/png",
    )


def frame_image_content(frame: Any) -> llm.ImageContent:
    width, height = vision_inference_size()
    return llm.ImageContent(
        image=frame,
        inference_width=width,
        inference_height=height,
    )
