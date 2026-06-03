"""LiveKit Cloud entrypoint for the ARACHNE custom avatar worker (CPU)."""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from livekit.agents import AgentServer, JobContext, JobRequest, cli
from livekit.agents.voice.avatar import (
    AvatarOptions,
    AvatarRunner,
    DataStreamAudioReceiver,
)

from avatar.arachne_video_generator import ArachneVideoGenerator

load_dotenv(".env.local")

logger = logging.getLogger("agent-KAIRA-ARACHNE-AVATAR")

DEFAULT_AGENT_NAME = "KAIRA-ARACHNE-AVATAR"
DEFAULT_AVATAR_IDENTITY = "kaira-arachne-avatar"
DEFAULT_AVATAR_NAME = "KAIRA Arachne"

VIDEO_WIDTH = 854
VIDEO_HEIGHT = 480
VIDEO_FPS = 25.0
AUDIO_SAMPLE_RATE = 24_000
AUDIO_CHANNELS = 1


def _avatar_agent_name() -> str:
    return os.getenv("KAIRA_ARACHNE_AVATAR_AGENT_NAME", "").strip() or DEFAULT_AGENT_NAME


def _avatar_identity() -> str:
    return os.getenv("KAIRA_ARACHNE_AVATAR_IDENTITY", "").strip() or DEFAULT_AVATAR_IDENTITY


def _avatar_participant_name() -> str:
    return (
        os.getenv("KAIRA_ARACHNE_AVATAR_PARTICIPANT_NAME", "").strip()
        or DEFAULT_AVATAR_NAME
    )


def _kaira_sender_identity(ctx: JobContext) -> str | None:
    explicit = os.getenv("KAIRA_AGENT_IDENTITY", "").strip()
    if explicit:
        return explicit
    metadata = (ctx.job.metadata or "").strip()
    if not metadata:
        return None
    try:
        parsed = json.loads(metadata)
    except json.JSONDecodeError:
        logger.warning("invalid dispatch metadata for ARACHNE avatar worker")
        return None
    value = parsed.get("kaira_identity")
    return value if isinstance(value, str) and value.strip() else None


async def _accept_arachne_job(req: JobRequest) -> None:
    await req.accept(
        name=_avatar_participant_name(),
        identity=_avatar_identity(),
    )


server = AgentServer()


@server.rtc_session(agent_name=_avatar_agent_name(), on_request=_accept_arachne_job)
async def arachne_avatar_session(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": _avatar_agent_name(),
    }

    await ctx.connect()

    sender_identity = _kaira_sender_identity(ctx)
    audio_recv = DataStreamAudioReceiver(
        ctx.room,
        sender_identity=sender_identity,
    )
    video_gen = ArachneVideoGenerator(session_id=ctx.room.name)
    runner = AvatarRunner(
        ctx.room,
        audio_recv=audio_recv,
        video_gen=video_gen,
        options=AvatarOptions(
            video_width=VIDEO_WIDTH,
            video_height=VIDEO_HEIGHT,
            video_fps=VIDEO_FPS,
            audio_sample_rate=AUDIO_SAMPLE_RATE,
            audio_channels=AUDIO_CHANNELS,
        ),
    )

    try:
        await runner.start()
        await runner.wait_for_complete()
    finally:
        await video_gen.aclose()
        await runner.aclose()


if __name__ == "__main__":
    cli.run_app(server)
