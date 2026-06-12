from fastapi import APIRouter, Request

from apps.api.schemas.lyrics_request import LyricsRequest, LyricsResponse
from apps.api.services.lyrics import get_lyrics
from apps.api.services.spotify import resolve_track

router = APIRouter(prefix="/lyrics", tags=["lyrics"])


@router.post("", response_model=LyricsResponse)
async def get_lyrics_endpoint(body: LyricsRequest, request: Request) -> LyricsResponse:
    client = request.app.state.http_client
    track = await resolve_track(body.url, client)
    result = await get_lyrics(title=track.title, artist=track.artist)
    return LyricsResponse(
        title=track.title,
        artist=track.artist,
        provider=result.provider,
        lyrics=result.text,
    )
