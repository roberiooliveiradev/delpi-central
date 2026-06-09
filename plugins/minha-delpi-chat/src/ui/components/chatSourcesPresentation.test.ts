import { describe, expect, it } from "vitest";

import type { ChatSource } from "../../data/api/chatTypes";

import { resolveSourcePresentation } from "./ChatSources";

const webSource = (url: string): ChatSource => ({
  scope: "web_search",
  sourceRef: url,
  title: "Título",
});

const ragSource = (): ChatSource => ({
  scope: "global",
  title: "Norma interna",
  sourceRef: "doc-1",
});

describe("resolveSourcePresentation", () => {
  it("usa cards e oculta badges quando há 2+ fontes web", () => {
    const result = resolveSourcePresentation([
      webSource("https://a.example"),
      webSource("https://b.example"),
    ]);

    expect(result).toEqual({ showSourceCards: true, showSourceBadges: false });
  });

  it("mantém badges para fonte web única", () => {
    const result = resolveSourcePresentation([webSource("https://a.example")]);

    expect(result).toEqual({ showSourceCards: false, showSourceBadges: true });
  });

  it("mantém badges para fontes de conhecimento interno", () => {
    const result = resolveSourcePresentation([ragSource(), ragSource()]);

    expect(result).toEqual({ showSourceCards: false, showSourceBadges: true });
  });
});
