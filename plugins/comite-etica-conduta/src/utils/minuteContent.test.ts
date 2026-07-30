import { describe, expect, it } from "vitest";

import { mergeMinuteContentHtml, splitMinuteContentForSave } from "./minuteContent";

describe("minuteContent", () => {
  it("retorna body quando só há conteúdo principal", () => {
    expect(
      mergeMinuteContentHtml({
        body_html: "<p>Texto</p>",
        agenda_html: "<p></p>",
      }),
    ).toBe("<p>Texto</p>");
  });

  it("une seções preenchidas com títulos", () => {
    const merged = mergeMinuteContentHtml({
      agenda_html: "<p>Pauta X</p>",
      body_html: "<p>Corpo</p>",
      decisions_html: "<p></p>",
      pending_html: "<p>Pend 1</p>",
    });
    expect(merged).toContain("<h2>Pauta</h2>");
    expect(merged).toContain("<h2>Conteúdo</h2>");
    expect(merged).toContain("<h2>Pendências</h2>");
  });

  it("salva tudo em body_html", () => {
    expect(splitMinuteContentForSave("<p>Único</p>").body_html).toBe("<p>Único</p>");
    expect(splitMinuteContentForSave("<p>Único</p>").agenda_html).toBe("<p></p>");
  });
});
