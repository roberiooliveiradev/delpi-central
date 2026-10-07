// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoBlock, ComunicadoInputBlock } from "@delpi/tv-dashboard-presentation";

const editor = vi.hoisted(() => ({
  selected: null as ComunicadoBlock | null,
  config: { version: 5, blocks: [] as ComunicadoBlock[] },
  patchInputBlock: vi.fn(),
  scheduleInputFilterRefresh: vi.fn(),
}));

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => editor,
}));

vi.mock("../api/tvDashboardApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/tvDashboardApi")>();
  return { ...actual, listDataRoutes: vi.fn().mockResolvedValue([]) };
});

import { InputBindingInspector } from "./InputBindingInspector";

const legacyInput: ComunicadoInputBlock = {
  id: "in-branch",
  type: "input",
  frame: { x: 0, y: 0, w: 20, h: 10 },
  input: { paramKey: "branch", targetScope: "slide", defaultValue: "01" },
};

function variableInput(id: string, key: string): ComunicadoInputBlock {
  return {
    id,
    type: "input",
    frame: { x: 0, y: 0, w: 20, h: 10 },
    input: {
      paramKey: "",
      binding: { kind: "variable", key },
      valueSchema: { type: "integer", enum: [0, 1], enumLabels: { "0": "Segunda-feira", "1": "Terça-feira" } },
      defaultValue: 0,
    },
  };
}

function chooseOption(trigger: HTMLElement, label: string) {
  fireEvent.click(trigger);
  const option = screen
    .getAllByRole("listbox")
    .flatMap((list) => Array.from(list.querySelectorAll("button")))
    .find((button) => button.textContent === label);
  expect(option, `opção ${label}`).toBeTruthy();
  fireEvent.click(option!);
}

beforeEach(() => {
  editor.patchInputBlock.mockReset();
});

afterEach(() => cleanup());

describe("InputBindingInspector — Ligação", () => {
  it("legado → variável: limpa paramKey/alvo e cria binding + valueSchema", () => {
    editor.selected = legacyInput;
    editor.config = { version: 5, blocks: [legacyInput] };
    render(<InputBindingInspector />);
    chooseOption(screen.getByRole("button", { name: "Ligação do campo" }), "Variável reutilizável do slide");
    expect(editor.patchInputBlock).toHaveBeenCalledWith("in-branch", {
      paramKey: "",
      targetScope: undefined,
      targetSourceIds: undefined,
      binding: { kind: "variable", key: "variable_1" },
      valueSchema: { type: "string" },
      defaultValue: null,
    });
  });

  it("variável → parâmetro de dados: remove binding/valueSchema", () => {
    const block = variableInput("in-md", "meeting_day");
    editor.selected = block;
    editor.config = { version: 5, blocks: [block] };
    render(<InputBindingInspector />);
    expect((screen.getByLabelText("Chave da variável") as HTMLInputElement).value).toBe("meeting_day");
    chooseOption(screen.getByRole("button", { name: "Ligação do campo" }), "Parâmetro de dados");
    expect(editor.patchInputBlock).toHaveBeenCalledWith("in-md", {
      binding: undefined,
      valueSchema: undefined,
      paramKey: "",
      targetScope: "slide",
      defaultValue: null,
    });
  });

  it("chave duplicada no slide não é gravada", () => {
    const block = variableInput("in-md", "meeting_day");
    const other = variableInput("in-other", "other_key");
    editor.selected = block;
    editor.config = { version: 5, blocks: [block, other] };
    render(<InputBindingInspector />);
    const keyInput = screen.getByLabelText("Chave da variável");
    fireEvent.change(keyInput, { target: { value: "other_key" } });
    fireEvent.blur(keyInput);
    expect(screen.getByText(/Já existe uma variável com esta chave/)).toBeTruthy();
    expect(editor.patchInputBlock).not.toHaveBeenCalled();

    fireEvent.change(keyInput, { target: { value: "reference_day" } });
    fireEvent.blur(keyInput);
    expect(editor.patchInputBlock).toHaveBeenCalledWith("in-md", {
      binding: { kind: "variable", key: "reference_day" },
    });
  });

  it("opções valor=rótulo gravam enum tipado + enumLabels", () => {
    const block = variableInput("in-md", "meeting_day");
    editor.selected = block;
    editor.config = { version: 5, blocks: [block] };
    render(<InputBindingInspector />);
    const options = screen.getByLabelText("Opções (opcional)");
    fireEvent.change(options, { target: { value: "0=Segunda-feira\n2=Quarta-feira" } });
    fireEvent.blur(options);
    expect(editor.patchInputBlock).toHaveBeenCalledWith("in-md", {
      valueSchema: {
        type: "integer",
        enum: [0, 2],
        enumLabels: { "0": "Segunda-feira", "2": "Quarta-feira" },
      },
    });
  });
});
