from abc import ABC, abstractmethod

from apps.api.schemas.lyrics import LyricsResult


class LyricsProvider(ABC):
    @abstractmethod
    async def get_lyrics(self, title: str, artist: str) -> LyricsResult | None:
        ...
