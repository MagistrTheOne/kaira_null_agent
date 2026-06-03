import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParticipantProfile:
    identity: str
    name: str
    joined_at: float
    last_active_at: float
    speaking_events: int = 0
    role_hint: str = "participant"


@dataclass
class KairaRoomMemory:
    """Session-scoped operational memory, not CRM persistence."""

    room_name: str
    participants: dict[str, ParticipantProfile] = field(default_factory=dict)
    active_speakers: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    latest_video_frame: Any | None = None

    def upsert_participant(self, identity: str, name: str | None = None) -> None:
        now = time.time()
        existing = self.participants.get(identity)
        if existing:
            existing.name = name or existing.name
            existing.last_active_at = now
            return
        self.participants[identity] = ParticipantProfile(
            identity=identity,
            name=name or identity,
            joined_at=now,
            last_active_at=now,
            role_hint=self._infer_role(identity, name),
        )

    def remove_participant(self, identity: str) -> None:
        self.participants.pop(identity, None)
        self.active_speakers = [
            speaker for speaker in self.active_speakers if speaker != identity
        ]

    def mark_active_speakers(self, identities: list[str]) -> None:
        self.active_speakers = identities
        now = time.time()
        for identity in identities:
            profile = self.participants.get(identity)
            if profile:
                profile.last_active_at = now
                profile.speaking_events += 1

    def note_user_topic(self, utterance: str, *, max_len: int = 120) -> None:
        snippet = utterance.strip().replace("\n", " ")[:max_len]
        if not snippet:
            return
        self.topics.append(snippet)
        if len(self.topics) > 16:
            self.topics = self.topics[-16:]

    def snapshot(self) -> dict[str, object]:
        return {
            "roomName": self.room_name,
            "participantCount": len(self.participants),
            "participants": [
                {
                    "identity": profile.identity,
                    "name": profile.name,
                    "roleHint": profile.role_hint,
                    "speakingEvents": profile.speaking_events,
                }
                for profile in self.participants.values()
            ],
            "activeSpeakers": self.active_speakers,
            "topics": self.topics[-8:],
            "concerns": self.concerns[-8:],
        }

    @staticmethod
    def _infer_role(identity: str, name: str | None) -> str:
        value = f"{identity} {name or ''}".lower()
        if "agent" in value or "kaira" in value or "anam" in value:
            return "agent"
        if "phone" in value or "sip" in value or value.startswith("+"):
            return "phone"
        if "viewer" in value or "observer" in value:
            return "observer"
        return "participant"
