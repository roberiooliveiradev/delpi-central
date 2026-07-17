import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DataQueryCompileResult, DataQueryFunction } from "../domain/dataQueryTypes";
import { DataPrepareAdvancedEditor } from "./DataPrepareAdvancedEditor";
import { DataPrepareAppliedSteps } from "./DataPrepareAppliedSteps";

const script = "let\n    Etapa = Table.Skip(Fonte, 1)\nin\n    Etapa";
const compiled: DataQueryCompileResult = {
  profile: "m-delpi-v1",
  canonicalScript: script,
  scriptHash: "sha256:test",
  outputStepName: "Etapa",
  steps: [
    { name: "Etapa", label: "Etapa", operation: "Table.Skip", formula: "Table.Skip(Fonte, 1)" },
  ],
  diagnostics: [
    {
      code: "m.example",
      severity: "warning",
      message: "Aviso",
      range: {
        startLine: 2,
        startColumn: 5,
        endLine: 2,
        endColumn: 10,
        startOffset: 8,
        endOffset: 13,
      },
    },
  ],
  referencedQueries: ["Origem"],
  completionContext: {
    steps: ["Etapa"],
    columns: ["valor"],
    queries: ["Origem"],
    items: [
      { label: "valor", insertText: "[valor]", kind: "column" },
      { label: "Origem", insertText: "Origem", kind: "query" },
    ],
  },
  syntaxTokens: [{ kind: "keyword", startOffset: 0, endOffset: 3 }],
};
const functions: DataQueryFunction[] = [
  {
    name: "Table.Skip",
    kind: "transform",
    category: "Linhas",
    signature: "Table.Skip(table, count)",
    description: "Ignora linhas.",
    parameters: ["table", "count"],
    examples: ["Table.Skip(Fonte, 1)"],
    introducedIn: "1.0.0",
    availability: { ribbon: true, formulaBar: true, advancedEditor: true },
  },
];

afterEach(cleanup);

function setup() {
  const props = {
    open: true,
    script,
    compiled,
    functions,
    loadingFunctions: false,
    canUndo: true,
    canRedo: true,
    onChange: vi.fn(),
    onCompile: vi.fn(async () => undefined),
    onFormat: vi.fn(async () => undefined),
    onUndo: vi.fn(),
    onRedo: vi.fn(),
    onClose: vi.fn(),
  };
  render(<DataPrepareAdvancedEditor {...props} />);
  return props;
}

describe("editor avançado M", () => {
  it("mantém fallback responsivo e CSS estritamente escopado", () => {
    const css = readFileSync(resolve(process.cwd(), "src/index.css"), "utf8");
    expect(css).toMatch(/@media \(max-width: 900px\)[\s\S]*td-data-pq__editor-shell/);
    expect(css).toMatch(
      /\.dashboard-tv-dashboard \.td-data-pq__editor-input/,
    );
  });
  it("oferece autocomplete server-driven com assinatura e contexto compile", () => {
    setup();
    const editor = screen.getByRole("textbox", { name: "Script M" }) as HTMLTextAreaElement;
    editor.setSelectionRange(0, 0);
    fireEvent.keyDown(editor, { key: " ", ctrlKey: true });
    expect(screen.getByRole("listbox", { name: "Sugestões M" })).toBeTruthy();
    expect(screen.getByRole("option", { name: /Table\.Skip/ }).textContent).toContain(
      "Table.Skip(table, count)",
    );
    expect(screen.getByText("valor")).toBeTruthy();
  });

  it("preserva atalhos locais, formatter e compile explícito", () => {
    const props = setup();
    const editor = screen.getByRole("textbox", { name: "Script M" });
    fireEvent.keyDown(editor, { key: "z", ctrlKey: true });
    fireEvent.keyDown(editor, { key: "Z", ctrlKey: true, shiftKey: true });
    fireEvent.keyDown(editor, { key: "Enter", ctrlKey: true });
    fireEvent.click(screen.getByRole("button", { name: "Formatar" }));
    expect(props.onUndo).toHaveBeenCalledOnce();
    expect(props.onRedo).toHaveBeenCalledOnce();
    expect(props.onCompile).toHaveBeenCalledWith(script);
    expect(props.onFormat).toHaveBeenCalledOnce();
  });

  it("navega para range de diagnóstico e fecha sugestões com Escape", () => {
    const props = setup();
    const editor = screen.getByRole("textbox", { name: "Script M" }) as HTMLTextAreaElement;
    fireEvent.click(screen.getByRole("button", { name: /m\.example/ }));
    expect(editor.selectionStart).toBe(8);
    expect(editor.selectionEnd).toBe(13);
    fireEvent.keyDown(editor, { key: " ", metaKey: true });
    fireEvent.keyDown(editor, { key: "Escape" });
    expect(screen.queryByRole("listbox")).toBeNull();
    fireEvent.keyDown(editor, { key: "Escape" });
    expect(props.onClose).toHaveBeenCalledOnce();
  });

  it("expõe realce recebido do backend e foco acessível", () => {
    setup();
    expect(document.querySelector(".td-data-pq__token--keyword")?.textContent).toBe("let");
    expect(document.activeElement).toBe(screen.getByRole("textbox", { name: "Script M" }));
  });
});

describe("busca e rename de etapas", () => {
  it("filtra etapas e envia rename por nome lógico", () => {
    const rename = vi.fn();
    render(
      <DataPrepareAppliedSteps
        steps={[
          { name: "Primeira", label: "Primeira", operation: "x", formula: "x" },
          { name: "Segunda", label: "Segunda", operation: "x", formula: "x" },
        ]}
        selectedStepName={null}
        onSelect={() => undefined}
        onMove={() => undefined}
        onRemove={() => undefined}
        onRename={rename}
      />,
    );
    fireEvent.change(screen.getByRole("searchbox", { name: "Buscar etapa" }), {
      target: { value: "Seg" },
    });
    expect(screen.queryByRole("button", { name: "Primeira" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Renomear Segunda" }));
    const input = screen.getByRole("textbox", { name: "Novo nome de Segunda" });
    fireEvent.change(input, { target: { value: "Final" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(rename).toHaveBeenCalledWith("Segunda", "Final");
  });
});
