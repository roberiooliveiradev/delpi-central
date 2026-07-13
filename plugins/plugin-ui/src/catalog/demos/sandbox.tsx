import { ConfigurableSeriesChart, ImpactEffortMatrix } from "../../components/charts";
import type { CatalogEntry } from "../types";

function SandboxNotice({ children }: { children: string }) {
  return <p className="puc-sandbox-notice">{children}</p>;
}

export const sandboxCatalogEntries: CatalogEntry[] = [
  {
    id: "sandbox.ConfigurableSeriesChart",
    family: "sandbox",
    exportName: "ConfigurableSeriesChart",
    title: "ConfigurableSeriesChart",
    description: "Gráfico de série SVG nativo — demo mínima.",
    docAnchor: "configurableserieschart",
    propsSummary: ["chartType", "points", "options"],
    demos: [
      {
        id: "line",
        label: "Linha",
        render: () => (
          <div className="puc-sandbox-chart">
            <ConfigurableSeriesChart
              chartType="line"
              points={[
                { label: "Jan", value: 12 },
                { label: "Fev", value: 18 },
                { label: "Mar", value: 15 },
                { label: "Abr", value: 22 },
              ]}
              options={{ title: "Série demo", showLegend: false }}
            />
          </div>
        ),
      },
    ],
  },
  {
    id: "sandbox.ImpactEffortMatrix",
    family: "sandbox",
    exportName: "ImpactEffortMatrix",
    title: "ImpactEffortMatrix",
    description: "Matriz impacto × esforço — pontos mock.",
    docAnchor: "impacteffortmatrix",
    propsSummary: ["points", "activePointId"],
    demos: [
      {
        id: "default",
        label: "Scatter",
        render: () => (
          <div className="puc-sandbox-chart">
            <ImpactEffortMatrix
              points={[
                { id: "1", label: "Rápido", impacto: 80, esforco: 20, quadrante: "quick_win" },
                { id: "2", label: "Estratégico", impacto: 85, esforco: 75, quadrante: "strategic" },
                { id: "3", label: "Complementar", impacto: 30, esforco: 25, quadrante: "fill_in" },
                { id: "4", label: "Reavaliar", impacto: 25, esforco: 80, quadrante: "rethink" },
              ]}
            />
          </div>
        ),
      },
    ],
  },
  {
    id: "sandbox.FlowchartEditor",
    family: "sandbox",
    exportName: "FlowchartEditor",
    title: "FlowchartEditor",
    description: "Editor BPMN/fluxo — requer fixtures e labels completos.",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => (
          <SandboxNotice>
            Sandbox: FlowchartEditor exige labels, nós iniciais e integração com React Flow. Use o
            consumidor (ex.: TV dashboard) ou estenda esta entrada com fixtures dedicadas.
          </SandboxNotice>
        ),
      },
    ],
  },
  {
    id: "sandbox.FilePreviewModal",
    family: "sandbox",
    exportName: "FilePreviewModal",
    title: "FilePreviewModal",
    description: "Prévia de arquivo — requer blob/File ou URL.",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => (
          <SandboxNotice>
            Sandbox: FilePreviewModal precisa de um arquivo real (PDF/imagem) ou estado
            previewState. Monte a demo com fixture local quando necessário.
          </SandboxNotice>
        ),
      },
    ],
  },
];
