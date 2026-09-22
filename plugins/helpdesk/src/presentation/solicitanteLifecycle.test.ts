import { describe, expect, it } from "vitest";
import { solicitanteLifecycleCue, timelineHasSolution } from "./solicitanteLifecycle";

describe("timelineHasSolution", () => {
  it("detecta kind=solution e ignora followup", () => {
    expect(timelineHasSolution([{ kind: "followup" }, { kind: "solution" }])).toBe(true);
    expect(timelineHasSolution([{ kind: "followup" }])).toBe(false);
    expect(timelineHasSolution(undefined)).toBe(false);
  });
});

describe("solicitanteLifecycleCue", () => {
  it("capacidade nativa → ações no MFE", () => {
    const cue = solicitanteLifecycleCue({
      statusId: 5,
      hasSolution: true,
      canAcceptSolution: true,
      canRejectSolution: true,
    });
    expect(cue?.id).toBe("solved_native");
    expect(cue?.showNativeActions).toBe(true);
  });

  it("solucionado sem capability → CTA no helpdesk", () => {
    expect(solicitanteLifecycleCue({ statusId: 5, hasSolution: false })?.id).toBe("solved_needs_glpi");
    expect(solicitanteLifecycleCue({ statusId: 2, hasSolution: true })?.id).toBe("solved_needs_glpi");
  });

  it("fechado com pesquisa disponível", () => {
    const cue = solicitanteLifecycleCue({
      statusId: 6,
      hasSolution: true,
      canSubmitSatisfaction: true,
    });
    expect(cue?.id).toBe("closed_satisfaction");
    expect(cue?.showSatisfactionForm).toBe(true);
  });

  it("fechado já avaliado", () => {
    expect(
      solicitanteLifecycleCue({ statusId: 6, hasSolution: true, satisfaction: 4 })?.id,
    ).toBe("closed_done");
  });

  it("fechado sem capability → CTA", () => {
    expect(solicitanteLifecycleCue({ statusId: 6, hasSolution: true })?.id).toBe("closed");
  });

  it("aprovação 10 e negativo aberto sem solução", () => {
    expect(solicitanteLifecycleCue({ statusId: 10, hasSolution: false })?.id).toBe("approval_pending");
    expect(solicitanteLifecycleCue({ statusId: 1, hasSolution: false })).toBeNull();
  });
});
