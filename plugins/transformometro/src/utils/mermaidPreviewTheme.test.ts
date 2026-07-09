import { describe, expect, it } from "vitest";

import { getDiagramExportNodes, getDiagramFitNodes } from "./diagramViewFit";
import { applyMermaidPreviewTheme } from "./mermaidPreviewTheme";

describe("diagramViewFit", () => {
  it("ignora faixas no enquadramento", () => {
    const nodes = [
      { id: "lane-1", type: "lane", position: { x: 0, y: 0 }, data: {} },
      { id: "n1", type: "flowchart", position: { x: 220, y: 80 }, data: {} },
    ];

    expect(getDiagramFitNodes(nodes)).toEqual([nodes[1]]);
  });

  it("inclui faixas no enquadramento da exportação PNG", () => {
    const nodes = [
      { id: "lane-1", type: "lane", position: { x: 0, y: 0 }, data: {} },
      { id: "n1", type: "flowchart", position: { x: 220, y: 80 }, data: {} },
    ];

    expect(getDiagramExportNodes(nodes)).toEqual(nodes);
  });
});

describe("applyMermaidPreviewTheme", () => {
  it("substitui classDef claro por paleta escura", () => {
    const code = [
      "flowchart TD",
      '    n1["Tarefa"]:::bpmn_process',
      "    classDef bpmn_task fill:#ecfdf5,stroke:#059669,color:#047857",
    ].join("\n");

    const themed = applyMermaidPreviewTheme(code, true);
    expect(themed).toContain("classDef bpmn_task fill:#1e293b");
    expect(themed).not.toContain("#ecfdf5");
  });
});
