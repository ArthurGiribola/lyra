from apps.api.providers.base import LyricsProvider
from apps.api.schemas.lyrics import LyricsResult


class DummyLyricsProvider(LyricsProvider):
    async def get_lyrics(self, title: str, artist: str) -> LyricsResult:
        return LyricsResult(
            text=f"[Dummy lyrics for {title} by {artist}]",
            provider="dummy",
            language=None,
        )
