import { describe, expect, it } from "vitest";

import { isHtmlEmpty, mergeAtaContentHtml, splitAtaContentForSave } from "./ataContent";

describe("ataContent", () => {
  it("detecta HTML vazio", () => {
    expect(isHtmlEmpty("<p></p>")).toBe(true);
    expect(isHtmlEmpty("<p>Olá</p>")).toBe(false);
  });

  it("merge retorna única seção preenchida sem título extra", () => {
    expect(
      mergeAtaContentHtml({
        agenda_html: "<p></p>",
        body_html: "<p>Registro</p>",
        decisions_html: "",
        pending_html: "",
        observations_html: "",
      }),
    ).toBe("<p>Registro</p>");
  });

  it("merge une múltiplas seções com h2", () => {
    const merged = mergeAtaContentHtml({
      agenda_html: "<p>Pauta A</p>",
      body_html: "<p>Corpo</p>",
      decisions_html: "",
      pending_html: "",
      observations_html: "",
    });
    expect(merged).toContain("<h2>Pauta</h2>");
    expect(merged).toContain("<h2>Registro</h2>");
  });

  it("split concentra conteúdo em body_html", () => {
    expect(splitAtaContentForSave("<p>Único</p>")).toEqual({
      agenda_html: "<p></p>",
      body_html: "<p>Único</p>",
      decisions_html: "<p></p>",
      pending_html: "<p></p>",
      observations_html: "<p></p>",
    });
  });
});
