import { describe, expect, it } from "vitest";

import { canPreviewFile, resolveFilePreviewKind } from "./resolveFilePreviewKind";

describe("resolveFilePreviewKind", () => {
  it("detecta imagem, pdf, planilha, docx e texto", () => {
    expect(resolveFilePreviewKind({ mimeType: "image/png" })).toBe("image");
    expect(resolveFilePreviewKind({ mimeType: "application/pdf" })).toBe("pdf");
    expect(resolveFilePreviewKind({ fileName: "dados.xlsx" })).toBe("spreadsheet");
    expect(resolveFilePreviewKind({ fileName: "doc.docx" })).toBe("docx");
    expect(resolveFilePreviewKind({ fileName: "notas.txt" })).toBe("text");
  });

  it("respeita declaredType do domínio", () => {
    expect(resolveFilePreviewKind({ declaredType: "manual_text", mimeType: "application/octet-stream" })).toBe(
      "text",
    );
    expect(canPreviewFile({ declaredType: "spreadsheet", fileName: "x.bin" })).toBe(true);
  });
});
