from pydantic import BaseModel


class LyricsResult(BaseModel):
    text: str
    provider: str
    language: str | None = None
