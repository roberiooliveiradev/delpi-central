import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Download, ImagePlus } from "lucide-react";

import type { AppProps } from "../../App";
import { FieldLabel } from "../HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { uploadRevisaoEvidence } from "../../data/api/transformometroEvidenceApi";
import {
  fetchRevisaoDiagramMerged,
  fetchRevisaoDiagramOverlay,
  saveRevisaoDiagramOverlay,
} from "../../data/api/transformometroDiagramApi";
import {
  emptyFlowchart,
  emptyOverlay,
  flowToOverlayDraft,
  type FlowchartOverlayV1,
  type FlowchartV1,
  type MergedRevisaoDiagram,
} from "../../types/diagram";
import { DiagramMermaidPreview } from "./DiagramMermaidPreview";
import { DiagramFullscreenFrame } from "./DiagramFullscreenFrame";

const FlowchartEditor = lazy(() =>
  import("./FlowchartEditor").then((module) => ({ default: module.FlowchartEditor }))
);

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  cenarioTipo?: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
  onReload?: () => void;
};

export function RevisaoDiagramSection({
  revisaoId,
  cenarioTipo,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  onError,
  onReload,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [merged, setMerged] = useState<MergedRevisaoDiagram | null>(null);
  const [editable, setEditable] = useState<FlowchartV1>(emptyFlowchart());
  const [overlayDraft, setOverlayDraft] = useState<FlowchartOverlayV1>(emptyOverlay());
  const [baseMerged, setBaseMerged] = useState<FlowchartV1>(emptyFlowchart());
  const exportRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const [mergedData, overlayData] = await Promise.all([
        fetchRevisaoDiagramMerged(revisaoId, getAccessToken),
        fetchRevisaoDiagramOverlay(revisaoId, getAccessToken),
      ]);
      setMerged(mergedData);
      setEditable(mergedData.flowchart ?? emptyFlowchart());
      setBaseMerged(mergedData.flowchart ?? emptyFlowchart());
      setOverlayDraft(overlayData.conteudo ?? emptyOverlay());
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar diagrama da revisão.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisaoId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const overlay = flowToOverlayDraft(baseMerged, editable, overlayDraft);
      overlay.modo = "partial";
      if (cenarioTipo?.toLowerCase() === "baseline") {
        for (const node of editable.nodes) {
          overlay.node_overrides = {
            ...(overlay.node_overrides ?? {}),
            [node.id]: {
              ...(overlay.node_overrides?.[node.id] ?? {}),
              highlight: overlay.node_overrides?.[node.id]?.highlight ?? "asis",
            },
          };
        }
      } else {
        for (const node of editable.nodes) {
          overlay.node_overrides = {
            ...(overlay.node_overrides ?? {}),
            [node.id]: {
              ...(overlay.node_overrides?.[node.id] ?? {}),
              highlight: overlay.node_overrides?.[node.id]?.highlight ?? "tobe",
            },
          };
        }
      }
      await saveRevisaoDiagramOverlay(revisaoId, overlay, getAccessToken);
      await load();
      onReload?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar overlay do diagrama.");
    } finally {
      setSaving(false);
    }
  }

  async function exportPng(asEvidence = false) {
    const target = exportRef.current;
    if (!target) return;
    const { toPng } = await import("html-to-image");
    const dataUrl = await toPng(target, { cacheBust: true, pixelRatio: 2 });
    if (!asEvidence) {
      const link = document.createElement("a");
      link.download = `diagrama-revisao-${revisaoId}.png`;
      link.href = dataUrl;
      link.click();
      return;
    }
    const blob = await (await fetch(dataUrl)).blob();
    const file = new File([blob], `diagrama-revisao-${revisaoId}.png`, { type: "image/png" });
    await uploadRevisaoEvidence(
      revisaoId,
      { tipo: "foto", file, descricao: "Diagrama exportado (PNG)" },
      getAccessToken
    );
    onReload?.();
  }

  if (loading) {
    return <p className="ds-hint">Carregando diagrama da revisão…</p>;
  }

  if (!merged) {
    return <p className="ds-hint">Diagrama indisponível.</p>;
  }

  return (
    <div className="tm-diagram-section">
      {!embeddedInCard ? (
        <FieldLabel label="Diagrama da revisão" hint={TM_HELP_TOOLTIPS.revisao.diagramaRevisao} />
      ) : null}

      {merged.warnings?.length ? (
        <div className="ds-state ds-state--warn" role="status">
          {merged.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {merged.baseline_diff ? (
        <div className="tm-diagram-diff" role="status">
          <p className="ds-hint">
            Diff vs baseline: {merged.baseline_diff.changed.length} alterados,{" "}
            {merged.baseline_diff.added.length} novos, {merged.baseline_diff.removed.length} removidos.
          </p>
        </div>
      ) : null}

      <DiagramFullscreenFrame
        title="Diagrama da revisão"
        subtitle="Overlay as-is / to-be sobre o mapa macro do processo."
      >
        <Suspense fallback={<p className="ds-hint">Carregando editor…</p>}>
          <FlowchartEditor
            value={editable}
            onChange={readOnly ? undefined : setEditable}
            readOnly={readOnly}
            diffNodeIds={merged.baseline_diff ?? undefined}
            mermaidPreview={merged.mermaid}
            exportRef={exportRef}
            showTemplates={false}
          />
        </Suspense>

        {merged.mermaid ? (
          <details className="tm-diagram-section__preview">
            <summary>Preview Mermaid (mesclado)</summary>
            <DiagramMermaidPreview code={merged.mermaid} />
          </details>
        ) : null}

        <div className="tm-diagram-section__actions">
          {!readOnly ? (
            <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
              {saving ? "Salvando…" : "Salvar diagrama da revisão"}
            </button>
          ) : null}
          <button type="button" className="ds-ghost-btn" onClick={() => void exportPng(false)}>
            <Download size={16} />
            Exportar PNG
          </button>
          {!readOnly ? (
            <button type="button" className="ds-ghost-btn" onClick={() => void exportPng(true)}>
              <ImagePlus size={16} />
              PNG como evidência
            </button>
          ) : null}
        </div>
      </DiagramFullscreenFrame>
    </div>
  );
}
