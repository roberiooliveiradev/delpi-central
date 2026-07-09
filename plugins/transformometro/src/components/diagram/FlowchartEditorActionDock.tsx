import { DIAGRAM_EDITOR_SELECTION_ACTIONS } from "./flowchartEditorToolbar";
import { DiagramEditorActionDockButton } from "./DiagramEditorActionDockButton";

type Props = {
  clipboardReady: boolean;
  onSelectionAction: (actionId: (typeof DIAGRAM_EDITOR_SELECTION_ACTIONS)[number]["id"]) => void;
  isSelectionActionDisabled: (
    actionId: (typeof DIAGRAM_EDITOR_SELECTION_ACTIONS)[number]["id"]
  ) => boolean;
};

export function FlowchartEditorActionDock({
  clipboardReady,
  onSelectionAction,
  isSelectionActionDisabled,
}: Props) {
  return (
    <div
      className="tm-diagram-editor__action-dock"
      role="toolbar"
      aria-label="Ações de seleção do diagrama"
    >
      {DIAGRAM_EDITOR_SELECTION_ACTIONS.map((action) => {
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
