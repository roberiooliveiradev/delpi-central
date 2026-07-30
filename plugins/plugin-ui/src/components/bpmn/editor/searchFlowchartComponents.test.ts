import { describe, expect, it } from "vitest";

import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import { searchFlowchartComponents } from "./searchFlowchartComponents";

const labels = {
  addLane: "Adiciona uma faixa (swimlane).",
  autoLayout: "Reorganiza o layout.",
  templateLinear: "Modelo linear.",
  templateDecision: "Modelo com decisão.",
  templateSwimlanes: "Modelo com faixas.",
  toolbarModelsTab: "Modelos",
  toolbarElementsTab: "Elementos",
  toolbarElementsTabHint: "",
  toolbarModelsTabHint: "",
  elementGroupTabs: [
    { id: "events", label: "Eventos" },
    { id: "gateways", label: "Desvios" },
    { id: "tasks", label: "Tarefas" },
    { id: "activities", label: "Atividades" },
    { id: "artifacts", label: "Artefatos" },
    { id: "boundary", label: "Borda" },
    { id: "lanes", label: "Faixas" },
  ],
  elementGroupTabHints: {},
  eventSubTabs: [],
  eventSubTabHints: {},
  editorActions: [
    { id: "addLane", label: "Faixa", hint: "Adiciona uma faixa (swimlane)." },
    { id: "autoLayout", label: "Layout automático", hint: "Reorganiza o layout." },
    { id: "templateLinear", label: "Modelo linear", hint: "Modelo linear." },
    { id: "templateDecision", label: "Modelo decisão", hint: "Modelo com decisão." },
    { id: "templateSwimlanes", label: "Modelo BPMN com faixas", hint: "Modelo com faixas." },
  ],
  nodeHints: {},
} as FlowchartEditorLabels;

describe("searchFlowchartComponents", () => {
  it("inclui Faixa ao buscar 'faixa'", () => {
    const hits = searchFlowchartComponents("faixa", labels);
    expect(hits.some((hit) => hit.kind === "action" && hit.actionId === "addLane")).toBe(
      true,
    );
  });

  it("inclui Faixa ao buscar 'faixas'", () => {
    const hits = searchFlowchartComponents("faixas", labels);
    expect(hits.some((hit) => hit.kind === "action" && hit.actionId === "addLane")).toBe(
      true,
    );
  });

  it("continua encontrando nós da paleta", () => {
    const hits = searchFlowchartComponents("xor", labels);
    expect(hits.some((hit) => hit.kind === "node" && hit.type === "decision")).toBe(true);
  });

  it("inclui modelos na busca", () => {
    const hits = searchFlowchartComponents("modelo", labels);
    expect(hits.some((hit) => hit.kind === "action" && hit.actionId === "templateLinear")).toBe(
      true,
    );
  });
});
