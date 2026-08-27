"use client";

export function EditControls({
  isEditing,
  isSaving,
  onEdit,
  onSave,
  onCancel,
  size = "md",
}: {
  isEditing: boolean;
  isSaving: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  size?: "sm" | "md";
}) {
  const height = size === "sm" ? "h-[26px]" : "h-[28px]";

  if (!isEditing) {
    return (
      <button
        type="button"
        onClick={onEdit}
        className={`inline-flex ${height} shrink-0 cursor-pointer items-center rounded-[7px] px-[10px] text-[12px] text-text-2 shadow-[inset_0_0_0_1px_var(--color-border-soft-2)]`}
      >
        Editar
      </button>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={onSave}
        disabled={isSaving}
        className={`inline-flex ${height} shrink-0 cursor-pointer items-center rounded-md px-[14px] text-[12.5px] font-medium text-accent-soft shadow-[inset_0_0_0_1px_var(--color-accent)] disabled:cursor-default disabled:opacity-50`}
      >
        {isSaving ? "Guardando…" : "Guardar"}
      </button>
      <button
        type="button"
        onClick={onCancel}
        disabled={isSaving}
        className={`inline-flex ${height} shrink-0 cursor-pointer items-center rounded-md px-[12px] text-[12.5px] text-text-4 disabled:cursor-default disabled:opacity-50`}
      >
        Cancelar
      </button>
    </>
  );
}
