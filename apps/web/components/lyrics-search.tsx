"use client";

import { useState } from "react";
import { fetchLyrics, ApiError, type LyricsResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type State = "idle" | "loading" | "success" | "error";

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
    <div className="flex flex-col items-center gap-8 w-full max-w-2xl mx-auto px-4 py-16">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">Lyra</h1>
        <p className="mt-2 text-muted-foreground">
          Cole um link do Spotify para ver a letra
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 w-full">
        <Input
          type="url"
          placeholder="https://open.spotify.com/track/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={state === "loading"}
          className="flex-1 h-10"
        />
        <Button
          type="submit"
          size="lg"
          disabled={state === "loading" || !url.trim()}
        >
          {state === "loading" ? "Buscando…" : "Buscar"}
        </Button>
      </form>

      {state === "error" && (
        <p className="text-destructive text-sm text-center">{errorMessage}</p>
      )}

      {state === "success" && result && (
        <Card className="w-full">
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="text-lg">{result.title}</CardTitle>
                <CardDescription>{result.artist}</CardDescription>
              </div>
              <Badge variant="secondary">{result.provider}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground max-h-[60vh] overflow-y-auto">
              {result.lyrics}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
