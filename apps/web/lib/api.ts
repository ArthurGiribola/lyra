export interface SyncedLine {
  time_ms: number;
  text: string;
}

export interface LyricsResponse {
  title: string;
  artist: string;
  album: string | null;
  cover_url: string | null;
  duration_ms: number | null;
  spotify_url: string | null;
  provider: string;
  lyrics: string;
  synced_lines: SyncedLine[] | null;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

const ERROR_MESSAGES: Record<number, string> = {
  404: "Letra não encontrada para esta música.",
  422: "URL inválida. Use um link do Spotify no formato open.spotify.com/track/...",
  502: "Falha no provider de letra. Tente novamente.",
};

export async function fetchLyrics(url: string): Promise<LyricsResponse> {
  let response: Response;

  try {
    response = await fetch("/api/lyrics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
  } catch {
    throw new ApiError(0, "Não foi possível conectar à API.");
  }

  if (!response.ok) {
    const message =
      ERROR_MESSAGES[response.status] ?? "Erro inesperado. Tente novamente.";
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<LyricsResponse>;
}
