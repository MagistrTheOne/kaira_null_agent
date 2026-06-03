import json
import logging
import time

from livekit.agents import JobContext

from runtime.room_memory import KairaRoomMemory

logger = logging.getLogger("agent-KAIRA-NULLXES")

KAIRA_STATE_TOPIC = "kaira.state"
KAIRA_ROOM_TOPIC = "kaira.room"


async def publish_room_event(
    ctx: JobContext,
    *,
    agent_name: str,
    event: str,
    payload: dict[str, object],
) -> None:
    message = {
        "event": event,
        "agent": agent_name,
        "timestampMs": int(time.time() * 1000),
        **payload,
    }
    try:
        await ctx.room.local_participant.publish_data(
            json.dumps(message, ensure_ascii=False),
            reliable=True,
            topic=KAIRA_ROOM_TOPIC,
        )
    except Exception:
        logger.exception("failed to publish KAIRA room event: %s", event)


async def publish_kaira_state(
    ctx: JobContext,
    state: str,
    *,
    agent_name: str,
    reason: str | None = None,
    memory: KairaRoomMemory | None = None,
) -> None:
    payload: dict[str, object] = {
        "state": state,
        "agent": agent_name,
        "timestampMs": int(time.time() * 1000),
    }
    if reason:
        payload["reason"] = reason
    if memory:
        payload["room"] = memory.snapshot()

    try:
        await ctx.room.local_participant.publish_data(
            json.dumps(payload, ensure_ascii=False),
            reliable=True,
            topic=KAIRA_STATE_TOPIC,
        )
    except Exception:
        logger.exception("failed to publish KAIRA state: %s", state)
