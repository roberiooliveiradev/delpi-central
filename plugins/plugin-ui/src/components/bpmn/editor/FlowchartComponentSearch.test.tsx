import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import { FlowchartComponentSearch } from "./FlowchartComponentSearch";

const labels = {
  componentSearchPlaceholder: "Buscar componente…",
  componentSearchAriaLabel: "Buscar componente BPMN",
  componentSearchEmpty: "Nenhum componente encontrado.",
  componentSearchClear: "Limpar busca",
  nodeHints: {},
} as FlowchartEditorLabels;

afterEach(() => {
  cleanup();
});

describe("FlowchartComponentSearch", () => {
  it("lista hits e adiciona o componente escolhido", () => {
    const onAddNode = vi.fn();
    render(<FlowchartComponentSearch labels={labels} onAddNode={onAddNode} />);

    const input = screen.getByLabelText("Buscar componente BPMN") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "xor" } });

    fireEvent.click(screen.getByRole("option", { name: /Decisão \(XOR\)/i }));

    expect(onAddNode).toHaveBeenCalledWith("decision");
    expect(input.value).toBe("");
  });

  it("mostra vazio quando não há match", () => {
    render(<FlowchartComponentSearch labels={labels} onAddNode={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Buscar componente BPMN"), {
      target: { value: "zzzz-inexistente" },
    });
    expect(screen.getByText("Nenhum componente encontrado.")).toBeTruthy();
  });
});
