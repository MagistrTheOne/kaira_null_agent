import argparse
import asyncio
import os
import time

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

DEFAULT_AGENT_NAME = "KAIRA-NULLXES"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _normalise_phone(phone_number: str) -> str:
    value = phone_number.strip().replace(" ", "")
    if not value.startswith("+"):
        raise ValueError("phone_number must be E.164, for example +12676950155")
    return value


async def make_outbound_call(
    phone_number: str,
    *,
    room_name: str | None = None,
    participant_identity: str | None = None,
    participant_name: str = "KAIRA Phone Participant",
) -> dict[str, str]:
    """
    Create a LiveKit room context, dispatch KAIRA, and dial a phone participant.

    Required env:
    - LIVEKIT_URL
    - LIVEKIT_API_KEY
    - LIVEKIT_API_SECRET
    - SIP_OUTBOUND_TRUNK_ID

    Optional env:
    - KAIRA_AGENT_NAME
    - SIP_CALLER_ID
    """

    destination = _normalise_phone(phone_number)
    livekit_url = _require_env("LIVEKIT_URL")
    api_key = _require_env("LIVEKIT_API_KEY")
    api_secret = _require_env("LIVEKIT_API_SECRET")
    trunk_id = _require_env("SIP_OUTBOUND_TRUNK_ID")
    agent_name = (
        os.getenv("KAIRA_AGENT_NAME", DEFAULT_AGENT_NAME).strip() or DEFAULT_AGENT_NAME
    )

    room = room_name or f"kaira-call-{int(time.time())}"
    identity = (
        participant_identity or f"phone-{destination.lstrip('+')}-{int(time.time())}"
    )

    lkapi = api.LiveKitAPI(livekit_url, api_key, api_secret)
    try:
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room,
                agent_name=agent_name,
                metadata='{"source":"kaira_outbound_call"}',
            )
        )

        request = api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=destination,
            room_name=room,
            participant_identity=identity,
            participant_name=participant_name,
            wait_until_answered=True,
        )
        caller_id = os.getenv("SIP_CALLER_ID", "").strip()
        if caller_id:
            request.sip_number = caller_id

        participant = await lkapi.sip.create_sip_participant(request, trunk_id=trunk_id)
        return {
            "room": room,
            "agentName": agent_name,
            "dispatchId": dispatch.id,
            "participantIdentity": participant.participant_identity,
            "sipCallId": participant.sip_call_id,
        }
    finally:
        await lkapi.aclose()


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Trigger KAIRA outbound SIP call")
    parser.add_argument("phone_number", help="Target phone number in E.164 format")
    parser.add_argument("--room", dest="room_name", default=None)
    args = parser.parse_args()
    result = await make_outbound_call(args.phone_number, room_name=args.room_name)
    print(result)


if __name__ == "__main__":
    asyncio.run(_main())
