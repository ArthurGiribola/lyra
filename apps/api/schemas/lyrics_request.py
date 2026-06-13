from pydantic import BaseModel


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
