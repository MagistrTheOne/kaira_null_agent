import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
)
from livekit.plugins import ai_coustics, anam, deepgram, elevenlabs, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from agents.kaira_operator import create_operator_agent
from agents.kaira_public import create_public_agent
from kaira.modes import KairaMode
from kaira.session_context import KairaSessionContext
from kaira.vision import vision_enabled
from runtime.room_memory import KairaRoomMemory
from runtime.session_hooks import (
    install_positioning_and_handoff_hooks,
    install_room_awareness,
    install_session_state_events,
)
from runtime.state_publish import publish_kaira_state
from runtime.telephony import is_telephony_room
from runtime.vision_input import install_vision_video
from services.firecrawl import firecrawl_available

logger = logging.getLogger("agent-KAIRA-NULLXES")

load_dotenv(".env.local")

KAIRA_AGENT_NAME = os.getenv("KAIRA_AGENT_NAME", "KAIRA-NULLXES")

DEFAULT_ELEVENLABS_VOICE_ID = "oAkyDC87lsRvTg9MvKDG"


def operator_mode_enabled() -> bool:
    value = os.getenv("KAIRA_OPERATOR_MODE", "disabled").strip().lower()
    return value in ("enabled", "true", "1", "on")


if operator_mode_enabled():
    logger.info(
        "operator contour enabled firecrawl=%s tavily=%s browser=%s",
        firecrawl_available(),
        bool(os.getenv("TAVILY_API_KEY", "").strip()),
        os.getenv("KAIRA_BROWSER_EXECUTOR", "disabled"),
    )


def build_kaira_tts() -> elevenlabs.TTS:
    return elevenlabs.TTS(
        model=os.getenv("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2"),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID),
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        language=os.getenv("ELEVENLABS_LANGUAGE", "ru"),
    )


def build_kaira_llm() -> openai.LLM:
    llm_kwargs: dict[str, object] = {
        "model": os.getenv("KAIRA_LLM_MODEL", "gpt-4.1-mini"),
    }
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if api_key:
        llm_kwargs["api_key"] = api_key
    if base_url:
        llm_kwargs["base_url"] = base_url
    return openai.LLM(**llm_kwargs)


def create_kaira_context() -> KairaSessionContext:
    mode = KairaMode.OPERATOR if operator_mode_enabled() else KairaMode.PUBLIC
    return KairaSessionContext(mode=mode, operator_enabled=operator_mode_enabled())


def create_initial_agent(
    kaira_ctx: KairaSessionContext,
    memory: KairaRoomMemory,
):
    if kaira_ctx.mode == KairaMode.OPERATOR:
        return create_operator_agent(kaira_ctx, memory)
    return create_public_agent(kaira_ctx, memory)


# Backward compatibility for tests and imports
from agents.kaira_public import KairaPublicAgent

KairaAgent = KairaPublicAgent

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name=KAIRA_AGENT_NAME)
async def kaira_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": KAIRA_AGENT_NAME,
    }

    memory = KairaRoomMemory(room_name=ctx.room.name)
    kaira_ctx = create_kaira_context()

    install_room_awareness(ctx, memory, agent_name=KAIRA_AGENT_NAME)
    install_vision_video(ctx, memory)
    if vision_enabled():
        logger.info(
            "KAIRA vision enabled model=%s video_input=on",
            os.getenv("KAIRA_LLM_MODEL", "gpt-4.1-mini"),
        )
    await publish_kaira_state(
        ctx,
        "idle",
        agent_name=KAIRA_AGENT_NAME,
        reason="session_initializing",
        memory=memory,
    )

    session = AgentSession(
        stt=deepgram.STT(
            model=os.getenv("DEEPGRAM_STT_MODEL", "nova-3"),
            language=os.getenv("DEEPGRAM_LANGUAGE", "ru"),
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            smart_format=True,
        ),
        llm=build_kaira_llm(),
        tts=build_kaira_tts(),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    install_session_state_events(ctx, session, memory, agent_name=KAIRA_AGENT_NAME)

    def operator_handoff():
        return create_operator_agent(kaira_ctx, memory)

    install_positioning_and_handoff_hooks(
        session,
        kaira_ctx,
        memory,
        handoff_factory=operator_handoff if kaira_ctx.operator_enabled else None,
    )

    avatar_id = os.getenv("ANAM_AVATAR_ID", "").strip()
    telephony = is_telephony_room(ctx.room.name)
    use_anam_avatar = bool(avatar_id) and not telephony
    if use_anam_avatar:
        avatar_session = anam.AvatarSession(
            persona_config=anam.PersonaConfig(
                name="KAIRA NULLXES",
                avatarId=avatar_id,
            ),
            avatar_participant_name="KAIRA NULLXES",
        )
        await avatar_session.start(session, room=ctx.room)
        logger.info("Anam avatar session started for KAIRA NULLXES")
    elif avatar_id and telephony:
        logger.info("Anam avatar skipped for telephony room %s", ctx.room.name)

    await publish_kaira_state(
        ctx,
        "listening",
        agent_name=KAIRA_AGENT_NAME,
        reason="agent_session_start",
        memory=memory,
    )

    await session.start(
        agent=create_initial_agent(kaira_ctx, memory),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            video_input=vision_enabled(),
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_L
                ),
            ),
            # With Anam, TTS audio goes to the avatar worker (lk.publish_on_behalf).
            # See https://docs.livekit.io/agents/models/avatar/
            audio_output=not use_anam_avatar,
        ),
    )

    await publish_kaira_state(
        ctx,
        "listening",
        agent_name=KAIRA_AGENT_NAME,
        reason="agent_session_ready",
        memory=memory,
    )


if __name__ == "__main__":
    cli.run_app(server)
