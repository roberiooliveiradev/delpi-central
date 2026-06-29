import { GripVertical, X } from "lucide-react";
import type { DragEvent, HTMLAttributes } from "react";

type DragHandleProps = {
  draggable: boolean;
  onDragStart: (event: DragEvent) => void;
  onDragEnd: () => void;
};

type RowActionsProps = {
  dragProps?: DragHandleProps;
  onRemove: () => void;
  removeDisabled?: boolean;
  removeTitle?: string;
  removeAriaLabel?: string;
};

export function DragHandle({
  dragProps,
  className,
}: {
  dragProps: DragHandleProps;
  className?: string;
}) {
  const handleClass = ["pac-drag-handle", className].filter(Boolean).join(" ");

  return (
    <span
      className={handleClass}
      title="Arrastar para reordenar"
      aria-label="Arrastar para reordenar"
      {...dragProps}
    >
      <GripVertical size={16} aria-hidden="true" />
    </span>
  );
}

export function RowActions({
  dragProps,
  onRemove,
  removeDisabled = false,
  removeTitle,
  removeAriaLabel = "Remover linha",
}: RowActionsProps) {
  return (
    <div className="pac-row-order-actions">
      {dragProps?.draggable ? <DragHandle dragProps={dragProps} /> : null}
      <button
        type="button"
        className="pac-ghost-btn pac-ghost-btn--icon"
        aria-label={removeAriaLabel}
        disabled={removeDisabled}
        title={removeTitle}
        onClick={onRemove}
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}

export function RemoveRowButton({
  onRemove,
  removeDisabled = false,
  removeTitle,
  removeAriaLabel = "Remover linha",
  className,
}: Omit<RowActionsProps, "dragProps"> & Pick<HTMLAttributes<HTMLButtonElement>, "className">) {
  return (
    <button
      type="button"
      className={["pac-ghost-btn pac-ghost-btn--icon", className].filter(Boolean).join(" ")}
      aria-label={removeAriaLabel}
      disabled={removeDisabled}
      title={removeTitle}
      onClick={onRemove}
    >
      <X size={16} aria-hidden="true" />
    </button>
  );
}
