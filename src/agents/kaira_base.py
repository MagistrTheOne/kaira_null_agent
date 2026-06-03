import asyncio
import logging
import os

from livekit.agents import Agent, get_job_context, llm

from kaira.identity.positioning import (
    detect_positioning_trigger,
    format_positioning_inject,
)
from kaira.identity.router import build_instructions
from kaira.modes import KairaMode
from kaira.session_context import KairaSessionContext
from kaira.vision import (
    frame_image_content,
    image_content_from_bytes,
    user_message_text,
    vision_enabled,
    vision_image_topic,
)
from runtime.room_memory import KairaRoomMemory

logger = logging.getLogger("agent-KAIRA-NULLXES")


class KairaAgentBase(Agent):
    def __init__(
        self,
        kaira_ctx: KairaSessionContext,
        memory: KairaRoomMemory,
    ) -> None:
        self._kaira_ctx = kaira_ctx
        self._memory = memory
        self._vision_tasks: list[asyncio.Task] = []
        super().__init__(instructions=build_instructions(kaira_ctx.mode))

    @property
    def kaira_ctx(self) -> KairaSessionContext:
        return self._kaira_ctx

    @property
    def room_memory(self) -> KairaRoomMemory:
        return self._memory

    async def apply_mode(self, mode: KairaMode) -> None:
        self._kaira_ctx.mode = mode
        if mode == KairaMode.MAGISTER:
            self._kaira_ctx.magister_active = True
        elif mode == KairaMode.PUBLIC:
            self._kaira_ctx.magister_active = False
        await self.update_instructions(build_instructions(mode))

    async def on_enter(self) -> None:
        if not vision_enabled():
            return
        try:
            room = get_job_context().room
        except RuntimeError:
            logger.warning("KAIRA vision: job context unavailable on enter")
            return

        topic = vision_image_topic()

        def _image_received_handler(reader, participant_identity: str) -> None:
            task = asyncio.create_task(
                self._image_received(reader, participant_identity)
            )
            self._vision_tasks.append(task)

            def _discard_task(done: asyncio.Task) -> None:
                if done in self._vision_tasks:
                    self._vision_tasks.remove(done)

            task.add_done_callback(_discard_task)

        room.register_byte_stream_handler(topic, _image_received_handler)
        logger.info("KAIRA vision byte stream handler registered topic=%s", topic)

    async def _image_received(self, reader, participant_identity: str) -> None:
        image_bytes = b""
        async for chunk in reader:
            image_bytes += chunk

        if not image_bytes:
            return

        caption = (
            f"Пользователь {participant_identity} отправил изображение. "
            "Опиши, что видишь, кратко и по-русски."
        )
        await self.inject_user_vision_message(
            image_content_from_bytes(image_bytes),
            caption,
        )
        logger.info(
            "KAIRA vision image added to chat context from %s (%s bytes)",
            participant_identity,
            len(image_bytes),
        )

    async def inject_user_vision_message(
        self,
        image: llm.ImageContent,
        caption: str,
    ) -> None:
        chat_ctx = self.chat_ctx.copy()
        chat_ctx.add_message(role="user", content=[image, caption])
        await self.update_chat_ctx(chat_ctx)

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        if vision_enabled() and self._memory.latest_video_frame is not None:
            frame = self._memory.latest_video_frame
            self._memory.latest_video_frame = None
            if isinstance(new_message.content, list):
                new_message.content.append(frame_image_content(frame))
            else:
                text_part = (
                    new_message.content if isinstance(new_message.content, str) else ""
                )
                new_message.content = [text_part, frame_image_content(frame)]
            logger.info("KAIRA vision appended latest video frame to user turn")

        text = user_message_text(new_message.content)

        if text:
            self._kaira_ctx.last_user_utterance = text
            self._memory.note_user_topic(text)

            positioning_key = detect_positioning_trigger(text)
            if (
                positioning_key
                and positioning_key not in self._kaira_ctx.injected_positioning_keys
            ):
                inject = format_positioning_inject(positioning_key)
                if inject:
                    self._kaira_ctx.injected_positioning_keys.add(positioning_key)
                    turn_ctx.add_message(role="system", content=inject)
                    logger.info("positioning injected: %s", positioning_key)

    def _policy_command(self) -> str:
        return self._kaira_ctx.last_user_utterance

    def _operator_status_payload(self) -> dict[str, object]:
        from services.audit import audit_enabled
        from services.firecrawl import firecrawl_available
        from services.mcp_executor import mcp_browser_available
        from services.spotify import spotify_availability

        return {
            "operatorMode": os.getenv("KAIRA_OPERATOR_MODE", "disabled"),
            "vision": vision_enabled(),
            "visionImageTopic": vision_image_topic(),
            "firecrawl": firecrawl_available(),
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
            "newsResearch": firecrawl_available() or bool(os.getenv("TAVILY_API_KEY")),
            "spotify": spotify_availability(),
            "browserExecutor": os.getenv("KAIRA_BROWSER_EXECUTOR", "disabled"),
            "mcpBrowser": mcp_browser_available(),
            "auditTrail": audit_enabled(),
            "magisterProtocol": self._kaira_ctx.magister_active,
            "sessionMode": self._kaira_ctx.mode.value,
        }
