from runtime.telephony import is_telephony_room


def test_inbound_sip_room_detected() -> None:
    assert is_telephony_room("KAIRA-NULLXES_+12676950155_abc123")


def test_outbound_dialer_room_detected() -> None:
    assert is_telephony_room("kaira-call-1780223095")


def test_web_room_not_telephony() -> None:
    assert not is_telephony_room("demo-room-42")
