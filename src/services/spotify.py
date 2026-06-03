import base64
import os
from dataclasses import dataclass
from typing import Any

import aiohttp
from livekit.agents import utils


class SpotifyServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpotifyConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    device_id: str | None = None
    market: str = "RU"

    @classmethod
    def from_env(cls) -> "SpotifyConfig | None":
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
        refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN", "").strip()
        if not client_id or not client_secret or not refresh_token:
            return None
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            device_id=os.getenv("SPOTIFY_DEVICE_ID", "").strip() or None,
            market=os.getenv("SPOTIFY_MARKET", "RU").strip() or "RU",
        )


def spotify_availability() -> dict[str, object]:
    client_id = bool(os.getenv("SPOTIFY_CLIENT_ID", "").strip())
    client_secret = bool(os.getenv("SPOTIFY_CLIENT_SECRET", "").strip())
    refresh_token = bool(os.getenv("SPOTIFY_REFRESH_TOKEN", "").strip())
    return {
        "configured": client_id and client_secret and refresh_token,
        "clientId": client_id,
        "clientSecret": client_secret,
        "refreshToken": refresh_token,
        "deviceId": bool(os.getenv("SPOTIFY_DEVICE_ID", "").strip()),
    }


async def _access_token(config: SpotifyConfig) -> str:
    credentials = f"{config.client_id}:{config.client_secret}".encode()
    auth = base64.b64encode(credentials).decode()
    session = utils.http_context.http_session()
    async with session.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth}"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": config.refresh_token,
        },
        timeout=aiohttp.ClientTimeout(total=10),
    ) as resp:
        if resp.status >= 400:
            raise SpotifyServiceError(f"Spotify auth HTTP {resp.status}")
        payload = await resp.json()
        token = payload.get("access_token")
        if not token:
            raise SpotifyServiceError("Spotify access token missing")
        return str(token)


def _format_track(track: dict[str, Any]) -> dict[str, str]:
    artists = ", ".join(artist.get("name", "") for artist in track.get("artists", []))
    return {
        "name": str(track.get("name") or ""),
        "artists": artists,
        "uri": str(track.get("uri") or ""),
        "url": str((track.get("external_urls") or {}).get("spotify") or ""),
    }


async def search_tracks(query: str, *, limit: int = 3) -> list[dict[str, str]]:
    config = SpotifyConfig.from_env()
    if not config:
        raise SpotifyServiceError(
            "Spotify contour is not authorized: SPOTIFY_CLIENT_SECRET and SPOTIFY_REFRESH_TOKEN are required"
        )

    token = await _access_token(config)
    session = utils.http_context.http_session()
    async with session.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": query,
            "type": "track",
            "limit": max(1, min(limit, 10)),
            "market": config.market,
        },
        timeout=aiohttp.ClientTimeout(total=10),
    ) as resp:
        if resp.status >= 400:
            raise SpotifyServiceError(f"Spotify search HTTP {resp.status}")
        payload = await resp.json()
    items = ((payload.get("tracks") or {}).get("items") or [])[:limit]
    return [_format_track(item) for item in items]


async def play_track(query: str) -> dict[str, str]:
    config = SpotifyConfig.from_env()
    if not config:
        raise SpotifyServiceError(
            "Spotify contour is not authorized: SPOTIFY_CLIENT_SECRET and SPOTIFY_REFRESH_TOKEN are required"
        )

    tracks = await search_tracks(query, limit=1)
    if not tracks:
        raise SpotifyServiceError("Spotify track not found")

    token = await _access_token(config)
    params = {"device_id": config.device_id} if config.device_id else None
    session = utils.http_context.http_session()
    async with session.put(
        "https://api.spotify.com/v1/me/player/play",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        json={"uris": [tracks[0]["uri"]]},
        timeout=aiohttp.ClientTimeout(total=10),
    ) as resp:
        if resp.status == 404:
            raise SpotifyServiceError("Spotify device is not active")
        if resp.status >= 400:
            raise SpotifyServiceError(f"Spotify playback HTTP {resp.status}")
    return tracks[0]
