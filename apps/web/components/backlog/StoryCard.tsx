"use client";

import type { AcceptanceCriterion, UserStory } from "@po-agent/contracts";
import { useState } from "react";
import { ApprovalActions } from "./ApprovalActions";
import { EditControls } from "./EditControls";
import { SourceList } from "./SourceList";
import { StatusBadge } from "./StatusBadge";

const DISCIPLINE_STYLE: Record<string, string> = {
  frontend: "bg-accent-wash-2 text-accent-soft",
};

export function StoryCard({
  story,
  index,
  onSave,
}: {
  story: UserStory;
  index: number;
  onSave: (updates: Record<string, unknown>) => Promise<void>;
}) {
  const [isOpen, setIsOpen] = useState(story.status === "draft");
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [title, setTitle] = useState(story.title);
  const [asA, setAsA] = useState(story.asA);
  const [iWant, setIWant] = useState(story.iWant);
  const [soThat, setSoThat] = useState(story.soThat);
  const [criteria, setCriteria] = useState<AcceptanceCriterion[]>(
    story.acceptanceCriteria,
  );

  const storyLabel = `US-${String(index + 1).padStart(2, "0")}`;

  async function persist(updates: Record<string, unknown>) {
    setIsSaving(true);
    try {
      await onSave(updates);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSave() {
    await persist({ title, asA, iWant, soThat, acceptanceCriteria: criteria });
    setIsEditing(false);
  }

  function handleCancel() {
    setTitle(story.title);
    setAsA(story.asA);
    setIWant(story.iWant);
    setSoThat(story.soThat);
    setCriteria(story.acceptanceCriteria);
    setIsEditing(false);
  }

  function updateCriterion(
    idx: number,
    field: "given" | "when" | "then",
    value: string,
  ) {
    setCriteria((prev) =>
      prev.map((criterion, i) =>
        i === idx ? { ...criterion, [field]: value } : criterion,
      ),
    );
  }

  function addCriterion() {
    setCriteria((prev) => [
      ...prev,
      { id: `local_${Date.now()}_${prev.length}`, given: "", when: "", then: "" },
    ]);
  }

  function removeCriterion(idx: number) {
    setCriteria((prev) => prev.filter((_, i) => i !== idx));
  }

  const pointsBadge = story.estimate && (
    <span
      className="inline-flex shrink-0 items-baseline gap-1 rounded-md px-[9px] py-[3px] font-mono text-[12px] text-accent-soft"
      style={{ boxShadow: "inset 0 0 0 1px var(--color-accent-ring)" }}
    >
      {story.estimate.storyPoints}
      <span className="text-[10px] text-text-4">pts</span>
    </span>
  );

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="flex w-full cursor-pointer items-center gap-3 rounded-md bg-surface px-4 py-3 text-left shadow-[inset_0_0_0_1px_var(--color-border)]"
      >
        <span className="font-mono text-[11px] text-text-5">{storyLabel}</span>
        <span className="text-[15px] font-medium">{story.title}</span>
        <StatusBadge status={story.status} size="sm" />
        <span className="mr-auto text-[11.5px] text-text-5">
          {story.acceptanceCriteria.length} criterios · {story.subtasks.length}{" "}
          subtareas · {story.sources.length} fuentes
        </span>
        {pointsBadge}
      </button>
    );
  }

  return (
    <div
      className="flex flex-col gap-3 rounded-lg bg-surface px-4 py-3.5"
      style={{
        boxShadow: isEditing
          ? "inset 0 0 0 1.5px var(--color-accent)"
          : "inset 0 0 0 1px var(--color-border)",
      }}
    >
      <div className="flex items-start gap-3">
        <div className="mr-auto flex flex-wrap items-center gap-2.5">
          <span className="font-mono text-[11px] text-text-5">{storyLabel}</span>
          {isEditing ? (
            <input
              className="h-8 min-w-[240px] rounded-md bg-surface-2 px-[10px] text-[15px] font-medium shadow-[inset_0_0_0_1px_var(--color-accent)] focus:outline-none"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          ) : (
            <>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="cursor-pointer text-[16px] font-medium"
              >
                {story.title}
              </button>
              <StatusBadge status={story.status} />
            </>
          )}
        </div>
        {pointsBadge}
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
            status={story.status}
            isSaving={isSaving}
            onApprove={() => persist({ status: "approved" })}
            onDiscard={() => persist({ status: "discarded" })}
            size="sm"
          />
        </div>
      </div>

      {isEditing ? (
        <div className="grid grid-cols-[auto_1fr] items-center gap-2 py-2">
          <span className="text-[11px] tracking-[.06em] text-text-5 uppercase">
            Como
          </span>
          <input
            className="h-[34px] rounded-md bg-surface-2 px-[11px] text-[13.5px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
            value={asA}
            onChange={(event) => setAsA(event.target.value)}
          />
          <span className="text-[11px] tracking-[.06em] text-text-5 uppercase">
            Quiero
          </span>
          <input
            className="h-[34px] rounded-md bg-surface-2 px-[11px] text-[13.5px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
            value={iWant}
            onChange={(event) => setIWant(event.target.value)}
          />
          <span className="text-[11px] tracking-[.06em] text-text-5 uppercase">
            Para
          </span>
          <input
            className="h-[34px] rounded-md bg-surface-2 px-[11px] text-[13.5px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
            value={soThat}
            onChange={(event) => setSoThat(event.target.value)}
          />
        </div>
      ) : (
        <div
          className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 rounded-lg bg-accent-wash px-[14px] py-3 text-[14px] leading-[1.5]"
          style={{ boxShadow: "inset 2px 0 0 var(--color-accent-ring)" }}
        >
          <span className="pt-1 text-[11px] tracking-[.06em] text-text-5 uppercase">
            Como
          </span>
          <span>{story.asA}</span>
          <span className="pt-1 text-[11px] tracking-[.06em] text-text-5 uppercase">
            Quiero
          </span>
          <span>{story.iWant}</span>
          <span className="pt-1 text-[11px] tracking-[.06em] text-text-5 uppercase">
            Para
          </span>
          <span>{story.soThat}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-[1.35fr_1fr]">
        <div className="flex flex-col gap-2">
          {(isEditing ? criteria : story.acceptanceCriteria).length > 0 && (
            <span className="text-[11px] tracking-[.08em] text-text-4 uppercase">
              Criterios de aceptación
            </span>
          )}
          <ol className="m-0 flex list-none flex-col gap-[7px] p-0">
            {(isEditing ? criteria : story.acceptanceCriteria).map(
              (criterion, i) => (
                <li
                  key={criterion.id}
                  className="grid grid-cols-[18px_1fr] gap-2 text-[13px] leading-[1.5]"
                >
                  <span className="pt-0.5 font-mono text-[11.5px] text-accent-strong">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {isEditing ? (
                    <div className="flex flex-wrap items-center gap-[6px]">
                      <input
                        className="h-8 flex-1 rounded-[6px] bg-surface-2 px-[10px] text-[12.5px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
                        placeholder="dado"
                        value={criterion.given}
                        onChange={(event) =>
                          updateCriterion(i, "given", event.target.value)
                        }
                      />
                      <input
                        className="h-8 flex-1 rounded-[6px] bg-surface-2 px-[10px] text-[12.5px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
                        placeholder="cuando"
                        value={criterion.when}
                        onChange={(event) =>
                          updateCriterion(i, "when", event.target.value)
                        }
                      />
                      <input
                        className="h-8 flex-1 rounded-[6px] bg-surface-2 px-[10px] text-[12.5px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
                        placeholder="entonces"
                        value={criterion.then}
                        onChange={(event) =>
                          updateCriterion(i, "then", event.target.value)
                        }
                      />
                      <button
                        type="button"
                        onClick={() => removeCriterion(i)}
                        aria-label="Eliminar criterio"
                        className="inline-flex h-[26px] w-[26px] shrink-0 cursor-pointer items-center justify-center rounded-[6px] text-[12px] text-text-4 shadow-[inset_0_0_0_1px_var(--color-border-soft-2)]"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <span className="text-text-2">
                      <span className="text-text-4">Dado que</span> {criterion.given}
                      {", "}
                      <span className="text-text-4">cuando</span> {criterion.when}
                      {", "}
                      <span className="text-text-4">entonces</span> {criterion.then}
                      {"."}
                    </span>
                  )}
                </li>
              ),
            )}
          </ol>
          {isEditing && (
            <button
              type="button"
              onClick={addCriterion}
              className="ml-7 cursor-pointer self-start text-[12.5px] text-accent-soft"
            >
              + agregar criterio
            </button>
          )}
        </div>

        <div
          className={`flex flex-col gap-3.5 ${isEditing ? "opacity-55" : ""}`}
        >
          {story.subtasks.length > 0 && (
            <div className="flex flex-col gap-2">
              <span className="text-[11px] tracking-[.08em] text-text-4 uppercase">
                Subtareas{isEditing ? " · solo lectura" : ""}
              </span>
              <div className="flex flex-col gap-[6px] text-[12.5px] text-text-2">
                {story.subtasks.map((subtask) => (
                  <span key={subtask.id} className="flex items-center gap-2">
                    <span
                      className={`min-w-[74px] rounded-[4px] px-[6px] py-[2px] text-center font-mono text-[10px] ${
                        DISCIPLINE_STYLE[subtask.discipline] ??
                        "bg-draft-wash text-text-2"
                      }`}
                    >
                      {subtask.discipline}
                    </span>
                    {subtask.title}
                  </span>
                ))}
              </div>
            </div>
          )}

          {story.estimate && (
            <div className="flex flex-col gap-1">
              <span className="text-[11px] tracking-[.08em] text-text-4 uppercase">
                Estimación{isEditing ? " · solo lectura" : ""}
              </span>
              <span className="text-[12.5px] text-text-3 [text-wrap:pretty]">
                {story.estimate.storyPoints} pts — {story.estimate.rationale}
              </span>
            </div>
          )}
        </div>
      </div>

      {((story.refinement.risks?.length ?? 0) > 0 ||
        (story.refinement.openQuestions?.length ?? 0) > 0) && (
        <div className="flex flex-wrap gap-2.5">
          {story.refinement.risks?.map((risk, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-2 rounded-md bg-discarded-wash-soft px-[10px] py-[6px] text-[12.5px] text-text-2"
              style={{ boxShadow: "inset 0 0 0 1px var(--color-discarded-ring-soft)" }}
            >
              <span className="text-[10px] tracking-[.08em] text-discarded-text uppercase">
                Riesgo
              </span>
              {risk}
            </span>
          ))}
          {story.refinement.openQuestions?.map((question, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-2 rounded-md bg-accent-wash px-[10px] py-[6px] text-[12.5px] text-text-2"
              style={{ boxShadow: "inset 0 0 0 1px var(--color-accent-ring-soft)" }}
            >
              <span className="text-[10px] tracking-[.08em] text-accent-soft uppercase">
                Pregunta
              </span>
              {question}
            </span>
          ))}
        </div>
      )}

      <SourceList sources={story.sources} />
    </div>
  );
}
