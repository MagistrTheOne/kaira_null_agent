from services.spotify import spotify_availability


def test_spotify_availability_reports_partial_env(monkeypatch) -> None:
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client")
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("SPOTIFY_REFRESH_TOKEN", raising=False)

    status = spotify_availability()

    assert status["clientId"] is True
    assert status["configured"] is False
