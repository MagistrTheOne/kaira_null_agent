def is_telephony_room(room_name: str) -> bool:
    """True for inbound SIP dispatch rooms and outbound dialer rooms."""
    normalized = room_name.strip().lower()
    return normalized.startswith("kaira-nullxes_") or normalized.startswith(
        "kaira-call-"
    )
