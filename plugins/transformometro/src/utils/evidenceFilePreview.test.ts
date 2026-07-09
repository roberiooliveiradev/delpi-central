import { describe, expect, it } from "vitest";

import { canPreviewAttachedFile } from "./evidenceFilePreview";

describe("canPreviewAttachedFile", () => {
  it("aceita planilha xlsx", () => {
    expect(
      canPreviewAttachedFile({
        tipo: "documento",
        tipo_mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        nome_arquivo: "IGD IDD METAS rev01.xlsx",
      })
    ).toBe(true);
  });

  it("ignora links externos", () => {
    expect(
      canPreviewAttachedFile({
        tipo: "link",
        nome_arquivo: "https://example.com/doc.xlsx",
      })
    ).toBe(false);
  });
});
