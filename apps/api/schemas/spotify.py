from pydantic import BaseModel


class TrackMetadata(BaseModel):
    id: str  # spotify:track:{spotifyId}
    title: str
    artist: str
    album: str | None
    duration_ms: int
    spotify_url: str
