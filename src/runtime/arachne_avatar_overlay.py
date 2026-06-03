"""Opt-in ARACHNE avatar overlay for KAIRA (dispatch + DataStream audio)."""

from __future__ import annotations

import json
import logging
import os

from livekit import api, rtc
from livekit.agents import AgentSession, JobContext, get_job_context
from livekit.agents.voice.avatar import DataStreamAudioOutput

from services.arachne_inference import inference_configured

logger = logging.getLogger("agent-KAIRA-NULLXES")

DEFAULT_ARACHNE_AVATAR_AGENT_NAME = "KAIRA-ARACHNE-AVATAR"
DEFAULT_ARACHNE_AVATAR_IDENTITY = "kaira-arachne-avatar"
DEFAULT_ARACHNE_AVATAR_PARTICIPANT_NAME = "KAIRA Arachne"
ARACHNE_TTS_SAMPLE_RATE = 24_000


def arachne_avatar_enabled() -> bool:
    return os.getenv("KAIRA_AVATAR_BACKEND", "").strip().lower() == "arachne"


def arachne_avatar_identity() -> str:
    return (
        os.getenv("KAIRA_ARACHNE_AVATAR_IDENTITY", "").strip()
        or DEFAULT_ARACHNE_AVATAR_IDENTITY
    )


def arachne_avatar_agent_name() -> str:
    return (
        os.getenv("KAIRA_ARACHNE_AVATAR_AGENT_NAME", "").strip()
        or DEFAULT_ARACHNE_AVATAR_AGENT_NAME
    )


async def dispatch_arachne_avatar(ctx: JobContext) -> None:
    livekit_url = os.getenv("LIVEKIT_URL", "").strip()
    api_key = os.getenv("LIVEKIT_API_KEY", "").strip()
    api_secret = os.getenv("LIVEKIT_API_SECRET", "").strip()
    if not livekit_url or not api_key or not api_secret:
        raise RuntimeError(
            "LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET required for ARACHNE dispatch"
        )

    kaira_agent_name = os.getenv("KAIRA_AGENT_NAME", "KAIRA-NULLXES").strip()
    job_ctx = get_job_context()
    metadata = json.dumps(
        {
            "paired": kaira_agent_name,
            "kaira_identity": job_ctx.local_participant_identity,
        }
    )

    lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
    try:
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=ctx.room.name,
                agent_name=arachne_avatar_agent_name(),
                metadata=metadata,
            )
        )
        logger.info(
            "ARACHNE avatar dispatch created room=%s agent=%s dispatch_id=%s",
            ctx.room.name,
            arachne_avatar_agent_name(),
            dispatch.id,
        )
    finally:
        await lkapi.aclose()


async def apply_arachne_avatar_overlay(
    ctx: JobContext,
    session: AgentSession,
    *,
    telephony: bool,
) -> bool:
    """
    Enable ARACHNE custom avatar when configured.

    Returns True if overlay applied (caller must skip Anam and disable room audio_output).
    """
    if not arachne_avatar_enabled() or telephony:
        return False

    if not inference_configured():
        logger.error(
            "KAIRA_AVATAR_BACKEND=arachne but inference URL/key missing; "
            "set %s and inference service key",
            "NULLXES_AVATAR_INFERENCE_URL",
        )
        return False

    await dispatch_arachne_avatar(ctx)

    destination = arachne_avatar_identity()
    session.output.audio = DataStreamAudioOutput(
        room=ctx.room,
        destination_identity=destination,
        sample_rate=ARACHNE_TTS_SAMPLE_RATE,
        wait_remote_track=rtc.TrackKind.KIND_VIDEO,
        wait_playback_start=True,
    )
    logger.info(
        "ARACHNE avatar overlay active room=%s destination_identity=%s",
        ctx.room.name,
        destination,
    )
    return True
