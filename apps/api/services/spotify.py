import re
import time
from dataclasses import dataclass

import httpx
from fastapi import HTTPException

from apps.api.config import settings
from apps.api.schemas.spotify import TrackMetadata

_TRACK_URL_RE = re.compile(r"open\.spotify\.com/track/([A-Za-z0-9]+)")
_TOKEN_URL = "https://accounts.spotify.com/api/token"
_API_BASE = "https://api.spotify.com/v1"


@dataclass
class SpotifyTokenCache:
    access_token: str
    expires_at: float


_token_cache: SpotifyTokenCache | None = None


def extract_track_id(url: str) -> str:
    match = _TRACK_URL_RE.search(url)
    if not match:
        raise HTTPException(status_code=422, detail="Invalid Spotify track URL")
    return match.group(1)


async def get_token(client: httpx.AsyncClient) -> str:
    global _token_cache

    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise HTTPException(status_code=500, detail="Spotify credentials not configured")

    if _token_cache and time.time() < _token_cache.expires_at:
        return _token_cache.access_token

    response = await client.post(
        _TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(settings.spotify_client_id, settings.spotify_client_secret),
    )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to obtain Spotify token")

    data = response.json()
    _token_cache = SpotifyTokenCache(
        access_token=data["access_token"],
        expires_at=time.time() + data["expires_in"] - 60,
    )
    return _token_cache.access_token


async def resolve_track(url: str, client: httpx.AsyncClient) -> TrackMetadata:
    track_id = extract_track_id(url)
    token = await get_token(client)

    response = await client.get(
        f"{_API_BASE}/tracks/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Track not found on Spotify")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Spotify API error")

    data = response.json()
    return TrackMetadata(
        id=f"spotify:track:{data['id']}",
        title=data["name"],
        artist=data["artists"][0]["name"],
        album=data["album"]["name"],
        duration_ms=data["duration_ms"],
        spotify_url=data["external_urls"]["spotify"],
    )
