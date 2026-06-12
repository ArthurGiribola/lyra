import httpx
from fastapi import HTTPException

from apps.api.providers.base import LyricsProvider
from apps.api.providers.dummy import DummyLyricsProvider
from apps.api.providers.lrclib import LRCLibProvider
from apps.api.schemas.lyrics import LyricsResult

_PROVIDERS: list[LyricsProvider] = []


def init_providers(client: httpx.AsyncClient) -> None:
    global _PROVIDERS
    _PROVIDERS = [
        LRCLibProvider(client),
        DummyLyricsProvider(),
    ]


async def get_lyrics(title: str, artist: str) -> LyricsResult:
    for provider in _PROVIDERS:
        result = await provider.get_lyrics(title=title, artist=artist)
        if result:
            return result
    raise HTTPException(status_code=404, detail="Lyrics not found")
