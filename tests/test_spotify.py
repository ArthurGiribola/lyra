import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import apps.api.services.spotify as spotify_module
from apps.api.schemas.spotify import TrackMetadata
from apps.api.services.spotify import extract_track_id, get_token, resolve_track

_VALID_URL = "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
_TRACK_ID = "4uLU6hMCjMI75M1A2tKUQC"
_FAKE_CREDS = {"spotify_client_id": "fake_id", "spotify_client_secret": "fake_secret"}


@pytest.fixture(autouse=True)
def reset_token_cache():
    spotify_module._token_cache = None
    yield
    spotify_module._token_cache = None


def _mock_token_response(token: str = "test_token", expires_in: int = 3600) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": token, "expires_in": expires_in}
    return resp


def _mock_track_response() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "id": _TRACK_ID,
        "name": "Blinding Lights",
        "artists": [{"name": "The Weeknd"}],
        "album": {"name": "After Hours"},
        "duration_ms": 200040,
        "external_urls": {"spotify": _VALID_URL},
    }
    return resp


def _warm_cache(token: str = "test_token") -> None:
    spotify_module._token_cache = spotify_module.SpotifyTokenCache(
        access_token=token,
        expires_at=time.time() + 3600,
    )


# --- extract_track_id ---


def test_extract_track_id_valid() -> None:
    assert extract_track_id(_VALID_URL) == _TRACK_ID


def test_extract_track_id_with_query_params() -> None:
    url = f"{_VALID_URL}?si=abc123&utm_source=copy-link"
    assert extract_track_id(url) == _TRACK_ID


def test_extract_track_id_invalid() -> None:
    with pytest.raises(HTTPException) as exc_info:
        extract_track_id("https://music.youtube.com/watch?v=abc")
    assert exc_info.value.status_code == 422


# --- get_token ---


async def test_get_token_missing_credentials() -> None:
    mock_client = AsyncMock()
    with patch.multiple(spotify_module.settings, spotify_client_id=None, spotify_client_secret=None):
        with pytest.raises(HTTPException) as exc_info:
            await get_token(mock_client)
    assert exc_info.value.status_code == 500


async def test_get_token_fetches_and_caches() -> None:
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_token_response("tok1")

    with patch.multiple(spotify_module.settings, **_FAKE_CREDS):
        token = await get_token(mock_client)
        assert token == "tok1"
        mock_client.post.assert_called_once()

        # Second call must hit cache, not make another request
        token2 = await get_token(mock_client)
        assert token2 == "tok1"
        mock_client.post.assert_called_once()


async def test_get_token_renews_when_expired() -> None:
    spotify_module._token_cache = spotify_module.SpotifyTokenCache(
        access_token="old_token",
        expires_at=time.time() - 10,
    )
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_token_response("new_token")

    with patch.multiple(spotify_module.settings, **_FAKE_CREDS):
        token = await get_token(mock_client)

    assert token == "new_token"
    mock_client.post.assert_called_once()


async def test_get_token_raises_502_on_provider_failure() -> None:
    mock_client = AsyncMock()
    bad_resp = MagicMock()
    bad_resp.status_code = 401
    mock_client.post.return_value = bad_resp

    with patch.multiple(spotify_module.settings, **_FAKE_CREDS):
        with pytest.raises(HTTPException) as exc_info:
            await get_token(mock_client)
    assert exc_info.value.status_code == 502


# --- resolve_track ---


async def test_resolve_track_success() -> None:
    _warm_cache()
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_track_response()

    with patch.multiple(spotify_module.settings, **_FAKE_CREDS):
        result = await resolve_track(_VALID_URL, mock_client)

    assert isinstance(result, TrackMetadata)
    assert result.id == f"spotify:track:{_TRACK_ID}"
    assert result.title == "Blinding Lights"
    assert result.artist == "The Weeknd"
    assert result.album == "After Hours"
    assert result.duration_ms == 200040
    assert result.spotify_url == _VALID_URL


async def test_resolve_track_not_found() -> None:
    _warm_cache()
    resp = MagicMock()
    resp.status_code = 404
    mock_client = AsyncMock()
    mock_client.get.return_value = resp

    with patch.multiple(spotify_module.settings, **_FAKE_CREDS):
        with pytest.raises(HTTPException) as exc_info:
            await resolve_track(_VALID_URL, mock_client)
    assert exc_info.value.status_code == 404


async def test_resolve_track_provider_error() -> None:
    _warm_cache()
    resp = MagicMock()
    resp.status_code = 500
    mock_client = AsyncMock()
    mock_client.get.return_value = resp

    with patch.multiple(spotify_module.settings, **_FAKE_CREDS):
        with pytest.raises(HTTPException) as exc_info:
            await resolve_track(_VALID_URL, mock_client)
    assert exc_info.value.status_code == 502


async def test_resolve_track_invalid_url() -> None:
    mock_client = AsyncMock()
    with pytest.raises(HTTPException) as exc_info:
        await resolve_track("https://not-spotify.com/foo", mock_client)
    assert exc_info.value.status_code == 422
