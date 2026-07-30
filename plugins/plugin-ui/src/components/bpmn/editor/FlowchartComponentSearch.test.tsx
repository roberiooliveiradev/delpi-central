import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import { FlowchartComponentSearch } from "./FlowchartComponentSearch";

const labels = {
  componentSearchPlaceholder: "Buscar componente…",
  componentSearchAriaLabel: "Buscar componente BPMN",
  componentSearchEmpty: "Nenhum componente encontrado.",
  componentSearchClear: "Limpar busca",
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
    { id: "lanes", label: "Faixas" },
  ],
  elementGroupTabHints: {},
  eventSubTabs: [],
  eventSubTabHints: {},
  editorActions: [
    { id: "addLane", label: "Faixa", hint: "Adiciona uma faixa (swimlane)." },
    { id: "autoLayout", label: "Layout automático", hint: "Reorganiza." },
    { id: "templateLinear", label: "Modelo linear", hint: "Linear." },
    { id: "templateDecision", label: "Modelo decisão", hint: "Decisão." },
    { id: "templateSwimlanes", label: "Modelo BPMN com faixas", hint: "Faixas." },
  ],
  nodeHints: {},
} as FlowchartEditorLabels;

afterEach(() => {
  cleanup();
});

describe("FlowchartComponentSearch", () => {
  it("lista hits e adiciona o nó escolhido", () => {
    const onAddNode = vi.fn();
    const onEditorAction = vi.fn();
    render(
      <FlowchartComponentSearch
        labels={labels}
        onAddNode={onAddNode}
        onEditorAction={onEditorAction}
      />,
    );

    const input = screen.getByLabelText("Buscar componente BPMN") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "xor" } });

    fireEvent.click(screen.getByRole("option", { name: /Decisão \(XOR\)/i }));

    expect(onAddNode).toHaveBeenCalledWith("decision");
    expect(input.value).toBe("");
  });

  it("executa ação de Faixa ao escolher na busca", () => {
    const onAddNode = vi.fn();
    const onEditorAction = vi.fn();
    render(
      <FlowchartComponentSearch
        labels={labels}
        onAddNode={onAddNode}
        onEditorAction={onEditorAction}
      />,
    );

    fireEvent.change(screen.getByLabelText("Buscar componente BPMN"), {
      target: { value: "faixa" },
    });
    const faixaOption = screen
      .getAllByRole("option")
      .find((el) => el.id.includes("action:addLane"));
    expect(faixaOption).toBeTruthy();
    fireEvent.click(faixaOption!);

    expect(onEditorAction).toHaveBeenCalledWith("addLane");
    expect(onAddNode).not.toHaveBeenCalled();
  });

  it("mostra vazio quando não há match", () => {
    render(
      <FlowchartComponentSearch
        labels={labels}
        onAddNode={vi.fn()}
        onEditorAction={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByLabelText("Buscar componente BPMN"), {
      target: { value: "zzzz-inexistente" },
    });
    expect(screen.getByText("Nenhum componente encontrado.")).toBeTruthy();
  });
});
