"""Portrait loading and rgb24 frame conversion for LiveKit video."""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import numpy as np
from livekit import rtc

logger = logging.getLogger(__name__)

DEFAULT_PORTRAIT_PATH = "assets/kaira_face.png"


def default_portrait_path() -> Path:
    override = os.getenv("KAIRA_ARACHNE_PORTRAIT_PATH", "").strip()
    if override:
        return Path(override)
    root = Path(__file__).resolve().parents[2]
    return root / DEFAULT_PORTRAIT_PATH


def load_portrait_base64(path: Path | None = None) -> str:
    """Read PNG portrait and return raw base64 (no data-URL prefix)."""
    portrait_path = path or default_portrait_path()
    if not portrait_path.is_file():
        raise FileNotFoundError(f"ARACHNE portrait not found: {portrait_path}")
    raw = portrait_path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        logger.warning("portrait is not a PNG header path=%s", portrait_path)
    return base64.b64encode(raw).decode("ascii")


def rgb24_bytes_to_video_frame(
    data: bytes,
    width: int,
    height: int,
) -> rtc.VideoFrame:
    """Convert worker rgb24 bytes to RGBA VideoFrame for LiveKit."""
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid frame dimensions: {width}x{height}")
    expected = width * height * 3
    if len(data) < expected:
        raise ValueError(
            f"rgb24 buffer too short: got {len(data)} expected {expected}"
        )
    rgb = np.frombuffer(data[:expected], dtype=np.uint8).reshape((height, width, 3))
    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = rgb
    rgba[:, :, 3] = 255
    return rtc.VideoFrame(
        width,
        height,
        rtc.VideoBufferType.RGBA,
        rgba.tobytes(),
    )


def decode_frame_payload(
    *,
    encoding: str,
    data_b64: str,
    width: int,
    height: int,
) -> rtc.VideoFrame:
    raw = base64.b64decode(data_b64)
    enc = (encoding or "").lower()
    if enc == "rgb24_base64" or enc == "rgb24":
        return rgb24_bytes_to_video_frame(raw, width, height)
    raise ValueError(f"unsupported avatar frame encoding: {encoding}")
