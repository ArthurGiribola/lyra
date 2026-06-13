"use client";

import { useState } from "react";
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

function LoadingDots() {
  return (
    <div
      className="flex items-center justify-center gap-1.5 py-10"
      aria-label="Buscando letra…"
    >
      {[0, 200, 400].map((delay) => (
        <span
          key={delay}
          className="size-1.5 rounded-full bg-muted-foreground animate-[dotPulse_1.4s_ease-in-out_infinite]"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  );
}

function LyricsResult({ result }: { result: LyricsResponse }) {
  return (
    <div className="w-full animate-[fadeSlideUp_0.35s_ease-out_forwards]">
      <div className="flex items-start justify-between gap-4 mb-5 pb-4 border-b border-white/[0.07]">
        <div className="min-w-0">
          <h2 className="text-base font-semibold tracking-tight leading-snug truncate">
            {result.title}
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">{result.artist}</p>
        </div>
        <Badge
          variant="outline"
          className="shrink-0 mt-0.5 text-[11px] border-white/10 text-muted-foreground font-normal"
        >
          {result.provider}
        </Badge>
      </div>

      <pre className="whitespace-pre-wrap font-sans text-sm leading-7 text-foreground/80 max-h-[62vh] overflow-y-auto lyra-scrollbar pr-2">
        {result.lyrics}
      </pre>
    </div>
  );
}

export default function LyricsSearch() {
  const [url, setUrl] = useState("");
  const [state, setState] = useState<State>("idle");
  const [result, setResult] = useState<LyricsResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

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
          <p className="mt-3 text-sm text-destructive text-center px-2 animate-[fadeSlideUp_0.2s_ease-out_forwards]">
            {errorMessage}
          </p>
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
