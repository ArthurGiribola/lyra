import re

import httpx
from fastapi import HTTPException

from apps.api.providers.base import LyricsProvider
from apps.api.schemas.lyrics import LyricsResult, SyncedLine

_BASE_URL = "https://lrclib.net/api/get"
_LRC_RE = re.compile(r"^\[(\d{2}):(\d{2})\.(\d{2})\]\s?(.*)")


def _parse_lrc(raw: str) -> list[SyncedLine] | None:
    lines = []
    for line in raw.splitlines():
        m = _LRC_RE.match(line)
        if m:
            mm, ss, cc, text = m.groups()
            time_ms = (int(mm) * 60 + int(ss)) * 1000 + int(cc) * 10
            lines.append(SyncedLine(time_ms=time_ms, text=text))
    return lines if lines else None


class LRCLibProvider(LyricsProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_lyrics(self, title: str, artist: str) -> LyricsResult | None:
        try:
            response = await self._client.get(
                _BASE_URL,
                params={"track_name": title, "artist_name": artist},
                timeout=httpx.Timeout(10.0, read=20.0),
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=502, detail="LRCLib request timed out") from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="LRCLib request failed") from exc
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        data = response.json()
        text = data.get("plainLyrics")
        if not text:
            return None
        raw_synced = data.get("syncedLyrics")
        synced_lines = _parse_lrc(raw_synced) if raw_synced else None
        return LyricsResult(text=text, provider="lrclib", synced_lines=synced_lines)
