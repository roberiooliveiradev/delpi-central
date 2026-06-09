import { describe, expect, it } from "vitest";

import {
  resolveIcebreakerCardPresentation,
  resolveIcebreakerVisualKind,
} from "./agentIcebreakers";

describe("resolveIcebreakerCardPresentation", () => {
  it("separa rótulo e exemplo dos templates padrão", () => {
    expect(
      resolveIcebreakerCardPresentation("me fale do produto {{productCode}}"),
    ).toEqual({
      title: "Consultar produto",
      subtitle: "10080001",
      example: "10080001",
    });
  });

  it("usa hint quando o template não tem exemplo", () => {
    expect(resolveIcebreakerCardPresentation("o que você pode fazer?")).toEqual({
      title: "Capacidades",
      subtitle: "Ferramentas, dados e limites do agente",
    });
  });

  it("resolve variante visual por template", () => {
    expect(resolveIcebreakerVisualKind("qual o estoque do produto {{productCode}}?")).toBe(
      "stock",
    );
    expect(resolveIcebreakerVisualKind("pesquise na web sobre {{searchQuery}}")).toBe("web");
  });
});
