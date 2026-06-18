import { describe, expect, it } from "vitest";

import { DEFAULT_AGENT_ICON, normalizeAgentIcon } from "./chatAgentIcon";

describe("chatAgentIcon", () => {
  it("normaliza slugs Lucide conhecidos", () => {
    expect(normalizeAgentIcon("sparkles")).toBe("sparkles");
    expect(normalizeAgentIcon(" BOT ")).toBe("bot");
    expect(normalizeAgentIcon("book-open")).toBe("book-open");
  });

  it("usa bot como fallback para vazio ou inválido", () => {
    expect(normalizeAgentIcon(null)).toBe(DEFAULT_AGENT_ICON);
    expect(normalizeAgentIcon("")).toBe(DEFAULT_AGENT_ICON);
    expect(normalizeAgentIcon("icone-invalido-xyz")).toBe(DEFAULT_AGENT_ICON);
  });
});
