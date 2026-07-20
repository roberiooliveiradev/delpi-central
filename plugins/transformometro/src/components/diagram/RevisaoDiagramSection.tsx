import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Download, ImagePlus } from "lucide-react";

import type { AppProps } from "../../App";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { uploadRevisaoEvidence } from "../../data/api/transformometroEvidenceApi";
import {
  fetchRevisaoDiagramMerged,
  fetchRevisaoDiagramOverlay,
  saveRevisaoDiagramOverlay,
} from "../../data/api/transformometroDiagramApi";
import {
  FieldLabel,
  emptyFlowchart,
  emptyOverlay,
  flowToOverlayDraft,
  flowchartToMermaid,
  DiagramMermaidPreview,
  DiagramFullscreenFrame,
  type FlowchartOverlayV1,
  type FlowchartV1,
  type FlowchartEditorHandle,
} from "@delpi/plugin-ui/index";
import type { MergedRevisaoDiagram } from "../../types/diagram";
import { FlowchartEditor } from "./TransformometroFlowchartEditor";
import { DS_GHOST_BTN } from "../ghostChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  cenarioTipo?: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  onReload?: () => void;
};

export function RevisaoDiagramSection({
  revisaoId,
  cenarioTipo,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
  onReload,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [merged, setMerged] = useState<MergedRevisaoDiagram | null>(null);
  const [editable, setEditable] = useState<FlowchartV1>(emptyFlowchart());
  const [overlayDraft, setOverlayDraft] = useState<FlowchartOverlayV1>(emptyOverlay());
  const liveMermaid = useMemo(() => flowchartToMermaid(editable), [editable]);
  /** Macro ∩ escopo — base absoluta do overlay (PB19 S7). */
  const [flowchartBase, setFlowchartBase] = useState<FlowchartV1>(emptyFlowchart());
  const editorRef = useRef<FlowchartEditorHandle>(null);

  const load = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true);
    }
    onError(null);
    try {
      const [mergedData, overlayData] = await Promise.all([
        fetchRevisaoDiagramMerged(revisaoId, getAccessToken),
        fetchRevisaoDiagramOverlay(revisaoId, getAccessToken),
      ]);
      setMerged(mergedData);
      setEditable(mergedData.flowchart ?? emptyFlowchart());
      setFlowchartBase(mergedData.flowchart_base ?? mergedData.flowchart ?? emptyFlowchart());
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

  useEffect(() => {
    if (!resyncVersion) return;
    void load({ silent: true });
  }, [resyncVersion, load]);

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const overlay = flowToOverlayDraft(flowchartBase, editable, overlayDraft);
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
    if (!editorRef.current) {
      onError("Editor do diagrama indisponível.");
      return;
    }
    try {
      const dataUrl = await editorRef.current.exportPng(`diagrama-revisao-${revisaoId}.png`);
      if (!asEvidence) return;
      const blob = await (await fetch(dataUrl)).blob();
      const file = new File([blob], `diagrama-revisao-${revisaoId}.png`, { type: "image/png" });
      await uploadRevisaoEvidence(
        revisaoId,
        { tipo: "foto", file, descricao: "Diagrama exportado (PNG)" },
        getAccessToken
      );
      onReload?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao exportar PNG.");
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando diagrama da revisão…</p>;
  }

  if (!merged) {
    return <p className="ds-hint">Diagrama indisponível.</p>;
  }

  const refLabel =
    merged.referencia?.versao_revisao ||
    (merged.referencia?.revisao_id ? merged.referencia.revisao_id.slice(0, 8) : null);
  const diff = merged.reference_diff ?? merged.baseline_diff;

  return (
    <div className="tm-diagram-section">
      {!embeddedInCard ? (
        <FieldLabel className="tm-field__label" label="Diagrama da revisão" hint={TM_HELP_TOOLTIPS.revisao.diagramaRevisao} />
      ) : null}

      {!readOnly ? (
        <p className="ds-hint tm-decomposition-revisao__edit-hint">
          {refLabel ? (
            <>
              Parte do diagrama da revisão de referência <strong>{refLabel}</strong>. O{" "}
              <strong>diagrama composto</strong> («agora») no processo reflete as revisões vigentes.
            </>
          ) : (
            <>
              Edite o fluxo no escopo desta melhoria. Sem referência, a âncora é o diagrama macro.
            </>
          )}
        </p>
      ) : null}

      {merged.seeded_from_reference ? (
        <p className="ds-hint" role="status">
          Overlay ainda vazio — diagrama iniciado a partir da referência. Ao salvar, o delta fica
          absoluto em relação ao macro.
        </p>
      ) : null}

      {merged.warnings?.length ? (
        <div className="ds-state ds-state--warn" role="status">
          {merged.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {diff ? (
        <div className="tm-diagram-diff" role="status">
          <p className="ds-hint">
            Diff vs {refLabel ? `referência (${refLabel})` : "referência"}: {diff.changed.length}{" "}
            alterados, {diff.added.length} novos, {diff.removed.length} removidos.
          </p>
        </div>
      ) : null}

      <DiagramFullscreenFrame
        title="Diagrama da revisão"
        subtitle={
          refLabel
            ? `Âncora: referência ${refLabel}. Overlay as-is / to-be no escopo da melhoria.`
            : "Overlay as-is / to-be sobre o mapa macro do processo."
        }
      >
        <FlowchartEditor
          ref={editorRef}
          value={editable}
          onChange={readOnly ? undefined : setEditable}
          readOnly={readOnly}
          diffNodeIds={diff ?? undefined}
        />

        <details className="tm-diagram-section__preview" open={false}>
          <summary>Preview Mermaid (mesclado)</summary>
          <DiagramMermaidPreview code={liveMermaid} />
        </details>

        <div className="tm-diagram-section__actions">
          {!readOnly ? (
            <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
              {saving ? "Salvando…" : "Salvar diagrama da revisão"}
            </button>
          ) : null}
          <button type="button" className={DS_GHOST_BTN} onClick={() => void exportPng(false)}>
            <Download size={16} />
            Exportar PNG
          </button>
          {!readOnly ? (
            <button type="button" className={DS_GHOST_BTN} onClick={() => void exportPng(true)}>
              <ImagePlus size={16} />
              PNG como evidência
            </button>
          ) : null}
        </div>
      </DiagramFullscreenFrame>
    </div>
  );
}
