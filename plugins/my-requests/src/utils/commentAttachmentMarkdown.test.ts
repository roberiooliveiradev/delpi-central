import { describe, expect, it } from "vitest";

import {
  appendAttachmentMarkdown,
  sanitizeAttachmentAlt,
} from "./commentAttachmentMarkdown";

describe("commentAttachmentMarkdown", () => {
  it("sanitiza alt do arquivo", () => {
    expect(sanitizeAttachmentAlt("foto [1].png")).toBe("foto 1.png");
    expect(sanitizeAttachmentAlt("")).toBe("imagem");
  });

  it("anexa tokens attachment: ao body (clip → bolha)", () => {
    expect(
      appendAttachmentMarkdown("anexo", [
        { id: "11111111-2222-3333-4444-555555555555", fileName: "grafico.png" },
      ]),
    ).toBe(
      "anexo\n\n![grafico.png](attachment:11111111-2222-3333-4444-555555555555)",
    );
    expect(
      appendAttachmentMarkdown("", [
        { id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", fileName: "x.jpg" },
      ]),
    ).toBe("![x.jpg](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)");
  });
});
