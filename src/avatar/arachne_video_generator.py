"""ARACHNE DiT VideoGenerator for LiveKit AvatarRunner."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator

import aiohttp
from livekit import rtc
from livekit.agents.utils.aio.channel import Chan, ChanEmpty
from livekit.agents.voice.avatar import AudioSegmentEnd, VideoGenerator

from avatar.audio_buffer import frames_to_pcm16_base64
from avatar.frame_codec import decode_frame_payload, load_portrait_base64
from services.arachne_inference import stream_avatar_frames

logger = logging.getLogger(__name__)


class ArachneVideoGenerator(VideoGenerator):
    def __init__(
        self,
        *,
        session_id: str,
        portrait_b64: str | None = None,
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._session_id = session_id
        self._portrait_b64 = portrait_b64 or load_portrait_base64()
        self._http_session = http_session

        self._segment_frames: list[rtc.AudioFrame] = []
        self._out_ch = Chan[rtc.VideoFrame | rtc.AudioFrame | AudioSegmentEnd]()
        self._inference_tasks: set[asyncio.Task[None]] = set()
        self._closed = False

        self._resolution = os.getenv("KAIRA_ARACHNE_RESOLUTION", "480p").strip() or "480p"
        try:
            self._inference_steps = max(
                1, int(os.getenv("KAIRA_ARACHNE_INFERENCE_STEPS", "8"))
            )
        except ValueError:
            self._inference_steps = 8
        self._prompt = os.getenv("KAIRA_ARACHNE_PROMPT", "").strip()
        self._negative_prompt = os.getenv("KAIRA_ARACHNE_NEGATIVE_PROMPT", "").strip()
        runtime = os.getenv("KAIRA_ARACHNE_RUNTIME_PROFILE", "").strip()
        self._runtime_profile = runtime or None

    async def push_audio(self, frame: rtc.AudioFrame | AudioSegmentEnd) -> None:
        if self._closed:
            return
        if isinstance(frame, AudioSegmentEnd):
            segment = self._segment_frames
            self._segment_frames = []
            for audio_frame in segment:
                await self._out_ch.send(audio_frame)
            if segment:
                task = asyncio.create_task(self._run_inference(segment))
                self._inference_tasks.add(task)
                task.add_done_callback(self._inference_tasks.discard)
            else:
                await self._out_ch.send(AudioSegmentEnd())
            return
        self._segment_frames.append(frame)

    async def clear_buffer(self) -> None:
        self._segment_frames.clear()
        for task in list(self._inference_tasks):
            task.cancel()
        self._inference_tasks.clear()
        while not self._out_ch.empty():
            try:
                self._out_ch.recv_nowait()
            except ChanEmpty:
                break

    def __aiter__(
        self,
    ) -> AsyncIterator[rtc.VideoFrame | rtc.AudioFrame | AudioSegmentEnd]:
        return self._out_ch

    async def _run_inference(self, segment: list[rtc.AudioFrame]) -> None:
        try:
            audio_b64 = frames_to_pcm16_base64(segment)
            if not audio_b64:
                return
            async for payload in stream_avatar_frames(
                self._http_session,
                session_id=self._session_id,
                image_base64=self._portrait_b64,
                audio_pcm16_base64=audio_b64,
                prompt=self._prompt,
                negative_prompt=self._negative_prompt,
                num_inference_steps=self._inference_steps,
                resolution=self._resolution,
                engine="arachne",
                runtime_profile=self._runtime_profile,
            ):
                if payload.encoding not in ("rgb24_base64", "rgb24"):
                    logger.warning(
                        "skipping non-rgb24 frame encoding=%s seq=%s",
                        payload.encoding,
                        payload.seq,
                    )
                    continue
                if payload.width <= 0 or payload.height <= 0:
                    logger.warning(
                        "skipping frame with invalid size seq=%s", payload.seq
                    )
                    continue
                video_frame = decode_frame_payload(
                    encoding=payload.encoding,
                    data_b64=payload.data,
                    width=payload.width,
                    height=payload.height,
                )
                await self._out_ch.send(video_frame)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "ARACHNE inference failed session_id=%s", self._session_id
            )
        finally:
            await self._out_ch.send(AudioSegmentEnd())

    async def aclose(self) -> None:
        self._closed = True
        await self.clear_buffer()
        self._out_ch.close()
