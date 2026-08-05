// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import {
  applyRichTextHtmlAutoClose,
  applyRichTextHtmlTagSuggestion,
  applyRichTextSourceSuggestion,
  findRichTextHtmlTagSuggestionContext,
  findRichTextStyleAttrSlice,
  listRichTextCssPropertySuggestions,
  listRichTextHtmlTagSuggestions,
  resolveRichTextSourceSuggestions,
  richTextHtmlQuotesBalancedBefore,
} from "./richTextHtmlAssist";

describe("findRichTextHtmlTagSuggestionContext", () => {
  it("detecta prefixo após <", () => {
    expect(findRichTextHtmlTagSuggestionContext("<ta", 3)).toEqual({
      start: 0,
      prefix: "ta",
    });
    expect(findRichTextHtmlTagSuggestionContext("x\n<", 3)).toEqual({
      start: 2,
      prefix: "",
    });
  });

  it("ignora fechamento </", () => {
    expect(findRichTextHtmlTagSuggestionContext("</p", 3)).toBeNull();
  });
});

describe("listRichTextHtmlTagSuggestions", () => {
  it("filtra por prefixo", () => {
    expect(listRichTextHtmlTagSuggestions("t")).toContain("table");
    expect(listRichTextHtmlTagSuggestions("t")).toContain("td");
    expect(listRichTextHtmlTagSuggestions("xyz")).toEqual([]);
  });
});

describe("CSS suggestions", () => {
  it("detecta conteúdo dentro de style=", () => {
    const html = '<p style="font-';
    const slice = findRichTextStyleAttrSlice(html, html.length);
    expect(slice?.content).toBe("font-");
  });

  it("sugere propriedades CSS no style", () => {
    const html = '<span style="font-';
    const session = resolveRichTextSourceSuggestions(html, html.length);
    expect(session?.kind).toBe("css-prop");
    expect(session?.items).toContain("font-size");
    expect(session?.items).toContain("font-family");
  });

  it("sugere valores CSS após prop:", () => {
    const html = '<p style="text-align: c';
    const session = resolveRichTextSourceSuggestions(html, html.length);
    expect(session?.kind).toBe("css-value");
    expect(session?.cssProperty).toBe("text-align");
    expect(session?.items).toContain("center");
  });

  it("aplica propriedade CSS com cursor após ': '", () => {
    const html = '<p style="col';
    const session = resolveRichTextSourceSuggestions(html, html.length);
    expect(session).toBeTruthy();
    const edit = applyRichTextSourceSuggestion(html, html.length, session!, "color");
    expect(edit?.value).toBe('<p style="color: ');
    expect(edit?.selectionStart).toBe('<p style="color: '.length);
  });

  it("aplica valor CSS", () => {
    const html = '<p style="text-align: c';
    const session = resolveRichTextSourceSuggestions(html, html.length)!;
    const edit = applyRichTextSourceSuggestion(html, html.length, session, "center");
    expect(edit?.value).toBe('<p style="text-align: center');
  });

  it("lista propriedades por prefixo", () => {
    expect(listRichTextCssPropertySuggestions("back")).toContain("background-color");
  });
});

describe("applyRichTextHtmlTagSuggestion", () => {
  it("completa o nome da tag e posiciona o cursor após o nome", () => {
    const edit = applyRichTextHtmlTagSuggestion("<ta", 3, "table");
    expect(edit).toEqual({
      value: "<table",
      selectionStart: 6,
      selectionEnd: 6,
    });
  });
});

describe("applyRichTextHtmlAutoClose", () => {
  it("insere fechamento e deixa cursor no meio", () => {
    const edit = applyRichTextHtmlAutoClose("<p>", 3);
    expect(edit).toEqual({
      value: "<p></p>",
      selectionStart: 3,
      selectionEnd: 3,
    });
  });

  it("não fecha void tags", () => {
    expect(applyRichTextHtmlAutoClose("<br>", 4)).toBeNull();
  });

  it("não duplica fechamento já presente", () => {
    expect(applyRichTextHtmlAutoClose("<p></p>", 3)).toBeNull();
  });
});

describe("richTextHtmlQuotesBalancedBefore", () => {
  it("detecta aspas abertas em atributos", () => {
    expect(richTextHtmlQuotesBalancedBefore('<p style="color:', 16)).toBe(false);
    expect(richTextHtmlQuotesBalancedBefore('<p style="color:red">', 21)).toBe(true);
  });
});
