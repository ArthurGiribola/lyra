from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

import apps.api.services.lyrics as lyrics_module
from apps.api.providers.base import LyricsProvider
from apps.api.providers.dummy import DummyLyricsProvider
from apps.api.providers.lrclib import LRCLibProvider, _parse_lrc
from apps.api.schemas.lyrics import LyricsResult, SyncedLine
from apps.api.services.lyrics import get_lyrics


class _NullProvider(LyricsProvider):
    async def get_lyrics(self, title: str, artist: str) -> None:
        return None


def _mock_client(
    status: int,
    plain_lyrics: str | None = None,
    synced_lyrics: str | None = None,
) -> AsyncMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"plainLyrics": plain_lyrics, "syncedLyrics": synced_lyrics}
    client = AsyncMock()
    client.get.return_value = resp
    return client


_SAMPLE_LRC = "[00:09.65] First line\n[00:12.10] Second line\n[00:14.00] "
_SAMPLE_PLAIN = "First line\nSecond line\n"


# --- DummyLyricsProvider ---


async def test_dummy_provider_returns_lyrics_result() -> None:
    provider = DummyLyricsProvider()
    result = await provider.get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert isinstance(result, LyricsResult)
    assert result.provider == "dummy"


async def test_dummy_provider_text_contains_title_and_artist() -> None:
    provider = DummyLyricsProvider()
    result = await provider.get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert result is not None
    assert "Blinding Lights" in result.text
    assert "The Weeknd" in result.text


# --- LRCLibProvider ---


async def test_lrclib_provider_returns_lyrics_on_success() -> None:
    provider = LRCLibProvider(_mock_client(200, "Verse 1\nChorus"))
    result = await provider.get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert isinstance(result, LyricsResult)
    assert result.provider == "lrclib"
    assert result.text == "Verse 1\nChorus"
    assert result.synced_lines is None


async def test_lrclib_provider_returns_synced_lines_when_available() -> None:
    provider = LRCLibProvider(_mock_client(200, _SAMPLE_PLAIN, _SAMPLE_LRC))
    result = await provider.get_lyrics(title="Shape of You", artist="Ed Sheeran")
    assert result is not None
    assert result.synced_lines is not None
    assert len(result.synced_lines) == 3
    assert result.synced_lines[0] == SyncedLine(time_ms=9650, text="First line")
    assert result.synced_lines[1] == SyncedLine(time_ms=12100, text="Second line")
    assert result.synced_lines[2] == SyncedLine(time_ms=14000, text="")


async def test_lrclib_provider_synced_lines_none_when_field_absent() -> None:
    provider = LRCLibProvider(_mock_client(200, "Verse 1\nChorus", synced_lyrics=None))
    result = await provider.get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert result is not None
    assert result.synced_lines is None


async def test_lrclib_provider_returns_none_when_not_found() -> None:
    provider = LRCLibProvider(_mock_client(404))
    result = await provider.get_lyrics(title="Unknown Track", artist="Nobody")
    assert result is None


async def test_lrclib_provider_returns_none_on_provider_error() -> None:
    provider = LRCLibProvider(_mock_client(500))
    result = await provider.get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert result is None


async def test_lrclib_provider_applies_extended_read_timeout() -> None:
    client = AsyncMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"plainLyrics": "Verse\nChorus"}
    client.get.return_value = resp

    provider = LRCLibProvider(client)
    await provider.get_lyrics(title="Shape of You", artist="Ed Sheeran")

    _, kwargs = client.get.call_args
    timeout = kwargs.get("timeout")
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.read == 20.0
    assert timeout.connect == 10.0


async def test_lrclib_provider_raises_502_on_timeout() -> None:
    client = AsyncMock()
    client.get.side_effect = httpx.ReadTimeout("timed out")
    provider = LRCLibProvider(client)
    with pytest.raises(HTTPException) as exc_info:
        await provider.get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "LRCLib request timed out"


async def test_lrclib_provider_raises_502_on_network_error() -> None:
    client = AsyncMock()
    client.get.side_effect = httpx.ConnectError("connection refused")
    provider = LRCLibProvider(client)
    with pytest.raises(HTTPException) as exc_info:
        await provider.get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "LRCLib request failed"


# --- get_lyrics orchestration ---


async def test_get_lyrics_returns_result_from_first_provider() -> None:
    with patch.object(
        lyrics_module,
        "_PROVIDERS",
        [LRCLibProvider(_mock_client(200, "Real lyrics")), DummyLyricsProvider()],
    ):
        result = await get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert isinstance(result, LyricsResult)
    assert result.provider == "lrclib"
    assert result.text == "Real lyrics"


async def test_get_lyrics_falls_back_to_dummy_when_lrclib_returns_none() -> None:
    with patch.object(
        lyrics_module,
        "_PROVIDERS",
        [LRCLibProvider(_mock_client(404)), DummyLyricsProvider()],
    ):
        result = await get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert result.provider == "dummy"


async def test_get_lyrics_raises_404_when_all_providers_return_none() -> None:
    with patch.object(lyrics_module, "_PROVIDERS", [_NullProvider()]):
        with pytest.raises(HTTPException) as exc_info:
            await get_lyrics(title="Unknown Track", artist="Nobody")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Lyrics not found"


def test_lyrics_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        LyricsProvider()  # type: ignore[abstract]


# --- _parse_lrc ---


def test_parse_lrc_converts_timestamps_to_ms() -> None:
    raw = "[00:09.65] First line\n[01:02.30] Second line"
    lines = _parse_lrc(raw)
    assert lines is not None
    assert lines[0] == SyncedLine(time_ms=9650, text="First line")
    assert lines[1] == SyncedLine(time_ms=62300, text="Second line")


def test_parse_lrc_handles_empty_text_lines() -> None:
    raw = "[00:09.00] Text\n[00:10.00] "
    lines = _parse_lrc(raw)
    assert lines is not None
    assert lines[1] == SyncedLine(time_ms=10000, text="")


def test_parse_lrc_returns_none_for_empty_string() -> None:
    assert _parse_lrc("") is None


def test_parse_lrc_skips_non_timestamp_lines() -> None:
    raw = "not a timestamp line\n[00:01.00] Valid line"
    lines = _parse_lrc(raw)
    assert lines is not None
    assert len(lines) == 1
    assert lines[0].text == "Valid line"
