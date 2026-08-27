import type { ArtifactStatus } from "@po-agent/contracts";

const LABELS: Record<ArtifactStatus, string> = {
  draft: "Borrador",
  approved: "Aprobado",
  discarded: "Descartado",
};

const TOKEN: Record<ArtifactStatus, string> = {
  draft: "draft",
  approved: "approved",
  discarded: "discarded",
};

export function StatusBadge({
  status,
  size = "md",
}: {
  status: ArtifactStatus;
  size?: "sm" | "md";
}) {
  const token = TOKEN[status];
  const height = size === "sm" ? "h-[22px]" : "h-[24px]";
  const dotSize = size === "sm" ? "h-[6px] w-[6px]" : "h-[7px] w-[7px]";

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-[7px] ${height} rounded-md py-[3px] pr-[9px] pl-[7px] text-[11.5px]`}
      style={{
        background: `var(--color-${token}-wash)`,
        boxShadow: `inset 0 0 0 1px var(--color-${token}-ring)`,
        color: `var(--color-${token}-text)`,
      }}
    >
      <span
        className={`${dotSize} rounded-full`}
        style={{ background: `var(--color-${token})` }}
      />
      {LABELS[status]}
    </span>
  );
}
