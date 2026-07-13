import { CatalogStub } from "../CatalogStub";
import type { CatalogEntryDraft } from "../types";

export const diagramCatalogEntries: CatalogEntryDraft[] = [
  {
    id: "diagram.FlowchartEditor",
    family: "diagram",
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
            note="Fixture completa no consumidor (TV dashboard / diagramas)."
          />
        ),
      },
    ],
  },
  {
    id: "diagram.DiagramMermaidPreview",
    family: "diagram",
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
    id: "diagram.DiagramFullscreenFrame",
    family: "diagram",
    exportName: "DiagramFullscreenFrame",
    title: "DiagramFullscreenFrame",
    demos: [
      {
        id: "stub",
        label: "Stub",
        render: () => <CatalogStub name="DiagramFullscreenFrame" />,
      },
    ],
  },
  {
    id: "diagram.TabPanelTransition",
    family: "diagram",
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
