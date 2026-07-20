import { Redo2, Undo2 } from "lucide-react";

import { HintAction } from "../help/HintAction";
import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";

type Props = {
  labels: FlowchartEditorLabels;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
};

/** Desfazer/refazer — ícones compactos na faixa de abas (padrão TV Dashboard). */
export function FlowchartEditorHistoryActions({
  labels,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
}: Props) {
  return (
    <div className="tm-diagram-editor__history" role="group" aria-label={labels.historyAriaLabel}>
      <HintAction hint={labels.undoHint} ariaLabel={labels.undo}>
        <button
          type="button"
          className="tm-diagram-editor__history-btn"
          disabled={!canUndo}
          onClick={onUndo}
          aria-label={labels.undo}
        >
          <Undo2 size={14} aria-hidden="true" />
        </button>
      </HintAction>
      <HintAction hint={labels.redoHint} ariaLabel={labels.redo}>
        <button
          type="button"
          className="tm-diagram-editor__history-btn"
          disabled={!canRedo}
          onClick={onRedo}
          aria-label={labels.redo}
        >
          <Redo2 size={14} aria-hidden="true" />
        </button>
      </HintAction>
    </div>
  );
}
