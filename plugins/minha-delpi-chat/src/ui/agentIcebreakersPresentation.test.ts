import { describe, expect, it } from "vitest";

import { resolveIcebreakerCardPresentation } from "./agentIcebreakers";

describe("resolveIcebreakerCardPresentation", () => {
  it("separa rótulo e exemplo dos templates padrão", () => {
    expect(
      resolveIcebreakerCardPresentation("me fale do produto {{productCode}}"),
    ).toEqual({
      title: "Consultar produto",
      subtitle: "10080001",
    });
  });

  it("mantém pergunta sem placeholder só no título", () => {
    expect(resolveIcebreakerCardPresentation("o que você pode fazer?")).toEqual({
      title: "Capacidades",
    });
  });
});
