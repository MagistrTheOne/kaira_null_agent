"""Accumulate LiveKit AudioFrame segments and encode PCM16 mono 16 kHz for ARACHNE."""

from __future__ import annotations

import base64
from collections.abc import Iterable

import numpy as np
from livekit import rtc
from livekit.agents.voice.avatar import AudioSegmentEnd

ARACHNE_AUDIO_SAMPLE_RATE = 16_000
ARACHNE_AUDIO_CHANNELS = 1


def _resample_mono_int16(
    samples: np.ndarray,
    *,
    source_rate: int,
    target_rate: int,
) -> np.ndarray:
    if source_rate == target_rate or samples.size == 0:
        return samples
    target_len = max(1, int(round(samples.size * target_rate / source_rate)))
    x_old = np.arange(samples.size, dtype=np.float64)
    x_new = np.linspace(0, samples.size - 1, num=target_len)
    resampled = np.interp(x_new, x_old, samples.astype(np.float64))
    return np.clip(resampled, -32768, 32767).astype(np.int16)


def _frame_to_pcm16_mono(
    frame: rtc.AudioFrame,
    *,
    target_rate: int = ARACHNE_AUDIO_SAMPLE_RATE,
) -> bytes:
    """Convert one AudioFrame to PCM16 mono at target_rate."""
    samples = np.frombuffer(bytes(frame.data), dtype=np.int16)
    channels = frame.num_channels
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1).astype(np.int16)

    if frame.sample_rate != target_rate:
        samples = _resample_mono_int16(
            samples,
            source_rate=frame.sample_rate,
            target_rate=target_rate,
        )
    return samples.tobytes()


def frames_to_pcm16_bytes(frames: Iterable[rtc.AudioFrame]) -> bytes:
    chunks: list[bytes] = []
    for frame in frames:
        if isinstance(frame, AudioSegmentEnd):
            continue
        chunks.append(_frame_to_pcm16_mono(frame))
    return b"".join(chunks)


def frames_to_pcm16_base64(frames: Iterable[rtc.AudioFrame]) -> str:
    return base64.b64encode(frames_to_pcm16_bytes(frames)).decode("ascii")


def pcm16_duration_sec(
    pcm_bytes: bytes, sample_rate: int = ARACHNE_AUDIO_SAMPLE_RATE
) -> float:
    if not pcm_bytes:
        return 0.0
    samples = len(pcm_bytes) // 2
    return samples / sample_rate
