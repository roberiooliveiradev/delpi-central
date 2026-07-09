import { RefreshCw, Wand2 } from "lucide-react";

import { NativeTextAreaControl } from "@delpi/plugin-ui";

import { DiagramMermaidPreview } from "./DiagramMermaidPreview";
import type { DiagramEditorLayout } from "./DiagramLayoutContext";

type Props = {
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
};

export function FlowchartMermaidPanel({
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
            Atualizar do canvas
          </button>
          {isEmpty ? (
            <button type="button" className="ds-ghost-btn" onClick={onUseTemplate}>
              <Wand2 size={16} aria-hidden />
              Modelo inicial
            </button>
          ) : null}
          <button
            type="button"
            className="ds-primary-btn"
            disabled={applying || !draft.trim()}
            onClick={onApply}
          >
            {applying ? "Aplicando…" : "Aplicar ao canvas"}
          </button>
        </div>
      ) : null}

      {applyError ? (
        <div className="ds-state ds-state--warn" role="alert">
          {applyError}
        </div>
      ) : null}

      {readOnly ? (
        <pre className="tm-diagram-editor__mermaid-code">{draft || "Sem preview."}</pre>
      ) : (
        <NativeTextAreaControl
          className="tm-diagram-editor__mermaid-input"
          value={draft}
          spellCheck={false}
          aria-label="Código Mermaid"
          onChange={onDraftChange}
        />
      )}

      <DiagramMermaidPreview code={draft} className="tm-diagram-editor__mermaid-preview" />
    </div>
  );
}
