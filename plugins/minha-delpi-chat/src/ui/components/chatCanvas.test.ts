import { describe, expect, it } from "vitest";

import { getCanvasOpenFromMetadata, normalizeCanvasOpenPayload } from "./chatCanvas";

describe("chatCanvas", () => {
  it("normaliza payload com markdown", () => {
    expect(
      normalizeCanvasOpenPayload({
        title: "Informações do produto",
        markdown: "### Produto\n\nDetalhes",
        sourceMessageId: "msg-1",
      }),
    ).toEqual({
      title: "Informações do produto",
      markdown: "### Produto\n\nDetalhes",
      messageId: null,
      sourceMessageId: "msg-1",
    });
  });

  it("lê canvasOpen do metadata da mensagem", () => {
    expect(
      getCanvasOpenFromMetadata({
        canvasOpen: {
          title: "Lousa",
          markdown: "Conteúdo",
        },
      })?.markdown,
    ).toBe("Conteúdo");
  });
});
