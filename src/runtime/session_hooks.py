import asyncio
import logging
import re
from collections.abc import Callable

from livekit import rtc
from livekit.agents import AgentSession, JobContext
from livekit.agents.voice.events import UserInputTranscribedEvent

from kaira.identity.positioning import (
    detect_positioning_trigger,
    format_positioning_inject,
)
from kaira.modes import KairaMode
from kaira.session_context import KairaSessionContext
from runtime.room_memory import KairaRoomMemory
from runtime.state_publish import publish_kaira_state, publish_room_event

logger = logging.getLogger("agent-KAIRA-NULLXES")

_BACKGROUND_TASKS: set[asyncio.Task] = set()

_OPERATOR_HANDOFF_PATTERNS = (
    r"найди",
    r"поищи",
    r"новост",
    r"сводк",
    r"гугл",
    r"google",
    r"компан",
    r"что\s+известно",
    r"scrape",
    r"соскрейп",
    r"spotify",
    r"спотиф",
    r"браузер",
    r"открой\s+сайт",
)


def schedule_background(coro) -> None:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)

    def on_done(done: asyncio.Task) -> None:
        _BACKGROUND_TASKS.discard(done)
        try:
            done.result()
        except Exception:
            logger.exception("KAIRA background task failed")

    task.add_done_callback(on_done)


def _normalise_agent_state(raw_state: object) -> str:
    value = str(raw_state).split(".")[-1].lower()
    if value in {"speaking"}:
        return "speaking"
    if value in {"thinking", "generating"}:
        return "thinking"
    if value in {"listening"}:
        return "listening"
    return "idle"


def should_handoff_to_operator(utterance: str, *, operator_enabled: bool) -> bool:
    if not operator_enabled:
        return False
    value = utterance.strip().lower()
    return any(re.search(pattern, value) for pattern in _OPERATOR_HANDOFF_PATTERNS)


def install_session_state_events(
    ctx: JobContext,
    session: AgentSession,
    memory: KairaRoomMemory,
    *,
    agent_name: str,
) -> None:
    @session.on("agent_state_changed")
    def on_agent_state_changed(event):
        state = _normalise_agent_state(event.new_state)
        logger.info("KAIRA state changed: %s -> %s", event.old_state, event.new_state)
        schedule_background(
            publish_kaira_state(
                ctx,
                state,
                agent_name=agent_name,
                reason="agent_state_changed",
                memory=memory,
            )
        )

    @session.on("user_state_changed")
    def on_user_state_changed(event):
        logger.info("user state changed: %s -> %s", event.old_state, event.new_state)
        if str(event.new_state).split(".")[-1].lower() == "speaking":
            schedule_background(
                publish_kaira_state(
                    ctx,
                    "listening",
                    agent_name=agent_name,
                    reason="user_speaking",
                    memory=memory,
                )
            )

    @session.on("speech_created")
    def on_speech_created(event):
        schedule_background(
            publish_kaira_state(
                ctx,
                "thinking",
                agent_name=agent_name,
                reason=f"speech_created:{event.source}",
                memory=memory,
            )
        )

    @session.on("overlapping_speech")
    def on_overlapping_speech(event):
        logger.info("overlapping speech detected: %s", event)
        schedule_background(
            publish_room_event(
                ctx,
                agent_name=agent_name,
                event="overlapping_speech",
                payload={"room": memory.snapshot()},
            )
        )

    @session.on("agent_false_interruption")
    def on_agent_false_interruption(event):
        logger.info("agent false interruption: resumed=%s", event.resumed)
        schedule_background(
            publish_room_event(
                ctx,
                agent_name=agent_name,
                event="agent_false_interruption",
                payload={"resumed": event.resumed, "room": memory.snapshot()},
            )
        )


def install_room_awareness(
    ctx: JobContext,
    memory: KairaRoomMemory,
    *,
    agent_name: str,
) -> None:
    for participant in ctx.room.remote_participants.values():
        memory.upsert_participant(participant.identity, participant.name)

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        memory.upsert_participant(participant.identity, participant.name)
        schedule_background(
            publish_room_event(
                ctx,
                agent_name=agent_name,
                event="participant_connected",
                payload={
                    "participant": participant.identity,
                    "name": participant.name,
                    "room": memory.snapshot(),
                },
            )
        )

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        memory.remove_participant(participant.identity)
        schedule_background(
            publish_room_event(
                ctx,
                agent_name=agent_name,
                event="participant_disconnected",
                payload={
                    "participant": participant.identity,
                    "room": memory.snapshot(),
                },
            )
        )

    @ctx.room.on("active_speakers_changed")
    def on_active_speakers_changed(speakers: list[rtc.Participant]):
        identities = [speaker.identity for speaker in speakers]
        memory.mark_active_speakers(identities)
        schedule_background(
            publish_room_event(
                ctx,
                agent_name=agent_name,
                event="active_speakers_changed",
                payload={
                    "activeSpeakers": identities,
                    "room": memory.snapshot(),
                },
            )
        )


def install_positioning_and_handoff_hooks(
    session: AgentSession,
    kaira_ctx: KairaSessionContext,
    memory: KairaRoomMemory,
    *,
    handoff_factory: Callable[[], object] | None = None,
) -> None:
    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: UserInputTranscribedEvent) -> None:
        if not event.is_final:
            return

        utterance = event.transcript.strip()
        if not utterance:
            return

        kaira_ctx.last_user_utterance = utterance
        memory.note_user_topic(utterance)

        positioning_key = detect_positioning_trigger(utterance)
        if (
            positioning_key
            and positioning_key not in kaira_ctx.injected_positioning_keys
        ):
            kaira_ctx.injected_positioning_keys.add(positioning_key)
            inject_text = format_positioning_inject(positioning_key)
            if inject_text:
                logger.info("positioning inject: %s", positioning_key)

        if (
            handoff_factory is not None
            and kaira_ctx.operator_enabled
            and kaira_ctx.mode in {KairaMode.PUBLIC, KairaMode.DEMO}
            and should_handoff_to_operator(utterance, operator_enabled=True)
        ):
            logger.info("handoff to operator agent")
            kaira_ctx.mode = KairaMode.OPERATOR
            session.update_agent(handoff_factory())
