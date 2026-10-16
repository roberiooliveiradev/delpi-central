import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Download, FileCode2, ShieldCheck } from "lucide-react";

import type { AppProps } from "../../../App";
import { TRANSFORMOMETRO_FLOWCHART_EDITOR_LABELS } from "../../../content/flowchartEditorLabels";
import { TM_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import {
  fetchProcessoDiagramBpmnXml,
  fetchProcessoDiagrama,
  validateProcessoDiagrama,
  type DiagramValidationReport,
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
import { DiagramIoMenu } from "../DiagramIoMenu";
import { DiagramValidationPanel } from "../validation/DiagramValidationPanel";
import { FlowchartEditor } from "../editor/TransformometroFlowchartEditor";
import { DS_GHOST_BTN } from "../../ghostChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
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
};

export function ProcessoDiagramSection({
  processoId,
  getAccessToken,
  embeddedInCard = false,
  variant = "embedded",
  chromeLeading,
  chromeNotices,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [validationPanelOpen, setValidationPanelOpen] = useState(false);
  const [validationPanelCollapsed, setValidationPanelCollapsed] = useState(false);
  const [flowchart, setFlowchart] = useState<FlowchartV1>(emptyFlowchart());
  const liveMermaid = useMemo(() => flowchartToMermaid(flowchart), [flowchart]);
  const [validation, setValidation] = useState<DiagramValidationReport | null>(null);
  const [mermaidPreviewOpen, setMermaidPreviewOpen] = useState(false);
  const editorRef = useRef<FlowchartEditorHandle>(null);
  const isPage = variant === "page";

  const load = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true);
    }
    onError(null);
    try {
      const data = await fetchProcessoDiagrama(processoId, getAccessToken);
      setFlowchart(data.conteudo ?? emptyFlowchart());
      setValidation(null);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar diagrama macro.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load({ silent: true });
  }, [resyncVersion, load]);

  async function runValidation(nextChart: FlowchartV1 = flowchart) {
    setValidating(true);
    setValidationPanelOpen(true);
    setValidationPanelCollapsed(false);
    onError(null);
    try {
      const report = await validateProcessoDiagrama(processoId, nextChart, getAccessToken);
      setValidation(report);
      return report;
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao validar diagrama.");
      return null;
    } finally {
      setValidating(false);
    }
  }

  async function exportPng() {
    if (!editorRef.current) {
      onError("Editor do diagrama indisponível.");
      return;
    }
    try {
      await editorRef.current.exportPng(`diagrama-processo-${processoId}.png`);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao exportar PNG.");
    }
  }

  async function exportBpmnXml() {
    try {
      const xml = await fetchProcessoDiagramBpmnXml(processoId, getAccessToken);
      const blob = new Blob([xml], { type: "application/xml" });
      const link = document.createElement("a");
      link.download = `diagrama-processo-${processoId}.bpmn`;
      link.href = URL.createObjectURL(blob);
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao exportar BPMN XML.");
    }
  }

  const actionBtnClass = isPage
    ? `${DS_GHOST_BTN} delpi-ui-bpmn-editor__chrome-action-btn`
    : DS_GHOST_BTN;

  const ioItems = [
    {
      id: "export-png",
      label: "Exportar PNG",
      icon: Download,
      onSelect: () => void exportPng(),
    },
    {
      id: "export-bpmn",
      label: "Exportar BPMN XML",
      icon: FileCode2,
      onSelect: () => void exportBpmnXml(),
    },
  ];

  const diagramActions: ReactNode = (
    <>
      <button
        type="button"
        className={[
          actionBtnClass,
          validationPanelOpen ? "delpi-ui-bpmn-editor__chrome-action-btn--active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        disabled={validating}
        aria-pressed={validationPanelOpen}
        onClick={() => {
          if (validationPanelOpen && validation && !validating) {
            setValidationPanelOpen(false);
            setValidationPanelCollapsed(false);
            return;
          }
          void runValidation();
        }}
      >
        <ShieldCheck size={14} />
        Validar / simular
      </button>
      <DiagramIoMenu items={ioItems} triggerClassName={actionBtnClass} />
    </>
  );

  if (loading) {
    return <p className="ds-hint">Carregando diagrama macro…</p>;
  }

  const showValidationPanel =
    validationPanelOpen && (validating || validation != null);
  const validationLayout = isPage ? "aside" : "stack";

  const editorCore = (
    <FlowchartEditor
      ref={editorRef}
      value={flowchart}
      readOnly
      chromeLeading={isPage ? chromeLeading : undefined}
      chromeNotices={isPage ? chromeNotices : undefined}
      chromeActions={isPage ? diagramActions : undefined}
    />
  );

  const closeValidationPanel = () => {
    setValidationPanelOpen(false);
    setValidationPanelCollapsed(false);
  };

  const validationPanel = showValidationPanel ? (
    <DiagramValidationPanel
      report={validation}
      loading={validating}
      layout={validationLayout}
      collapsed={isPage ? validationPanelCollapsed : false}
      onCollapse={isPage ? () => setValidationPanelCollapsed(true) : undefined}
      onExpand={isPage ? () => setValidationPanelCollapsed(false) : undefined}
      onClose={closeValidationPanel}
    />
  ) : null;

  const editorBody = (
    <>
      {isPage ? (
        <div
          className={[
            "delpi-ui-bpmn-workspace__split",
            showValidationPanel ? "delpi-ui-bpmn-workspace__split--with-panel" : "",
            showValidationPanel && validationPanelCollapsed
              ? "delpi-ui-bpmn-workspace__split--rail"
              : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <div className="delpi-ui-bpmn-workspace__main">{editorCore}</div>
          {showValidationPanel ? (
            <div
              className={[
                "delpi-ui-bpmn-workspace__aside",
                validationPanelCollapsed ? "delpi-ui-bpmn-workspace__aside--rail" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {validationPanel}
            </div>
          ) : null}
        </div>
      ) : (
        <>
          {editorCore}
          {validationPanel}
        </>
      )}

      {!isPage ? (
        <details
          className="delpi-ui-bpmn-section__preview"
          open={false}
          onToggle={(event) => {
            const el = event.currentTarget;
            if (el.open) setMermaidPreviewOpen(true);
          }}
        >
          <summary>Preview Mermaid</summary>
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
    <div className={["delpi-ui-bpmn-section", isPage ? "delpi-ui-bpmn-section--page" : ""].filter(Boolean).join(" ")}>
      {!embeddedInCard && !isPage ? (
        <FieldLabel className="tm-field__label" label="Diagrama macro" hint={TM_HELP_TOOLTIPS.processos.diagramaMacro} />
      ) : null}

      {isPage ? (
        <DiagramLayoutProvider layout="fill">
          <div className="delpi-ui-bpmn-workspace delpi-ui-bpmn-workspace--page">
            <div className="delpi-ui-bpmn-workspace__body">{editorBody}</div>
          </div>
        </DiagramLayoutProvider>
      ) : (
        <DiagramFullscreenFrame
          title="Diagrama macro"
          subtitle="Mapa canônico do fluxo end-to-end deste processo-mestre."
          portalScopeClassName="dashboard-transformometro"
          labels={{ expandHint: TM_HELP_TOOLTIPS.diagramEditor.fullscreen }}
        >
          {editorBody}
        </DiagramFullscreenFrame>
      )}
    </div>
  );
}
