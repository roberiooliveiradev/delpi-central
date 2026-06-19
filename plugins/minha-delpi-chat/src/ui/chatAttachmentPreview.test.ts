import { describe, expect, it } from "vitest";

import {
  formatAttachmentSize,
  resolveAttachmentPreviewKind,
} from "./chatAttachmentPreview";

describe("chatAttachmentPreview", () => {
  it("resolveAttachmentPreviewKind classifica imagem, pdf, texto, planilha e docx", () => {
    expect(resolveAttachmentPreviewKind("image/png", "foto.png")).toBe("image");
    expect(resolveAttachmentPreviewKind("application/pdf", "relatorio.pdf")).toBe("pdf");
    expect(resolveAttachmentPreviewKind("text/plain", "notas.txt")).toBe("text");
    expect(
      resolveAttachmentPreviewKind(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "dados.xlsx",
      ),
    ).toBe("spreadsheet");
    expect(
      resolveAttachmentPreviewKind(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "relatorio.docx",
      ),
    ).toBe("docx");
    expect(resolveAttachmentPreviewKind("application/octet-stream", "arquivo.bin")).toBe(
      "unsupported",
    );
  });

  it("formatAttachmentSize formata bytes, KB e MB", () => {
    expect(formatAttachmentSize(512)).toBe("512 B");
    expect(formatAttachmentSize(2048)).toBe("2.0 KB");
    expect(formatAttachmentSize(2 * 1024 * 1024)).toBe("2.0 MB");
  });
});
