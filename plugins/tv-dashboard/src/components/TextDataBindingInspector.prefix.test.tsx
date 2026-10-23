import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TextDataBindingInspector } from "./TextDataBindingInspector";

/**
 * Task 029 — contrato de string vazia no «Campo dinâmico».
 *
 * O canal governado (upsert_block) é partial-patch com merge profundo:
 * chave AUSENTE = preservar, `""` = valor válido (schema string). Um
 * `value || undefined` na borda do input apaga a intenção do usuário —
 * o merge ressuscita o prefixo antigo e o ACK o restaura localmente.
 * O estado autoral deve serializar `""` — nunca omitir a chave.
 */

const updateSelected = vi.fn();

const block = {
  id: "txt-dyn",
  type: "text",
  content: "Pendentes: ",
  frame: { x: 0, y: 0, w: 20, h: 10 },
  dataSourceId: "src-1",
  textProjection: {
    field: "qty",
    aggregation: "first",
    format: "raw",
    prefix: "r",
    suffix: " un",
    fallback: "N/D",
  },
};

const editorState = {
  selected: block,
  blocks: [block],
  config: { version: 2, blocks: [block], dataModels: [] },
  updateSelected,
  openDataCatalog: vi.fn(),
  getDataPreviewResolved: vi.fn(() => undefined),
};

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => editorState,
}));

function projectionPatch(): Record<string, unknown> {
  const patch = updateSelected.mock.calls.at(-1)?.[0] as
    | { textProjection?: Record<string, unknown> }
    | undefined;
  return patch?.textProjection ?? {};
}

function sectionInputs(): HTMLInputElement[] {
  const section = document.querySelector(".td-text-data-binding-sections")!;
  return [...section.querySelectorAll<HTMLInputElement>("input")];
}

const INPUT_ORDER = { Prefixo: 0, Sufixo: 1, "Se vazio": 2 } as const;

function sectionInput(label: keyof typeof INPUT_ORDER): HTMLInputElement {
  return sectionInputs()[INPUT_ORDER[label]]!;
}

function clearInput(label: keyof typeof INPUT_ORDER) {
  const input = sectionInput(label);
  expect(input, `input "${label}" deve existir`).toBeTruthy();
  fireEvent.change(input, { target: { value: "" } });
}

describe("TextDataBindingInspector — contrato de string vazia (029)", () => {
  beforeEach(() => {
    updateSelected.mockClear();
  });

  it("Prefixo r → vazio serializa \"prefix\":\"\" — nunca omite a chave", () => {
    render(<TextDataBindingInspector layout="pane" />);
    clearInput("Prefixo");
    expect(updateSelected).toHaveBeenCalledOnce();
    const projection = projectionPatch();
    // A chave precisa chegar ao wire: ausente no JSON = keep no merge do server.
    expect(Object.keys(projection)).toContain("prefix");
    expect(projection.prefix).toBe("");
    expect(JSON.stringify(projection)).toContain('"prefix":""');
  });

  it("Sufixo removido serializa \"suffix\":\"\" (mesmo contrato do prefixo)", () => {
    render(<TextDataBindingInspector layout="pane" />);
    clearInput("Sufixo");
    const projection = projectionPatch();
    expect(projection.suffix).toBe("");
    expect(JSON.stringify(projection)).toContain('"suffix":""');
  });

  it("Se vazio (fallback) removido serializa \"fallback\":\"\"", () => {
    render(<TextDataBindingInspector layout="pane" />);
    clearInput("Se vazio");
    const projection = projectionPatch();
    expect(projection.fallback).toBe("");
    expect(JSON.stringify(projection)).toContain('"fallback":""');
  });

  it("Prefixo vazio → novo valor persiste normalmente (sem regressão)", () => {
    const noPrefixBlock = {
      ...block,
      textProjection: { field: "qty", aggregation: "first" },
    };
    editorState.selected = noPrefixBlock;
    render(<TextDataBindingInspector layout="pane" />);
    fireEvent.change(sectionInput("Prefixo"), {
      target: { value: "R$ " },
    });
    const projection = projectionPatch();
    expect(projection.prefix).toBe("R$ ");
    editorState.selected = block;
  });
});
