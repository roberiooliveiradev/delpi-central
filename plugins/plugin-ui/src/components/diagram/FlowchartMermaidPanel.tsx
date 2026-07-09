import { RefreshCw, Wand2 } from "lucide-react";

import { NativeTextAreaControl } from "../forms/NativeTextAreaControl";
import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";
import { DiagramMermaidPreview } from "./DiagramMermaidPreview";
import type { DiagramEditorLayout } from "./DiagramLayoutContext";

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
}: Props) {
  return (
    <div
      className={[
        "tm-diagram-editor__mermaid-panel",
        layout === "fill" ? "tm-diagram-editor__mermaid-panel--fill" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!readOnly ? (
        <div className="tm-diagram-editor__mermaid-toolbar">
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
        <div className="ds-state ds-state--warn" role="alert">
          {applyError}
        </div>
      ) : null}

      {readOnly ? (
        <pre className="tm-diagram-editor__mermaid-code">{draft || labels.mermaidReadonlyEmpty}</pre>
      ) : (
        <NativeTextAreaControl
          className="tm-diagram-editor__mermaid-input"
          value={draft}
          spellCheck={false}
          aria-label={labels.mermaidCodeAriaLabel}
          onChange={onDraftChange}
        />
      )}

      <DiagramMermaidPreview
        code={draft}
        className="tm-diagram-editor__mermaid-preview"
        isDark={isDark}
        renderingLabel={labels.mermaidRendering}
        errorFallback={labels.mermaidRenderError}
      />
    </div>
  );
}
