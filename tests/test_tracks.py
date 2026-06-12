from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from httpx import AsyncClient

import apps.api.services.spotify as spotify_module
from apps.api.schemas.spotify import TrackMetadata

_VALID_URL = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
_TRACK_ID = "4uLU6hMCjMI75M1A2tKUQC"

_SAMPLE_TRACK = TrackMetadata(
    id=f"spotify:track:{_TRACK_ID}",
    title="Blinding Lights",
    artist="The Weeknd",
    album="After Hours",
    duration_ms=200040,
    spotify_url=_VALID_URL,
)


def _mock_resolve(
    result: TrackMetadata | None = None,
    exc: Exception | None = None,
) -> AsyncMock:
    mock = AsyncMock()
    if exc:
        mock.side_effect = exc
    else:
        mock.return_value = result or _SAMPLE_TRACK
    return mock


async def test_resolve_returns_200_with_track_metadata(client: AsyncClient) -> None:
    with patch("apps.api.routers.tracks.resolve_track", _mock_resolve()):
        response = await client.post("/tracks/resolve", json={"url": _VALID_URL})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == f"spotify:track:{_TRACK_ID}"
    assert data["title"] == "Blinding Lights"
    assert data["artist"] == "The Weeknd"
    assert data["album"] == "After Hours"
    assert data["duration_ms"] == 200040
    assert data["spotify_url"] == _VALID_URL


async def test_resolve_missing_url_returns_422(client: AsyncClient) -> None:
    response = await client.post("/tracks/resolve", json={})
    assert response.status_code == 422


async def test_resolve_invalid_spotify_url_returns_422(client: AsyncClient) -> None:
    exc = HTTPException(status_code=422, detail="Invalid Spotify track URL")
    with patch("apps.api.routers.tracks.resolve_track", _mock_resolve(exc=exc)):
        response = await client.post(
            "/tracks/resolve", json={"url": "https://music.youtube.com/watch?v=abc"}
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid Spotify track URL"


async def test_resolve_track_not_found_returns_404(client: AsyncClient) -> None:
    exc = HTTPException(status_code=404, detail="Track not found on Spotify")
    with patch("apps.api.routers.tracks.resolve_track", _mock_resolve(exc=exc)):
        response = await client.post("/tracks/resolve", json={"url": _VALID_URL})

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found on Spotify"


async def test_resolve_provider_error_returns_502(client: AsyncClient) -> None:
    exc = HTTPException(status_code=502, detail="Spotify API error")
    with patch("apps.api.routers.tracks.resolve_track", _mock_resolve(exc=exc)):
        response = await client.post("/tracks/resolve", json={"url": _VALID_URL})

    assert response.status_code == 502


async def test_resolve_uses_app_state_http_client(client: AsyncClient) -> None:
    mock_fn = _mock_resolve()
    with patch("apps.api.routers.tracks.resolve_track", mock_fn):
        await client.post("/tracks/resolve", json={"url": _VALID_URL})

    mock_fn.assert_awaited_once()
    assert isinstance(mock_fn.call_args.args[1], httpx.AsyncClient)


async def test_resolve_missing_spotify_credentials_returns_500(client: AsyncClient) -> None:
    spotify_module._token_cache = None
    with patch.multiple(spotify_module.settings, spotify_client_id=None, spotify_client_secret=None):
        response = await client.post("/tracks/resolve", json={"url": _VALID_URL})

    assert response.status_code == 500
    assert "credentials" in response.json()["detail"].lower()
