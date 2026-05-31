import { describe, expect, it } from "vitest";

import { splitWelcomeHeadline } from "./welcomeHeadline";

describe("splitWelcomeHeadline", () => {
  it("separa cláusula final após «e» em títulos longos", () => {
    const parts = splitWelcomeHeadline(
      "Olá! Posso ajudar com consultas operacionais, textos, documentos e análises.",
    );

    expect(parts.lead).toContain("consultas operacionais");
    expect(parts.accent).toBe("análises.");
  });

  it("mantém título curto em uma linha", () => {
    expect(splitWelcomeHeadline("Oi, Robério.")).toEqual({ lead: "Oi, Robério." });
  });
});
