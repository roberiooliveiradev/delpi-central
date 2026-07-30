import { CatalogStub } from "../CatalogStub";
import type { CatalogEntryDraft } from "../types";
import { DiagramFullscreenFrame } from "../../components/bpmn/shell/DiagramFullscreenFrame";

export const bpmnCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "bpmn.FlowchartEditor",
    family: "bpmn",
    exportName: "FlowchartEditor",
    title: "FlowchartEditor",
    description: "Editor BPMN/fluxo (React Flow) — requer labels e nós iniciais.",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => (
          <CatalogStub
            name="FlowchartEditor"
            note="Fixture completa no consumidor (Transformômetro / outros MFEs)."
          />
        ),
      },
    ],
  },
  {
    id: "bpmn.DiagramMermaidPreview",
    family: "bpmn",
    exportName: "DiagramMermaidPreview",
    title: "DiagramMermaidPreview",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => <CatalogStub name="DiagramMermaidPreview" note="Requer string Mermaid." />,
      },
    ],
  },
  {
    id: "bpmn.DiagramFullscreenFrame",
    family: "bpmn",
    exportName: "DiagramFullscreenFrame",
    title: "DiagramFullscreenFrame",
    description: "Botão Tela cheia → ModalShell contido no host MFE (mesmo padrão do FilePreview).",
    demos: [
      {
        id: "basic",
        label: "Com botão",
        render: () => (
          <div className="dashboard-plugin-ui-catalog" style={{ minHeight: 160 }}>
            <DiagramFullscreenFrame title="Diagrama demo" subtitle="Abre no ModalShell">
              <p className="ds-hint">Conteúdo do editor (paleta / canvas) entra no modal.</p>
            </DiagramFullscreenFrame>
          </div>
        ),
      },
    ],
  },
  {
    id: "bpmn.TabPanelTransition",
    family: "bpmn",
    exportName: "TabPanelTransition",
    title: "TabPanelTransition",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => <CatalogStub name="TabPanelTransition" />,
      },
    ],
  },
];
