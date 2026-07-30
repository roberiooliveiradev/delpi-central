import { EditorHistoryActions } from "../../layout/EditorHistoryActions";
import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";

type Props = {
  labels: FlowchartEditorLabels;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
};

/** Desfazer/refazer do editor BPMN — chrome canônico {@link EditorHistoryActions}. */
export function FlowchartEditorHistoryActions({
  labels,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
}: Props) {
  return (
    <EditorHistoryActions
      canUndo={canUndo}
      canRedo={canRedo}
      onUndo={onUndo}
      onRedo={onRedo}
      undoLabel={labels.undo}
      redoLabel={labels.redo}
      undoHint={labels.undoHint}
      redoHint={labels.redoHint}
      ariaLabel={labels.historyAriaLabel}
      className="delpi-ui-bpmn-editor__history"
    />
  );
}
