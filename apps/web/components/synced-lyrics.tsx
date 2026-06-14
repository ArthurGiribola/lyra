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
      const maxMs =
        durationMs ??
        (visibleLines[visibleLines.length - 1]?.time_ms ?? 0) + 5000;
      const clamped = Math.min(ms, maxMs);

      let newActiveIndex = -1;
      for (let i = 0; i < visibleLines.length; i++) {
        if (visibleLines[i].time_ms <= clamped) newActiveIndex = i;
        else break;
      }

      setElapsed(clamped);
      setActiveIndex(newActiveIndex);

      if (clamped >= maxMs) {
        elapsedAtPauseRef.current = maxMs;
        setPlaying(false);
        return;
      }

      rafId = requestAnimationFrame(tick);
    }

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [playing, visibleLines, durationMs]);

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

  const prePlay = activeIndex === -1;

  return (
    <div className="w-full">
      {/* Controls */}
      <div className="sticky top-4 z-10 mb-8 flex w-fit mx-auto items-center gap-3 rounded-full border border-white/[0.08] bg-background/90 backdrop-blur-md px-4 py-2">
        <button
          onClick={handleReset}
          aria-label="Reiniciar"
          className="text-muted-foreground/50 hover:text-foreground transition-colors"
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

        <button
          onClick={handlePlayPause}
          aria-label={playing ? "Pausar" : "Reproduzir"}
          className="flex size-8 items-center justify-center rounded-full bg-primary text-primary-foreground hover:brightness-110 transition-all active:scale-95"
        >
          {playing ? (
            <svg
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          ) : (
            <svg
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          )}
        </button>

        <span className="min-w-[36px] tabular-nums text-xs text-muted-foreground/50">
          {formatTime(elapsed)}
        </span>
      </div>

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
                prePlay
                  ? "text-[15px] text-foreground/60"
                  : isActive
                    ? "text-[17px] font-medium text-foreground"
                    : isPast
                      ? "text-[15px] text-muted-foreground opacity-40"
                      : "text-[15px] text-muted-foreground opacity-25",
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
