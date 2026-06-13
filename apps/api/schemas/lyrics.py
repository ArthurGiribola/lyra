from pydantic import BaseModel


class SyncedLine(BaseModel):
    time_ms: int
    text: str


class LyricsResult(BaseModel):
    text: str
    provider: str
    language: str | None = None
    synced_lines: list[SyncedLine] | None = None
