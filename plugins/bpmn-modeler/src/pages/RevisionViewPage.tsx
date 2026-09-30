import { useEffect, useRef, useState } from "react";

import {
  BpmnModelerApiError,
  getRevision,
  getRevisionXml,
  type RevisionSummary,
} from "../data/api/bpmnModelerApi";
import { BpmnEditorAdapter, type ElementSummary } from "../editor/BpmnEditorAdapter";
import { ElementInspector } from "../editor/inspector/ElementInspector";
import { ReadOnlyBanner } from "../components/ReadOnlyBanner";

type Props = {
  modelId: string;
  revisionNumber: number;
  getAccessToken?: () => string | undefined;
  navigate: (path: string) => void;
};

/** Revision View (P4 §17/§24) — rota própria, read-only, deep-linkável. */
export function RevisionViewPage({ modelId, revisionNumber, getAccessToken, navigate }: Props) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const adapterRef = useRef<BpmnEditorAdapter | null>(null);
  const [revision, setRevision] = useState<RevisionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState<ElementSummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    const adapter = new BpmnEditorAdapter();
    adapterRef.current = adapter;

    const load = async () => {
      try {
        const [meta, xml] = await Promise.all([
          getRevision(modelId, revisionNumber, { getAccessToken }),
          getRevisionXml(modelId, revisionNumber, { getAccessToken }),
        ]);
        if (cancelled) return;
        setRevision(meta);
        adapter.subscribe({
          onSelectionChanged: (ids) =>
            setSelection(ids[0] ? adapter.getElementSummary(ids[0]) : null),
        });
        adapter.mount(canvasRef.current!, "viewer");
        const result = await adapter.importXml(xml);
        if (!result.ok) setError("Não foi possível renderizar a revisão.");
      } catch (err) {
        if (!cancelled)
          setError(
            err instanceof BpmnModelerApiError ? err.message : "Falha ao carregar revisão.",
          );
      }
    };
    void load();
    return () => {
      cancelled = true;
      adapter.destroy();
      adapterRef.current = null;
    };
  }, [modelId, revisionNumber, getAccessToken]);

  return (
    <div className="bpmnm-page bpmnm-editor">
      <header className="bpmnm-editor__header">
        <button
          type="button"
          className="bpmnm-btn bpmnm-btn--ghost"
          onClick={() => navigate(`/apps/bpmn-modeler/models/${modelId}`)}
        >
          ← Voltar ao modelo
        </button>
        <h1 className="bpmnm-editor__title">
          Revisão {revisionNumber}
          <span className="bpmnm-badge">Somente leitura</span>
        </h1>
        {revision ? (
          <span className="bpmnm-hint">
            {new Date(revision.created_at).toLocaleString("pt-BR")} · {revision.created_by}
            {revision.origin === "restore" ? " · criada por restauração" : ""}
          </span>
        ) : null}
      </header>

      <ReadOnlyBanner reason="REVISION_VIEW" />
      {error ? <div className="bpmnm-error" role="alert">{error}</div> : null}

      <div className="bpmnm-editor__body">
        <div ref={canvasRef} className="bpmnm-canvas" aria-label="Diagrama da revisão" />
        <aside className="bpmnm-side">
          <h3>Elemento</h3>
          <ElementInspector element={selection} />
        </aside>
      </div>
    </div>
  );
}
