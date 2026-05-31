import { describe, expect, it } from "vitest";

import {
  agentIcebreakersUseDefaults,
  buildIcebreakerPlaceholderToken,
  getIcebreakerGridDensityClass,
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
});
