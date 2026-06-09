import { describe, expect, it } from "vitest";

import {
  formatAttachmentSize,
  resolveAttachmentPreviewKind,
} from "./chatAttachmentPreview";

describe("chatAttachmentPreview", () => {
  it("resolveAttachmentPreviewKind classifica imagem, pdf e texto", () => {
    expect(resolveAttachmentPreviewKind("image/png", "foto.png")).toBe("image");
    expect(resolveAttachmentPreviewKind("application/pdf", "relatorio.pdf")).toBe("pdf");
    expect(resolveAttachmentPreviewKind("text/plain", "notas.txt")).toBe("text");
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
