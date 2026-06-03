"""Room-level video frame buffering for OpenAI Vision (Path A)."""

from __future__ import annotations

import asyncio
import logging

from livekit import rtc
from livekit.agents import JobContext

from kaira.vision import vision_enabled
from runtime.room_memory import KairaRoomMemory

logger = logging.getLogger("agent-KAIRA-NULLXES")

_VISION_STREAM_KEY = "kaira_vision_video"


def install_vision_video(ctx: JobContext, memory: KairaRoomMemory) -> None:
    if not vision_enabled():
        return
    if ctx.proc.userdata.get(_VISION_STREAM_KEY):
        return

    room = ctx.room
    tasks: set[asyncio.Task] = set()
    stream_holder: dict[str, rtc.VideoStream | None] = {"stream": None}

    def _attach_video_track(track: rtc.Track) -> None:
        if track.kind != rtc.TrackKind.KIND_VIDEO:
            return

        existing = stream_holder["stream"]
        if existing is not None:
            old = existing
            stream_holder["stream"] = None
            close_task = asyncio.create_task(old.aclose())
            tasks.add(close_task)
            close_task.add_done_callback(tasks.discard)

        stream = rtc.VideoStream(track)
        stream_holder["stream"] = stream

        async def read_stream() -> None:
            try:
                async for event in stream:
                    memory.latest_video_frame = event.frame
            except Exception:
                logger.exception("KAIRA vision video stream ended with error")

        task = asyncio.create_task(read_stream())
        tasks.add(task)
        task.add_done_callback(tasks.discard)
        logger.info("KAIRA vision video stream attached")

    for participant in room.remote_participants.values():
        for publication in participant.track_publications.values():
            if publication.track and publication.track.kind == rtc.TrackKind.KIND_VIDEO:
                _attach_video_track(publication.track)
                break

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        del publication, participant
        _attach_video_track(track)

    ctx.proc.userdata[_VISION_STREAM_KEY] = True
    logger.info("KAIRA vision video input hooks installed for room %s", room.name)
