import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Download, ImagePlus } from "lucide-react";

import type { AppProps } from "../../../App";
import { TRANSFORMOMETRO_FLOWCHART_EDITOR_LABELS } from "../../../content/flowchartEditorLabels";
import { TM_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { uploadRevisaoEvidence } from "../../../data/api/transformometroEvidenceApi";
import {
  fetchRevisaoDiagramMerged,
} from "../../../data/api/transformometroDiagramApi";
import {
  FieldLabel,
  emptyFlowchart,
  flowchartToMermaid,
  DiagramMermaidPreview,
  DiagramFullscreenFrame,
  DiagramLayoutProvider,
  type FlowchartV1,
  type FlowchartEditorHandle,
} from "@delpi/plugin-ui/index";
import type { MergedRevisaoDiagram } from "../../../types/diagram";
import {
  formatDiffSummary,
  mergeRemovedNodesIntoFlowchartForDiff,
  stripFlowchartHighlights,
} from "../../../utils/diffHighlightDisplay";
import { DiagramIoMenu } from "../DiagramIoMenu";
import { FlowchartEditor } from "../editor/TransformometroFlowchartEditor";
import { DiffHighlightToggle } from "../../DiffHighlightToggle";
import { StateBox } from "../../StateBox";
import { DS_GHOST_BTN } from "../../ghostChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  embeddedInCard?: boolean;
  /** `page` = editor full-page (sem modal de tela cheia; layout fill). */
  variant?: "embedded" | "page";
  chromeLeading?: {
    onBack?: () => void;
    backLabel?: string;
    title?: string;
  };
  chromeNotices?: import("react").ReactNode;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  onReload?: () => void;
};

export function RevisaoDiagramSection({
  revisaoId,
  getAccessToken,
  embeddedInCard = false,
  variant = "embedded",
  chromeLeading,
  chromeNotices,
  resyncVersion = 0,
  onError,
  onReload,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [merged, setMerged] = useState<MergedRevisaoDiagram | null>(null);
  const [editable, setEditable] = useState<FlowchartV1>(emptyFlowchart());
  const [showDiff, setShowDiff] = useState(false);
  const [mermaidPreviewOpen, setMermaidPreviewOpen] = useState(false);
  const editorRef = useRef<FlowchartEditorHandle>(null);
  const liveMermaid = useMemo(
    () => flowchartToMermaid(stripFlowchartHighlights(editable)),
    [editable]
  );
  const diff = merged?.reference_diff ?? merged?.baseline_diff ?? null;
  const displayFlowchart = useMemo(() => {
    const stripped = stripFlowchartHighlights(editable);
    if (!showDiff || !diff?.removed?.length) return stripped;
    return mergeRemovedNodesIntoFlowchartForDiff(
      stripped,
      merged?.flowchart_reference,
      diff.removed,
    );
  }, [editable, showDiff, diff, merged?.flowchart_reference]);

  const load = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true);
    }
    onError(null);
    try {
      const mergedData = await fetchRevisaoDiagramMerged(revisaoId, getAccessToken);
      setMerged(mergedData);
      setEditable(mergedData.flowchart ?? emptyFlowchart());
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
  const hasDiff =
    Boolean(diff) &&
    (diff!.changed.length > 0 || diff!.added.length > 0 || diff!.removed.length > 0);
  const isPage = variant === "page";
  const actionBtnClass = isPage
    ? `${DS_GHOST_BTN} delpi-ui-bpmn-editor__chrome-action-btn`
    : DS_GHOST_BTN;

  const diagramActions = (
    <DiagramIoMenu
      triggerClassName={actionBtnClass}
      items={[
        {
          id: "export-png",
          label: "Exportar PNG",
          icon: Download,
          onSelect: () => void exportPng(false),
        },
        {
          id: "export-evidence",
          label: "PNG como evidência",
          icon: ImagePlus,
          onSelect: () => void exportPng(true),
        },
      ]}
    />
  );

  const editorBody = (
    <>
      <FlowchartEditor
        ref={editorRef}
        value={displayFlowchart}
        readOnly
        diffNodeIds={showDiff && hasDiff ? diff ?? undefined : undefined}
        chromeLeading={isPage ? chromeLeading : undefined}
        chromeNotices={isPage ? chromeNotices : undefined}
        chromeActions={isPage ? diagramActions : undefined}
      />

      {!isPage ? (
        <details
          className="delpi-ui-bpmn-section__preview"
          open={false}
          onToggle={(event) => {
            const el = event.currentTarget;
            if (el.open) setMermaidPreviewOpen(true);
          }}
        >
          <summary>Preview Mermaid (mesclado)</summary>
          {mermaidPreviewOpen ? (
            <DiagramMermaidPreview
              code={liveMermaid}
              viewportLabels={TRANSFORMOMETRO_FLOWCHART_EDITOR_LABELS}
            />
          ) : null}
        </details>
      ) : null}

      {!isPage ? <div className="delpi-ui-bpmn-section__actions">{diagramActions}</div> : null}
    </>
  );

  return (
    <div
      className={[
        "delpi-ui-bpmn-section",
        variant === "page" ? "delpi-ui-bpmn-section--page" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!embeddedInCard && variant !== "page" ? (
        <FieldLabel
          className="tm-field__label"
          label="Diagrama da revisão"
          hint={TM_HELP_TOOLTIPS.revisao.diagramaRevisao}
        />
      ) : null}

      <p className="ds-hint">
        {refLabel ? (
          <>
            Overlay legado somente leitura — parte do diagrama da revisão de referência{" "}
            <strong>{refLabel}</strong>.
          </>
        ) : (
          <>Overlay legado somente leitura sobre o mapa macro do processo.</>
        )}
      </p>

      {merged.seeded_from_reference ? (
        <p className="ds-hint" role="status">
          Overlay legado vazio — diagrama exibido a partir da referência.
        </p>
      ) : null}

      {merged.warnings?.length ? (
        <StateBox variant="warning" dismissible={false}>
          {merged.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </StateBox>
      ) : null}

      {hasDiff ? (
        <DiffHighlightToggle
          active={showDiff}
          onChange={setShowDiff}
          summary={formatDiffSummary(diff, refLabel)}
        />
      ) : null}

      {variant === "page" ? (
        <DiagramLayoutProvider layout="fill">
          <div className="delpi-ui-bpmn-workspace delpi-ui-bpmn-workspace--page">
            <div className="delpi-ui-bpmn-workspace__body">{editorBody}</div>
          </div>
        </DiagramLayoutProvider>
      ) : (
        <DiagramFullscreenFrame
          title="Diagrama da revisão"
          subtitle={
            refLabel
              ? `Âncora: referência ${refLabel}. Overlay as-is / to-be no escopo da melhoria.`
              : "Overlay as-is / to-be sobre o mapa macro do processo."
          }
          portalScopeClassName="dashboard-transformometro"
          labels={{ expandHint: TM_HELP_TOOLTIPS.diagramEditor.fullscreen }}
        >
          {editorBody}
        </DiagramFullscreenFrame>
      )}
    </div>
  );
}
