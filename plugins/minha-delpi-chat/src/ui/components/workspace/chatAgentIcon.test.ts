import { describe, expect, it } from "vitest";

import { DEFAULT_AGENT_ICON, normalizeAgentIcon } from "./chatAgentIcon";

describe("chatAgentIcon", () => {
  it("normaliza slugs Lucide conhecidos", () => {
    expect(normalizeAgentIcon("sparkles")).toBe("sparkles");
    expect(normalizeAgentIcon(" BOT ")).toBe("bot");
  });

  it("usa bot como fallback", () => {
    expect(normalizeAgentIcon(null)).toBe(DEFAULT_AGENT_ICON);
    expect(normalizeAgentIcon("icone-invalido")).toBe(DEFAULT_AGENT_ICON);
  });
});
