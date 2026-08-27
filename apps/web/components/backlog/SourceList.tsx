"use client";

import type { SourceReference } from "@po-agent/contracts";
import { useState } from "react";

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const hh = Math.floor(totalSeconds / 3600);
  const mm = Math.floor((totalSeconds % 3600) / 60);
  const ss = totalSeconds % 60;
  const parts = [mm, ss].map((n) => String(n).padStart(2, "0"));
  return hh > 0 ? `${String(hh).padStart(2, "0")}:${parts.join(":")}` : parts.join(":");
}

function summarize(sources: SourceReference[]): string {
  const speakers = [...new Set(sources.map((s) => s.speaker).filter(Boolean))];
  const timestamps = sources
    .map((s) => s.startTimeMs)
    .filter((t): t is number => typeof t === "number");

  const speakerPart = speakers.join(", ");
  if (timestamps.length === 0) return speakerPart;

  const min = Math.min(...timestamps);
  const max = Math.max(...timestamps);
  const rangePart = min === max ? formatTime(min) : `${formatTime(min)}–${formatTime(max)}`;
  return speakerPart ? `${speakerPart} · ${rangePart}` : rangePart;
}

export function SourceList({ sources }: { sources: SourceReference[] }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex items-center gap-2 pt-0.5">
        <button
          type="button"
          onClick={() => setIsOpen((open) => !open)}
          className="inline-flex cursor-pointer items-center gap-[7px] rounded-md px-[10px] py-[5px] text-[12px] text-accent"
          style={{ boxShadow: "inset 0 0 0 1px var(--color-accent-ring)" }}
        >
          <span className="font-mono text-[11px]">{isOpen ? "⌄" : "›"}</span>
          Ver fuente ({sources.length})
        </button>
        <span className="text-[11.5px] text-text-5">{summarize(sources)}</span>
      </div>

      {isOpen && (
        <div
          className="flex flex-col gap-2.5 rounded-md bg-surface-2 px-[14px] py-3"
          style={{ boxShadow: "inset 0 0 0 1px var(--color-accent-ring-soft)" }}
        >
          {sources.map((source, index) => (
            <div key={index} className="grid grid-cols-[2px_1fr] gap-2.5 pl-0.5">
              <span
                className="rounded-[1px]"
                style={{ background: "var(--color-accent-ring)" }}
              />
              <div className="flex flex-col gap-[3px]">
                <span className="font-mono text-[13px] leading-[1.6] text-text">
                  &ldquo;{source.verbatim}&rdquo;
                </span>
                <span className="font-mono text-[11px] text-text-5">
                  {source.speaker ?? "Desconocido"}
                  {typeof source.startTimeMs === "number"
                    ? ` · ${formatTime(source.startTimeMs)}`
                    : ""}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
