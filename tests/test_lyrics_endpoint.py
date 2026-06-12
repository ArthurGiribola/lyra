from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from apps.api.schemas.lyrics import LyricsResult
from apps.api.schemas.spotify import TrackMetadata

_VALID_URL = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"

_SAMPLE_TRACK = TrackMetadata(
    id="spotify:track:4uLU6hMCjMI75M1A2tKUQC",
    title="Blinding Lights",
    artist="The Weeknd",
    album="After Hours",
    duration_ms=200040,
    spotify_url=_VALID_URL,
)

_SAMPLE_LYRICS = LyricsResult(
    text="I've been on my own for long enough\nMaybe you can show me how to love",
    provider="lrclib",
)


async def test_post_lyrics_returns_200(client: AsyncClient) -> None:
    with patch("apps.api.routers.lyrics.resolve_track", AsyncMock(return_value=_SAMPLE_TRACK)), \
         patch("apps.api.routers.lyrics.get_lyrics", AsyncMock(return_value=_SAMPLE_LYRICS)):
        response = await client.post("/lyrics", json={"url": _VALID_URL})

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Blinding Lights"
    assert data["artist"] == "The Weeknd"
    assert data["provider"] == "lrclib"
    assert data["lyrics"] == _SAMPLE_LYRICS.text
    assert set(data.keys()) == {"title", "artist", "provider", "lyrics"}


async def test_post_lyrics_missing_url_returns_422(client: AsyncClient) -> None:
    response = await client.post("/lyrics", json={})
    assert response.status_code == 422


async def test_post_lyrics_invalid_spotify_url_returns_422(client: AsyncClient) -> None:
    exc = HTTPException(status_code=422, detail="Invalid Spotify track URL")
    with patch("apps.api.routers.lyrics.resolve_track", AsyncMock(side_effect=exc)):
        response = await client.post("/lyrics", json={"url": "https://music.youtube.com/"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid Spotify track URL"


async def test_post_lyrics_track_not_found_returns_404(client: AsyncClient) -> None:
    exc = HTTPException(status_code=404, detail="Track not found on Spotify")
    with patch("apps.api.routers.lyrics.resolve_track", AsyncMock(side_effect=exc)):
        response = await client.post("/lyrics", json={"url": _VALID_URL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found on Spotify"


async def test_post_lyrics_lyrics_not_found_returns_404(client: AsyncClient) -> None:
    exc = HTTPException(status_code=404, detail="Lyrics not found")
    with patch("apps.api.routers.lyrics.resolve_track", AsyncMock(return_value=_SAMPLE_TRACK)), \
         patch("apps.api.routers.lyrics.get_lyrics", AsyncMock(side_effect=exc)):
        response = await client.post("/lyrics", json={"url": _VALID_URL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Lyrics not found"


async def test_post_lyrics_provider_error_returns_502(client: AsyncClient) -> None:
    exc = HTTPException(status_code=502, detail="Spotify API error")
    with patch("apps.api.routers.lyrics.resolve_track", AsyncMock(side_effect=exc)):
        response = await client.post("/lyrics", json={"url": _VALID_URL})

    assert response.status_code == 502
