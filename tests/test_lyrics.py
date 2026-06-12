import pytest
from fastapi import HTTPException
from unittest.mock import patch

import apps.api.services.lyrics as lyrics_module
from apps.api.providers.base import LyricsProvider
from apps.api.providers.dummy import DummyLyricsProvider
from apps.api.schemas.lyrics import LyricsResult
from apps.api.services.lyrics import get_lyrics


class _NullProvider(LyricsProvider):
    async def get_lyrics(self, title: str, artist: str) -> None:
        return None


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


async def test_get_lyrics_returns_result_from_provider() -> None:
    result = await get_lyrics(title="Blinding Lights", artist="The Weeknd")
    assert isinstance(result, LyricsResult)
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
