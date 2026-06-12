from pydantic import BaseModel


class LyricsRequest(BaseModel):
    url: str


class LyricsResponse(BaseModel):
    title: str
    artist: str
    provider: str
    lyrics: str
