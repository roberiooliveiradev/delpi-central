import { describe, expect, it } from "vitest";

import { splitWelcomeHeadline } from "./welcomeHeadline";

describe("splitWelcomeHeadline", () => {
  it("mantém título de onboarding em uma linha", () => {
    expect(
      splitWelcomeHeadline(
        "Olá! Posso ajudar com consultas operacionais, textos, documentos.",
      ),
    ).toEqual({
      lead: "Olá! Posso ajudar com consultas operacionais, textos, documentos.",
    });
  });

  it("separa cláusula final após «e» em títulos longos", () => {
    const parts = splitWelcomeHeadline(
      "Olá! Posso ajudar com consultas operacionais, textos, documentos e normas técnicas avançadas.",
    );

    expect(parts.lead).toContain("consultas operacionais");
    expect(parts.accent).toContain("normas");
  });

  it("mantém título curto em uma linha", () => {
    expect(splitWelcomeHeadline("Oi, Robério.")).toEqual({ lead: "Oi, Robério." });
  });
});
