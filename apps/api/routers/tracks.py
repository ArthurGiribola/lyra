from fastapi import APIRouter, Request

from apps.api.schemas.spotify import TrackMetadata
from apps.api.schemas.tracks import ResolveRequest
from apps.api.services.spotify import resolve_track

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.post("/resolve", response_model=TrackMetadata)
async def resolve_track_endpoint(body: ResolveRequest, request: Request) -> TrackMetadata:
    client = request.app.state.http_client
    return await resolve_track(body.url, client)
