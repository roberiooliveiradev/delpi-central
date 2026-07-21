import { describe, expect, it } from "vitest";

import {
  DELPI_TV_BLOCKS_CLIPBOARD_PREFIX,
  blocksFromExternalHtml,
  blocksFromPlainText,
  parseInternalBlocksPayload,
  planExternalClipboardPaste,
  serializeInternalBlocksPayload,
  tryParseTabularText,
} from "./externalClipboardPaste";

function mockDataTransfer(parts: {
  plain?: string;
  html?: string;
  files?: File[];
}): DataTransfer {
  const files = parts.files ?? [];
  return {
    getData: (type: string) => {
      if (type === "text/plain") return parts.plain ?? "";
      if (type === "text/html") return parts.html ?? "";
      return "";
    },
    files: files as unknown as FileList,
    items: [] as unknown as DataTransferItemList,
  } as DataTransfer;
}

describe("externalClipboardPaste", () => {
  it("serializa e restaura blocos internos", () => {
    const payload = serializeInternalBlocksPayload([
      { id: "a", type: "text", content: "Olá", frame: { x: 1, y: 2, w: 3, h: 4 } } as never,
    ]);
    expect(payload.startsWith(DELPI_TV_BLOCKS_CLIPBOARD_PREFIX)).toBe(true);
    const blocks = parseInternalBlocksPayload(payload);
    expect(blocks).toHaveLength(1);
    expect(blocks?.[0].type).toBe("text");
  });

  it("detecta TSV do Excel/Sheets como tabela", () => {
    const block = tryParseTabularText("A\tB\n1\t2\n3\t4");
    expect(block?.type).toBe("canvas_table");
    if (block?.type === "canvas_table") {
      expect(block.rows).toBe(3);
      expect(block.cols).toBe(2);
      expect(block.cells[0]).toEqual(["A", "B"]);
    }
  });

  it("cria texto a partir de plain text", () => {
    const blocks = blocksFromPlainText("Missão da empresa");
    expect(blocks).toHaveLength(1);
    expect(blocks[0].type).toBe("heading");
  });

  it("extrai forma com fundo a partir de HTML", () => {
    const blocks = blocksFromExternalHtml(
      `<div style="background-color:#e8f4fc;border-radius:8px">Missão: gerar valor</div>`,
    );
    expect(blocks.length).toBeGreaterThanOrEqual(1);
    expect(blocks.some((block) => block.type === "shape" || block.type === "text" || block.type === "heading")).toBe(
      true,
    );
  });

  it("prioriza payload interno sobre HTML", () => {
    const internal = serializeInternalBlocksPayload([
      { id: "x", type: "text", content: "interno", frame: { x: 0, y: 0, w: 10, h: 10 } } as never,
    ]);
    const plan = planExternalClipboardPaste(
      mockDataTransfer({
        plain: internal,
        html: `<div style="background:#fff">externo</div>`,
      }),
    );
    expect(plan.kind).toBe("internal-blocks");
  });

  it("prioriza imagem sobre HTML (recorte do Slides)", () => {
    const file = new File([new Uint8Array([1, 2, 3])], "clip.png", { type: "image/png" });
    const plan = planExternalClipboardPaste(
      mockDataTransfer({
        html: `<div style="background:#fff"> Ignorar </div>`,
        plain: "Ignorar",
        files: [file],
      }),
    );
    expect(plan.kind).toBe("images");
    if (plan.kind === "images") expect(plan.files).toHaveLength(1);
  });
});
