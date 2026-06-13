"use client";

import { useRef, useState } from "react";
import { fetchLyrics, ApiError, type LyricsResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

type State = "idle" | "loading" | "success" | "error";

function LyraIcon() {
  return (
    <svg
      width="26"
      height="26"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M7 20h10" />
      <path d="M7 20C6 14 3 11 8 5" />
      <path d="M17 20C18 14 21 11 16 5" />
      <path d="M8 5h8" />
      <line x1="10.5" y1="5" x2="10" y2="20" />
      <line x1="12" y1="5" x2="12" y2="20" />
      <line x1="13.5" y1="5" x2="14" y2="20" />
    </svg>
  );
}

function AlertIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function SpotifyIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
    </svg>
  );
}

function LoadingDots() {
  return (
    <div
      className="flex flex-col items-center justify-center gap-4 py-12"
      aria-label="Buscando letra…"
    >
      <div className="flex items-center gap-1.5">
        {[0, 200, 400].map((delay) => (
          <span
            key={delay}
            className="size-1.5 rounded-full bg-muted-foreground animate-[dotPulse_1.4s_ease-in-out_infinite]"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground/40 animate-pulse">
        Isso pode levar alguns segundos…
      </p>
    </div>
  );
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function LyricsResult({ result }: { result: LyricsResponse }) {
  const stanzas = result.lyrics.split(/\n\n+/).map((s) => s.trim()).filter(Boolean);

  return (
    <div className="w-full animate-[fadeSlideUp_0.35s_ease-out_forwards]">
      {/* Track card */}
      <div className="rounded-2xl bg-white/[0.03] border border-white/[0.06] p-4 mb-8">
        <div className="flex items-start gap-4">
          {/* Album cover */}
          <div className="shrink-0 size-20 sm:size-24 rounded-xl overflow-hidden bg-white/[0.06]">
            {result.cover_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={result.cover_url}
                alt={result.album ?? result.title}
                width={96}
                height={96}
                className="size-full object-cover"
              />
            ) : (
              <div className="size-full flex items-center justify-center text-muted-foreground/20">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z" />
                </svg>
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="min-w-0 flex-1 pt-0.5">
            <h2 className="text-lg font-semibold tracking-tight leading-snug line-clamp-2">
              {result.title}
            </h2>
            <p className="text-sm text-muted-foreground mt-1 truncate">
              {result.artist}
            </p>
            {result.duration_ms != null && (
              <p className="text-xs text-muted-foreground/40 mt-0.5">
                {formatDuration(result.duration_ms)}
              </p>
            )}
            {result.album && (
              <p className="text-sm text-muted-foreground/50 mt-1 truncate">
                {result.album}
              </p>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-3">
              <Badge
                variant="outline"
                className="text-[11px] border-white/10 text-muted-foreground font-normal"
              >
                {result.provider}
              </Badge>
              {result.spotify_url && (
                <a
                  href={result.spotify_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-[11px] text-[#1DB954] border border-[#1DB954]/30 rounded-full px-2.5 py-0.5 hover:bg-[#1DB954]/10 transition-colors"
                >
                  <SpotifyIcon />
                  Abrir no Spotify
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Lyrics */}
      <div className="space-y-6 pb-16">
        {stanzas.map((stanza, i) => (
          <p
            key={i}
            className="text-[15px] leading-8 text-foreground/85 whitespace-pre-line"
          >
            {stanza}
          </p>
        ))}
      </div>
    </div>
  );
}

export default function LyricsSearch() {
  const [url, setUrl] = useState("");
  const [state, setState] = useState<State>("idle");
  const [result, setResult] = useState<LyricsResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;

    setState("loading");
    setResult(null);
    setErrorMessage("");

    try {
      const data = await fetchLyrics(trimmed);
      setResult(data);
      setState("success");
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : "Não foi possível conectar à API.",
      );
      setState("error");
    }
  }

  function handleRetry() {
    setState("idle");
    setErrorMessage("");
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  return (
    <div className="min-h-screen flex flex-col items-center px-4 pt-14 pb-12">
      {/* Wordmark */}
      <div className="flex items-center gap-2.5 mb-9 text-primary">
        <LyraIcon />
        <span className="text-[1.75rem] font-bold tracking-tight text-foreground leading-none">
          Lyr<span className="text-primary">A</span>
        </span>
      </div>

      {/* Search */}
      <div className="w-full max-w-xl">
        <form onSubmit={handleSubmit}>
          <div className="flex items-center rounded-full border border-white/[0.08] bg-white/[0.04] focus-within:border-primary/40 focus-within:ring-4 focus-within:ring-primary/10 transition-all duration-200">
            <Input
              ref={inputRef}
              type="url"
              placeholder="https://open.spotify.com/track/…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={state === "loading"}
              className="flex-1 h-13 bg-transparent border-0 rounded-full pl-5 pr-2 text-sm placeholder:text-muted-foreground/40 focus-visible:ring-0 focus-visible:border-0"
            />
            <Button
              type="submit"
              disabled={state === "loading" || !url.trim()}
              className="m-1.5 h-10 rounded-full px-5 shrink-0 text-sm font-medium transition-all duration-150 hover:brightness-110 active:scale-[0.97]"
            >
              Buscar
            </Button>
          </div>
        </form>

        {state === "error" && (
          <div className="mt-4 flex flex-col items-center gap-2 animate-[fadeSlideUp_0.2s_ease-out_forwards]">
            <div className="flex items-center gap-2 text-sm text-destructive">
              <AlertIcon />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={handleRetry}
              className="text-xs text-muted-foreground/50 hover:text-muted-foreground underline underline-offset-2 transition-colors"
            >
              Tentar novamente
            </button>
          </div>
        )}
      </div>

      {/* Loading */}
      {state === "loading" && <LoadingDots />}

      {/* Result */}
      {state === "success" && result && (
        <div className="w-full max-w-xl mt-7">
          <LyricsResult result={result} />
        </div>
      )}

      {/* Footer */}
      <footer className="mt-auto pt-16 text-[11px] text-muted-foreground/30 tracking-wide">
        LRCLib · Spotify
      </footer>
    </div>
  );
}
