import httpx

from apps.api.providers.base import LyricsProvider
from apps.api.schemas.lyrics import LyricsResult

_BASE_URL = "https://lrclib.net/api/get"


class LRCLibProvider(LyricsProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_lyrics(self, title: str, artist: str) -> LyricsResult | None:
        response = await self._client.get(
            _BASE_URL,
            params={"track_name": title, "artist_name": artist},
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        data = response.json()
        text = data.get("plainLyrics")
        if not text:
            return None
        return LyricsResult(text=text, provider="lrclib")
