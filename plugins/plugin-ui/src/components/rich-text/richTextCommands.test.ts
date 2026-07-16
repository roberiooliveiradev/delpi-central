// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import {
  normalizeRichTextLinkUrl,
  unwrapRichTextLink,
} from "./richTextCommands";
import { clampRichTextFontSize } from "./richTextConfig";

describe("richTextConfig", () => {
  it("limita tamanho de fonte", () => {
    expect(clampRichTextFontSize(8)).toBe(10);
    expect(clampRichTextFontSize(80)).toBe(72);
    expect(clampRichTextFontSize(16.4)).toBe(16);
  });
});

describe("normalizeRichTextLinkUrl", () => {
  it("mantém URLs com esquema, âncoras e paths", () => {
    expect(normalizeRichTextLinkUrl("https://delpi.com.br")).toBe("https://delpi.com.br");
    expect(normalizeRichTextLinkUrl("mailto:x@delpi.com.br")).toBe("mailto:x@delpi.com.br");
    expect(normalizeRichTextLinkUrl("/apps/cipa")).toBe("/apps/cipa");
    expect(normalizeRichTextLinkUrl("#secao")).toBe("#secao");
  });

  it("completa https:// para domínio sem esquema", () => {
    expect(normalizeRichTextLinkUrl("delpi.com.br/ata")).toBe("https://delpi.com.br/ata");
  });

  it("retorna vazio para entrada em branco", () => {
    expect(normalizeRichTextLinkUrl("  ")).toBe("");
  });
});

describe("unwrapRichTextLink", () => {
  it("remove a âncora preservando o conteúdo", () => {
    const wrapper = document.createElement("p");
    wrapper.innerHTML = 'antes <a href="https://x.dev">meio <b>forte</b></a> depois';
    const anchor = wrapper.querySelector("a")!;

    unwrapRichTextLink(anchor);

    expect(wrapper.querySelector("a")).toBeNull();
    expect(wrapper.innerHTML).toBe("antes meio <b>forte</b> depois");
  });
});
