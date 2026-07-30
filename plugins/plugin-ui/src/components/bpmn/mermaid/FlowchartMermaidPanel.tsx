import { RefreshCw, Wand2 } from "lucide-react";

import { NativeTextAreaControl } from "../../forms/NativeTextAreaControl";
import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import { DiagramMermaidPreview } from "./DiagramMermaidPreview";
import type { DiagramEditorLayout } from "../shell/DiagramLayoutContext";

type Props = {
  labels: FlowchartEditorLabels;
  draft: string;
  onDraftChange: (code: string) => void;
  onApply: () => void;
  onRefreshFromCanvas: () => void;
  onUseTemplate: () => void;
  readOnly: boolean;
  layout: DiagramEditorLayout;
  applyError: string | null;
  applying: boolean;
  isEmpty: boolean;
  isDark?: boolean;
  /** Quando false, ações ficam no chrome (topbar). */
  showToolbar?: boolean;
};

export function FlowchartMermaidPanel({
  labels,
  draft,
  onDraftChange,
  onApply,
  onRefreshFromCanvas,
  onUseTemplate,
  readOnly,
  layout,
  applyError,
  applying,
  isEmpty,
  isDark,
  showToolbar = true,
}: Props) {
  return (
    <div
      className={[
        "delpi-ui-bpmn-editor__mermaid-panel",
        layout === "fill" ? "delpi-ui-bpmn-editor__mermaid-panel--fill" : "",
        !showToolbar || readOnly ? "delpi-ui-bpmn-editor__mermaid-panel--chrome" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!readOnly && showToolbar ? (
        <div className="delpi-ui-bpmn-editor__mermaid-toolbar">
          <button type="button" className="ds-ghost-btn" onClick={onRefreshFromCanvas}>
            <RefreshCw size={16} aria-hidden />
            {labels.mermaidRefreshFromDrawing}
          </button>
          {isEmpty ? (
            <button type="button" className="ds-ghost-btn" onClick={onUseTemplate}>
              <Wand2 size={16} aria-hidden />
              {labels.mermaidStarterTemplate}
            </button>
          ) : null}
          <button
            type="button"
            className="ds-primary-btn"
            disabled={applying || !draft.trim()}
            onClick={onApply}
          >
            {applying ? labels.mermaidApplying : labels.mermaidApplyToDrawing}
          </button>
        </div>
      ) : null}

      {applyError ? (
        <div className="ds-state ds-state--warn delpi-ui-bpmn-editor__mermaid-alert" role="alert">
          {applyError}
        </div>
      ) : null}

      {readOnly ? (
        <pre className="delpi-ui-bpmn-editor__mermaid-code">{draft || labels.mermaidReadonlyEmpty}</pre>
      ) : (
        <NativeTextAreaControl
          className="delpi-ui-bpmn-editor__mermaid-input"
          value={draft}
          spellCheck={false}
          aria-label={labels.mermaidCodeAriaLabel}
          onChange={onDraftChange}
        />
      )}

      <DiagramMermaidPreview
        code={draft}
        className="delpi-ui-bpmn-editor__mermaid-preview"
        isDark={isDark}
        renderingLabel={labels.mermaidRendering}
        errorFallback={labels.mermaidRenderError}
      />
    </div>
  );
}
