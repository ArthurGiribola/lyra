"use client";

import { useRef, useState, useEffect, useMemo } from "react";
import type { SyncedLine } from "@/lib/api";

interface Props {
  lines: SyncedLine[];
  durationMs: number | null;
}

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export default function SyncedLyrics({ lines, durationMs }: Props) {
  const visibleLines = useMemo(
    () => lines.filter((l) => l.text.trim() !== ""),
    [lines],
  );

  const totalMs = useMemo(
    () => durationMs ?? (visibleLines.at(-1)?.time_ms ?? 0) + 5000,
    [durationMs, visibleLines],
  );

  const [elapsed, setElapsed] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const elapsedAtPauseRef = useRef(0);
  const startTimeRef = useRef(0);
  const lineRefs = useRef<(HTMLParagraphElement | null)[]>([]);

  useEffect(() => {
    if (!playing) return;

    startTimeRef.current = performance.now();
    let rafId: number;

    function tick() {
      const now = performance.now();
      const ms = elapsedAtPauseRef.current + (now - startTimeRef.current);
      const clamped = Math.min(ms, totalMs);

      let newActiveIndex = -1;
      for (let i = 0; i < visibleLines.length; i++) {
        if (visibleLines[i].time_ms <= clamped) newActiveIndex = i;
        else break;
      }

      setElapsed(clamped);
      setActiveIndex(newActiveIndex);

      if (clamped >= totalMs) {
        elapsedAtPauseRef.current = totalMs;
        setPlaying(false);
        return;
      }

      rafId = requestAnimationFrame(tick);
    }

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [playing, visibleLines, totalMs]);

  useEffect(() => {
    if (activeIndex >= 0) {
      lineRefs.current[activeIndex]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [activeIndex]);

  function handlePlayPause() {
    if (playing) {
      elapsedAtPauseRef.current = elapsed;
      setPlaying(false);
    } else {
      setPlaying(true);
    }
  }

  function handleReset() {
    elapsedAtPauseRef.current = 0;
    setElapsed(0);
    setActiveIndex(-1);
    setPlaying(false);
  }

  const notStarted = elapsed === 0 && !playing;
  const progress = totalMs > 0 ? Math.min(elapsed / totalMs, 1) : 0;

  return (
    <div className="w-full">
      {/* Controls */}
      <div className="sticky top-4 z-10 rounded-2xl border border-white/[0.08] bg-background/90 backdrop-blur-md px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Reset */}
          <button
            onClick={handleReset}
            aria-label="Reiniciar"
            className="flex size-7 items-center justify-center rounded-full text-muted-foreground/50 hover:bg-white/[0.06] hover:text-foreground transition-all"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
            </svg>
          </button>

          {/* Play/Pause */}
          <button
            onClick={handlePlayPause}
            aria-label={playing ? "Pausar" : "Reproduzir"}
            className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:brightness-110 active:scale-95"
          >
            {playing ? (
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <rect x="6" y="4" width="4" height="16" />
                <rect x="14" y="4" width="4" height="16" />
              </svg>
            ) : (
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            )}
          </button>

          {/* Lyric position indicator */}
          <span className="shrink-0 tabular-nums text-xs text-muted-foreground/40">
            {formatTime(elapsed)}
          </span>

          {/* Sync track — shows position in lyrics, not audio playback */}
          <div className="relative flex h-3 flex-1 items-center">
            <div className="absolute inset-x-0 h-px rounded-full bg-white/[0.07]" />
            <div
              className="absolute inset-y-0 left-0 my-auto h-px rounded-full bg-primary/50"
              style={{ width: `${progress * 100}%` }}
            />
            {/* Position marker */}
            {elapsed > 0 && (
              <div
                className="absolute size-1.5 -translate-x-1/2 rounded-full bg-primary/80"
                style={{
                  left: `clamp(3px, ${progress * 100}%, calc(100% - 3px))`,
                }}
              />
            )}
          </div>

          <span className="shrink-0 tabular-nums text-xs text-muted-foreground/30">
            {formatTime(totalMs)}
          </span>
        </div>
      </div>

      {/* Hint */}
      <p
        className={[
          "mt-3 mb-6 text-center text-xs text-muted-foreground/35 transition-opacity duration-500",
          notStarted ? "opacity-100" : "opacity-0",
        ].join(" ")}
      >
        Abra a música no Spotify e pressione ▶ aqui para sincronizar a letra.
      </p>

      {/* Lines */}
      <div className="space-y-5 pb-16">
        {visibleLines.map((line, i) => {
          const isActive = i === activeIndex;
          const isPast = i < activeIndex;
          return (
            <p
              key={i}
              ref={(el) => {
                lineRefs.current[i] = el;
              }}
              className={[
                "leading-8 transition-all duration-300 cursor-default select-none",
                notStarted
                  ? "text-[15px] text-foreground/60"
                  : isActive
                    ? "text-[17px] font-semibold text-primary"
                    : isPast
                      ? "text-[15px] text-foreground/35"
                      : "text-[15px] text-foreground/25",
              ].join(" ")}
            >
              {line.text}
            </p>
          );
        })}
      </div>
    </div>
  );
}
