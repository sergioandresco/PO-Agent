"use client";

import type { Epic } from "@po-agent/contracts";
import { type ReactNode, useState } from "react";
import { ApprovalActions } from "./ApprovalActions";
import { EditControls } from "./EditControls";
import { StatusBadge } from "./StatusBadge";

export function EpicSection({
  epic,
  featureCount,
  storyCount,
  onSave,
  children,
}: {
  epic: Epic;
  featureCount: number;
  storyCount: number;
  onSave: (updates: Record<string, unknown>) => Promise<void>;
  children: ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [title, setTitle] = useState(epic.title);
  const [description, setDescription] = useState(epic.description);

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
    setTitle(epic.title);
    setDescription(epic.description);
    setIsEditing(false);
  }

  const kicker = `Épica · ${featureCount} ${featureCount === 1 ? "feature" : "features"} · ${storyCount} ${storyCount === 1 ? "historia" : "historias"}`;

  return (
    <div className="flex flex-col gap-3.5 rounded-lg bg-panel px-[18px] pt-[18px] pb-5 shadow-[inset_0_0_0_1px_var(--color-border)]">
      <div className="flex items-start gap-3">
        <button
          type="button"
          onClick={() => setIsOpen((open) => !open)}
          className="mt-1.5 shrink-0 cursor-pointer font-mono text-[13px] text-text-4"
          aria-label={isOpen ? "Colapsar épica" : "Expandir épica"}
        >
          {isOpen ? "⌄" : "›"}
        </button>
        <div className="mr-auto flex flex-col gap-1.5">
          <span className="font-mono text-[10.5px] tracking-[.08em] text-text-5 uppercase">
            {kicker}
          </span>
          <div className="flex flex-wrap items-center gap-2.5">
            {isEditing ? (
              <input
                className="h-9 min-w-[280px] rounded-md bg-surface-2 px-[11px] text-[20px] shadow-[inset_0_0_0_1px_var(--color-accent)] focus:outline-none"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            ) : (
              <h3 className="m-0 text-[23px] font-medium tracking-[-.015em]">
                {epic.title}
              </h3>
            )}
            {!isEditing && <StatusBadge status={epic.status} />}
          </div>
        </div>
        <div className="flex gap-1 pt-1">
          <EditControls
            isEditing={isEditing}
            isSaving={isSaving}
            onEdit={() => setIsEditing(true)}
            onSave={handleSave}
            onCancel={handleCancel}
          />
          <ApprovalActions
            status={epic.status}
            isSaving={isSaving}
            onApprove={() => persist({ status: "approved" })}
            onDiscard={() => persist({ status: "discarded" })}
          />
        </div>
      </div>

      {isOpen && (
        <>
          {isEditing ? (
            <label className="ml-[25px] flex max-w-[600px] flex-col gap-[3px]">
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
            epic.description && (
              <p className="m-0 ml-[25px] max-w-[82ch] text-[13.5px] text-text-3 [text-wrap:pretty]">
                {epic.description}
              </p>
            )
          )}
          <div className="ml-[25px] flex flex-col gap-3 border-l border-border-soft-3 pl-[18px]">
            {children}
          </div>
        </>
      )}
    </div>
  );
}
