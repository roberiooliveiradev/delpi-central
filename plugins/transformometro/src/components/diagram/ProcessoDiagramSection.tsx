import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Download, ImagePlus } from "lucide-react";

import type { AppProps } from "../../App";
import { FieldLabel } from "../HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchProcessoDiagrama,
  saveProcessoDiagrama,
} from "../../data/api/transformometroDiagramApi";
import { emptyFlowchart, type FlowchartV1 } from "../../types/diagram";
import { DiagramMermaidPreview } from "./DiagramMermaidPreview";

const FlowchartEditor = lazy(() =>
  import("./FlowchartEditor").then((module) => ({ default: module.FlowchartEditor }))
);

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
};

export function ProcessoDiagramSection({
  processoId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [flowchart, setFlowchart] = useState<FlowchartV1>(emptyFlowchart());
  const [mermaid, setMermaid] = useState("");
  const exportRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const data = await fetchProcessoDiagrama(processoId, getAccessToken);
      setFlowchart(data.conteudo ?? emptyFlowchart());
      setMermaid(data.mermaid ?? "");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar diagrama macro.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const data = await saveProcessoDiagrama(processoId, flowchart, getAccessToken);
      setFlowchart(data.conteudo);
      setMermaid(data.mermaid);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar diagrama macro.");
    } finally {
      setSaving(false);
    }
  }

  async function exportPng() {
    const target = exportRef.current;
    if (!target) return;
    const { toPng } = await import("html-to-image");
    const dataUrl = await toPng(target, { cacheBust: true, pixelRatio: 2 });
    const link = document.createElement("a");
    link.download = `diagrama-processo-${processoId}.png`;
    link.href = dataUrl;
    link.click();
  }

  if (loading) {
    return <p className="ds-hint">Carregando diagrama macro…</p>;
  }

  return (
    <div className="tm-diagram-section">
      {!embeddedInCard ? (
        <FieldLabel label="Diagrama macro" hint={TM_HELP_TOOLTIPS.processos.diagramaMacro} />
      ) : null}

      <Suspense fallback={<p className="ds-hint">Carregando editor…</p>}>
        <FlowchartEditor
          value={flowchart}
          onChange={readOnly ? undefined : setFlowchart}
          readOnly={readOnly}
          mermaidPreview={mermaid}
          exportRef={exportRef}
        />
      </Suspense>

      {mermaid ? (
        <details className="tm-diagram-section__preview">
          <summary>Preview Mermaid</summary>
          <DiagramMermaidPreview code={mermaid} />
        </details>
      ) : null}

      {!readOnly ? (
        <div className="tm-diagram-section__actions">
          <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
            {saving ? "Salvando…" : "Salvar diagrama"}
          </button>
          <button type="button" className="ds-ghost-btn" onClick={() => void exportPng()}>
            <Download size={16} />
            Exportar PNG
          </button>
        </div>
      ) : (
        <button type="button" className="ds-ghost-btn" onClick={() => void exportPng()}>
          <ImagePlus size={16} />
          Exportar PNG
        </button>
      )}
    </div>
  );
}
