import type { PointerEvent } from "react";

import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";
import type { DiagramEditorAction } from "./flowchartEditorToolbar";
import { DiagramEditorActionDockButton } from "./DiagramEditorActionDockButton";

type Props = {
  labels: FlowchartEditorLabels;
  selectionActions: DiagramEditorAction[];
  clipboardReady: boolean;
  onSelectionAction: (actionId: DiagramEditorAction["id"]) => void;
  isSelectionActionDisabled: (actionId: DiagramEditorAction["id"]) => boolean;
  onPointerDownCapture?: (event: PointerEvent<HTMLDivElement>) => void;
};

export function FlowchartEditorActionDock({
  labels,
  selectionActions,
  clipboardReady,
  onSelectionAction,
  isSelectionActionDisabled,
  onPointerDownCapture,
}: Props) {
  return (
    <div
      className="tm-diagram-editor__action-dock"
      role="toolbar"
      aria-label={labels.selectionDockAriaLabel}
      onPointerDownCapture={onPointerDownCapture}
    >
      {selectionActions.map((action) => {
        const disabled = isSelectionActionDisabled(action.id);
        const active =
          action.id === "paste"
            ? clipboardReady && !disabled
            : action.id === "delete" || action.id === "copy" || action.id === "duplicate"
              ? !disabled
              : false;

        return (
          <DiagramEditorActionDockButton
            key={action.id}
            label={action.label}
            hint={action.hint}
            icon={action.icon}
            disabled={disabled}
            active={active}
            onClick={() => onSelectionAction(action.id)}
          />
        );
      })}
    </div>
  );
}
