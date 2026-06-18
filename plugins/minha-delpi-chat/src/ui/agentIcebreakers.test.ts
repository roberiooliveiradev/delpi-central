import { describe, expect, it } from "vitest";

import {
  agentIcebreakersUseDefaults,
  buildIcebreakerPlaceholderToken,
  getIcebreakerGridDensityClass,
  reorderIcebreakers,
  resolveAgentIcebreakersForDisplay,
  resolveAgentIcebreakersForEditor,
} from "./agentIcebreakers";
import { DEFAULT_AGENT_ICEBREAKERS } from "./chatHomeStarters";

describe("agentIcebreakers", () => {
  it("usa padrões na home e no editor quando metadata está vazio", () => {
    expect(resolveAgentIcebreakersForDisplay({})).toEqual(DEFAULT_AGENT_ICEBREAKERS);
    expect(resolveAgentIcebreakersForEditor({})).toEqual(DEFAULT_AGENT_ICEBREAKERS);
    expect(agentIcebreakersUseDefaults({})).toBe(true);
  });

  it("respeita quebra-gelos configurados", () => {
    const metadata = {
      icebreakers: ["me fale do produto {{productCode}}"],
    };

    expect(resolveAgentIcebreakersForDisplay(metadata)).toEqual([
      "me fale do produto {{productCode}}",
    ]);
    expect(resolveAgentIcebreakersForEditor(metadata)).toEqual([
      "me fale do produto {{productCode}}",
    ]);
    expect(agentIcebreakersUseDefaults(metadata)).toBe(false);
  });

  it("gera token de placeholder", () => {
    expect(buildIcebreakerPlaceholderToken("productCode")).toBe("{{productCode}}");
  });

  it("usa grid 2x2 para quatro sugestões", () => {
    expect(getIcebreakerGridDensityClass(4)).toBe(
      "mdc-chat-agent-home__icebreakers--quad",
    );
  });

  it("reordena quebra-gelos preservando conteúdo", () => {
    const items = ["a", "b", "c"];

    expect(reorderIcebreakers(items, 0, 2)).toEqual(["b", "c", "a"]);
    expect(reorderIcebreakers(items, 2, 0)).toEqual(["c", "a", "b"]);
    expect(reorderIcebreakers(items, 1, 1)).toEqual(["a", "b", "c"]);
    expect(reorderIcebreakers(items, -1, 0)).toEqual(["a", "b", "c"]);
  });
});
