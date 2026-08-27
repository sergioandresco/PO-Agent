"use client";

import type { BacklogResult } from "@po-agent/contracts";
import { useState } from "react";

export function RawJsonViewer({ result }: { result: BacklogResult }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="flex cursor-pointer items-center gap-2 self-start rounded-md px-[14px] py-[10px] font-mono text-[12px] text-text-4 shadow-[inset_0_0_0_1px_var(--color-border-soft-3)]"
      >
        <span>{isOpen ? "⌄" : "›"}</span> Ver JSON crudo{" "}
        <span className="text-text-6">· BacklogResult</span>
      </button>
      {isOpen && (
        <pre className="max-h-[600px] overflow-auto rounded-md bg-surface-2 p-4 font-mono text-xs text-text-2 shadow-[inset_0_0_0_1px_var(--color-border)]">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
