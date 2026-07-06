import { describe, expect, it } from "vitest";

import { emptyFlowchart } from "../types/diagram";
import {
  flowchartToMermaid,
  mermaidToFlowchart,
  MermaidImportError,
} from "./flowchartMermaid";

describe("flowchartToMermaid", () => {
  it("gera placeholder para diagrama vazio", () => {
    const text = flowchartToMermaid(emptyFlowchart());
    expect(text).toContain("flowchart TD");
    expect(text.toLowerCase()).toContain("vazio");
  });

  it("renderiza nó de decisão com chaves", () => {
    const text = flowchartToMermaid({
      format: "flowchart_v1",
      format_version: 1,
      nodes: [
        {
          id: "n_dec",
          type: "decision",
          label: "Aprovado?",
          position: { x: 0, y: 0 },
        },
      ],
      edges: [],
    });
    expect(text).toContain('n_dec{"Aprovado?"}');
  });
});

describe("mermaidToFlowchart", () => {
  it("importa fluxo linear simples", () => {
    const code = [
      "flowchart TD",
      '    start(("Início"))',
      '    proc["Atividade"]',
      '    end(("Fim"))',
      "    start --> proc",
      "    proc --> end",
    ].join("\n");

    const chart = mermaidToFlowchart(code);
    expect(chart.nodes).toHaveLength(3);
    expect(chart.nodes[0]?.type).toBe("start");
    expect(chart.nodes[2]?.type).toBe("end");
    expect(chart.edges).toHaveLength(2);
  });

  it("rejeita cabeçalho inválido", () => {
    expect(() => mermaidToFlowchart("graph LR\n    a --> b")).toThrow(MermaidImportError);
  });

  it("round-trip preserva rótulos principais", () => {
    const original = {
      format: "flowchart_v1" as const,
      format_version: 1 as const,
      nodes: [
        { id: "n1", type: "start" as const, label: "Início", position: { x: 0, y: 0 } },
        { id: "n2", type: "process" as const, label: "Passo", position: { x: 0, y: 0 } },
        { id: "n3", type: "end" as const, label: "Fim", position: { x: 0, y: 0 } },
      ],
      edges: [
        { id: "e1", from: "n1", to: "n2", label: null },
        { id: "e2", from: "n2", to: "n3", label: null },
      ],
    };

    const code = flowchartToMermaid(original);
    const imported = mermaidToFlowchart(code);
    expect(imported.nodes.map((node) => node.label)).toEqual(["Início", "Passo", "Fim"]);
    expect(imported.edges).toHaveLength(2);
  });
});
