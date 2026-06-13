from pydantic import BaseModel

from apps.api.schemas.lyrics import SyncedLine


class LyricsRequest(BaseModel):
    url: str


class LyricsResponse(BaseModel):
    title: str
    artist: str
    album: str | None = None
    cover_url: str | None = None
    duration_ms: int | None = None
    spotify_url: str | None = None
    provider: str
    lyrics: str
    synced_lines: list[SyncedLine] | None = None
