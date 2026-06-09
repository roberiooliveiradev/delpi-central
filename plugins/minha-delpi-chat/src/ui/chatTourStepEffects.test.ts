import { describe, expect, it } from "vitest";

import { resolveTourStepEffect, tourTargetSelector } from "./chatTourStepEffects";

describe("chatTourStepEffects", () => {
  it("resolve alvo padrão do composer para pergunta", () => {
    expect(
      tourTargetSelector({ id: "ask", title: "Digite uma pergunta" }),
    ).toBe('[data-tour="composer-input"]');
  });

  it("prioriza target explícito do passo", () => {
    expect(
      tourTargetSelector({
        id: "ask",
        title: "X",
        target: "home-highlights",
      }),
    ).toBe('[data-tour="home-highlights"]');
  });

  it("resolve alvo da saudação na home", () => {
    expect(
      tourTargetSelector({ id: "welcome", title: "Bem-vindo" }),
    ).toBe('[data-tour="home-greeting"]');
  });

  it("inclui demoQuery padrão para ask", () => {
    const effect = resolveTourStepEffect({ id: "ask", title: "Digite" });

    expect(effect.demoQuery).toContain("estoque");
    expect(effect.openPlusMenu).toBe(false);
  });

  it("abre menu + no passo de agente", () => {
    const effect = resolveTourStepEffect({ id: "agent", title: "Agente" });

    expect(effect.openPlusMenu).toBe(true);
    expect(effect.target).toBe("composer-plus-menu-agents");
  });
});
