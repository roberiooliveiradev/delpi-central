import type { PointerEvent } from "react";

import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import type { DiagramEditorAction } from "./flowchartEditorToolbar";
import { DiagramEditorActionDockButton } from "./DiagramEditorActionDockButton";

type Props = {
  labels: FlowchartEditorLabels;
  selectionActions: DiagramEditorAction[];
  clipboardReady: boolean;
  onSelectionAction: (actionId: DiagramEditorAction["id"]) => void;
  isSelectionActionDisabled: (actionId: DiagramEditorAction["id"]) => boolean;
  onPointerDownCapture?: (event: PointerEvent<HTMLDivElement>) => void;
  /** `statusbar` = faixa inferior horizontal; `floating` = legado vertical. */
  variant?: "statusbar" | "floating";
};

export function FlowchartEditorActionDock({
  labels,
  selectionActions,
  clipboardReady,
  onSelectionAction,
  isSelectionActionDisabled,
  onPointerDownCapture,
  variant = "statusbar",
}: Props) {
  return (
    <div
      className={[
        "delpi-ui-bpmn-editor__action-dock",
        variant === "statusbar"
          ? "delpi-ui-bpmn-editor__action-dock--statusbar"
          : "delpi-ui-bpmn-editor__action-dock--floating",
      ].join(" ")}
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
            variant={variant}
            onClick={() => onSelectionAction(action.id)}
          />
        );
      })}
    </div>
  );
}
