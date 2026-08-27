"use client";

import type { ArtifactStatus } from "@po-agent/contracts";

export function ApprovalActions({
  status,
  isSaving,
  onApprove,
  onDiscard,
  size = "md",
}: {
  status: ArtifactStatus;
  isSaving: boolean;
  onApprove: () => void;
  onDiscard: () => void;
  size?: "sm" | "md";
}) {
  const height = size === "sm" ? "h-[26px]" : "h-[28px]";

  return (
    <>
      <button
        type="button"
        onClick={onApprove}
        disabled={isSaving || status === "approved"}
        className={`inline-flex ${height} shrink-0 cursor-pointer items-center rounded-[7px] px-[10px] text-[12px] text-approved-text shadow-[inset_0_0_0_1px_var(--color-approved-ring)] transition-opacity disabled:cursor-default disabled:opacity-45`}
      >
        Aprobar
      </button>
      <button
        type="button"
        onClick={onDiscard}
        disabled={isSaving || status === "discarded"}
        className={`inline-flex ${height} shrink-0 cursor-pointer items-center rounded-[7px] px-[10px] text-[12px] text-discarded-text shadow-[inset_0_0_0_1px_var(--color-discarded-ring)] transition-opacity disabled:cursor-default disabled:opacity-45`}
      >
        Descartar
      </button>
    </>
  );
}
