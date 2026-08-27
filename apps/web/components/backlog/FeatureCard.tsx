"use client";

import type { Feature } from "@po-agent/contracts";
import { type ReactNode, useState } from "react";
import { ApprovalActions } from "./ApprovalActions";
import { EditControls } from "./EditControls";
import { StatusBadge } from "./StatusBadge";

export function FeatureCard({
  feature,
  storyCount,
  onSave,
  children,
}: {
  feature: Feature;
  storyCount: number;
  onSave: (updates: Record<string, unknown>) => Promise<void>;
  children: ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(feature.status === "draft");
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [title, setTitle] = useState(feature.title);
  const [description, setDescription] = useState(feature.description);

  const storiesLabel = `${storyCount} ${storyCount === 1 ? "historia" : "historias"}`;

  async function persist(updates: Record<string, unknown>) {
    setIsSaving(true);
    try {
      await onSave(updates);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSave() {
    await persist({ title, description });
    setIsEditing(false);
  }

  function handleCancel() {
    setTitle(feature.title);
    setDescription(feature.description);
    setIsEditing(false);
  }

  if (!isOpen) {
    const isDiscarded = feature.status === "discarded";
    return (
      <div
        role="button"
        tabIndex={0}
        onClick={() => setIsOpen(true)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") setIsOpen(true);
        }}
        className={`flex w-full cursor-pointer items-center gap-3 rounded-md py-3 pr-4 pl-4 text-left shadow-[inset_0_0_0_1px_var(--color-border)] ${isDiscarded ? "opacity-[.72]" : ""}`}
        style={{
          background: isDiscarded ? "var(--color-feature-discarded)" : "var(--color-feature)",
          borderLeft: `2px solid ${isDiscarded ? "var(--color-discarded-ring)" : "var(--color-approved-ring)"}`,
        }}
      >
        <span className="font-mono text-[10.5px] tracking-[.08em] text-text-5 uppercase">
          Feature
        </span>
        <span
          className={`text-[16px] font-medium ${isDiscarded ? "text-text-3 line-through" : ""}`}
        >
          {feature.title}
        </span>
        <StatusBadge status={feature.status} size="sm" />
        <span className="mr-auto text-[11.5px] text-text-5">
          {storiesLabel} {isDiscarded ? "ocultas" : ""}
        </span>
        <div
          className="flex gap-1"
          onClick={(event) => event.stopPropagation()}
        >
          <ApprovalActions
            status={feature.status}
            isSaving={isSaving}
            onApprove={() => persist({ status: "approved" })}
            onDiscard={() => persist({ status: "discarded" })}
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col gap-3 rounded-lg py-3.5 pr-4 pl-4"
      style={{
        background: "var(--color-feature)",
        boxShadow: "inset 0 0 0 1px var(--color-border)",
        borderLeft: "2px solid var(--color-accent)",
      }}
    >
      <div className="flex items-start gap-3">
        <div className="mr-auto flex flex-col gap-[5px]">
          <span className="font-mono text-[10.5px] tracking-[.08em] text-text-5 uppercase">
            Feature · {storiesLabel}
          </span>
          <div className="flex flex-wrap items-center gap-2.5">
            {isEditing ? (
              <input
                className="h-8 min-w-[220px] rounded-md bg-surface-2 px-[10px] text-[17px] shadow-[inset_0_0_0_1px_var(--color-accent)] focus:outline-none"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="cursor-pointer text-[18px] font-medium"
                >
                  {feature.title}
                </button>
                <StatusBadge status={feature.status} />
              </>
            )}
          </div>
        </div>
        <div className="flex gap-1">
          <EditControls
            isEditing={isEditing}
            isSaving={isSaving}
            onEdit={() => setIsEditing(true)}
            onSave={handleSave}
            onCancel={handleCancel}
            size="sm"
          />
          <ApprovalActions
            status={feature.status}
            isSaving={isSaving}
            onApprove={() => persist({ status: "approved" })}
            onDiscard={() => persist({ status: "discarded" })}
            size="sm"
          />
        </div>
      </div>

      {isEditing ? (
        <label className="flex max-w-[560px] flex-col gap-[3px]">
          <span className="text-[10px] tracking-[.06em] text-text-5 uppercase">
            Descripción
          </span>
          <textarea
            className="rounded-md bg-surface-2 px-[11px] py-2 text-[13px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
            rows={2}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
      ) : (
        feature.description && (
          <p className="m-0 max-w-[78ch] text-[13px] text-text-4">
            {feature.description}
          </p>
        )
      )}

      <div className="flex flex-col gap-2.5">{children}</div>
    </div>
  );
}
