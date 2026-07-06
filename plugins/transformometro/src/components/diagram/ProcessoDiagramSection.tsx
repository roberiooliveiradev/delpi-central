import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Download, FileCode2, ShieldCheck, Upload } from "lucide-react";

import type { AppProps } from "../../App";
import { FieldLabel } from "../HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchProcessoDiagramBpmnXml,
  fetchProcessoDiagrama,
  importProcessoDiagramBpmnXml,
  saveProcessoDiagrama,
  validateProcessoDiagrama,
  type DiagramValidationReport,
} from "../../data/api/transformometroDiagramApi";
import { emptyFlowchart, type FlowchartV1 } from "../../types/diagram";
import { flowchartToMermaid } from "../../utils/flowchartMermaid";
import { DiagramMermaidPreview } from "./DiagramMermaidPreview";
import { DiagramValidationPanel } from "./DiagramValidationPanel";
import { DiagramFullscreenFrame } from "./DiagramFullscreenFrame";

const FlowchartEditor = lazy(() =>
  import("./FlowchartEditor").then((module) => ({ default: module.FlowchartEditor }))
);

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  onEntityChanged?: () => void;
};

export function ProcessoDiagramSection({
  processoId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
  onEntityChanged,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [flowchart, setFlowchart] = useState<FlowchartV1>(emptyFlowchart());
  const liveMermaid = useMemo(() => flowchartToMermaid(flowchart), [flowchart]);
  const [validation, setValidation] = useState<DiagramValidationReport | null>(null);
  const exportRef = useRef<HTMLDivElement>(null);
  const importInputRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
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
    void load();
  }, [resyncVersion, load]);

  async function runValidation(nextChart: FlowchartV1 = flowchart) {
    setValidating(true);
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

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const report = await validateProcessoDiagrama(processoId, flowchart, getAccessToken);
      setValidation(report);
      if (!report.valid) {
        onError("Corrija os erros de validação antes de salvar.");
        return;
      }
      const data = await saveProcessoDiagrama(processoId, flowchart, getAccessToken);
      setFlowchart(data.conteudo);
      onEntityChanged?.();
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

  async function importBpmnXml(file: File) {
    try {
      const xml = await file.text();
      const data = await importProcessoDiagramBpmnXml(processoId, xml, getAccessToken);
      setFlowchart(data.conteudo);
      setValidation(null);
      onEntityChanged?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao importar BPMN XML.");
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando diagrama macro…</p>;
  }

  return (
    <div className="tm-diagram-section">
      {!embeddedInCard ? (
        <FieldLabel label="Diagrama macro" hint={TM_HELP_TOOLTIPS.processos.diagramaMacro} />
      ) : null}

      <DiagramFullscreenFrame
        title="Diagrama macro"
        subtitle="Mapa canônico do fluxo end-to-end deste processo-mestre."
      >
        <Suspense fallback={<p className="ds-hint">Carregando editor…</p>}>
          <FlowchartEditor
            value={flowchart}
            onChange={readOnly ? undefined : setFlowchart}
            readOnly={readOnly}
            exportRef={exportRef}
          />
        </Suspense>

        <DiagramValidationPanel report={validation} loading={validating} />

        <details className="tm-diagram-section__preview" open={false}>
          <summary>Preview Mermaid</summary>
          <DiagramMermaidPreview code={liveMermaid} />
        </details>

        {!readOnly ? (
          <div className="tm-diagram-section__actions">
            <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
              {saving ? "Salvando…" : "Salvar diagrama"}
            </button>
            <button type="button" className="ds-ghost-btn" disabled={validating} onClick={() => void runValidation()}>
              <ShieldCheck size={16} />
              Validar / simular
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => void exportPng()}>
              <Download size={16} />
              Exportar PNG
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => void exportBpmnXml()}>
              <FileCode2 size={16} />
              Exportar BPMN XML
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => importInputRef.current?.click()}>
              <Upload size={16} />
              Importar BPMN XML
            </button>
            <input
              ref={importInputRef}
              type="file"
              accept=".bpmn,.xml,text/xml,application/xml"
              hidden
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (file) void importBpmnXml(file);
              }}
            />
          </div>
        ) : (
          <div className="tm-diagram-section__actions">
            <button type="button" className="ds-ghost-btn" onClick={() => void exportPng()}>
              <Download size={16} />
              Exportar PNG
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => void exportBpmnXml()}>
              <FileCode2 size={16} />
              Exportar BPMN XML
            </button>
          </div>
        )}
      </DiagramFullscreenFrame>
    </div>
  );
}
