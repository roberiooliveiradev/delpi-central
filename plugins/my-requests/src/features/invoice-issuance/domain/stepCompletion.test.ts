import { describe, expect, it } from "vitest";

import {
  buildStepCompletionMap,
  canOpenStep,
  computeMaxUnlockedIndex,
  computeStepStates,
  isStepComplete,
  progressPercent,
  resolveNextStepAfterEdit,
  type WizardDraft,
} from "./stepCompletion";
import type { IssuanceItem, Party } from "./types";

const party: Party = {
  party_type: "customer",
  party_code: "001",
  party_store: "01",
  party_name: "ACME",
};

const item: IssuanceItem = {
  product_code: "P1",
  product_description: "Prod",
  quantity: 1,
  unit_price: 10,
  stock_write_off: true,
};

function draft(partial: Partial<WizardDraft> = {}): WizardDraft {
  return {
    party: null,
    invoiceType: "sale",
    invoiceTypeOther: "",
    items: [],
    freightMode: "cif",
    weightKg: "1",
    volumeCount: "1",
    ...partial,
  };
}

describe("stepCompletion", () => {
  it("marca destinatário completo só com party_code e party_store", () => {
    expect(isStepComplete("recipient", draft())).toBe(false);
    expect(isStepComplete("recipient", draft({ party }))).toBe(true);
  });

  it("desbloqueia etapas em sequência e bloqueia futuras", () => {
    const completion = buildStepCompletionMap(
      draft({ party, items: [item], invoiceType: "sale" }),
    );
    expect(completion.recipient).toBe(true);
    expect(completion.invoiceType).toBe(true);
    expect(completion.items).toBe(true);
    expect(computeMaxUnlockedIndex(completion)).toBe(3);
    expect(canOpenStep("freight", completion)).toBe(true);
    expect(canOpenStep("extras", completion)).toBe(false);
  });

  it("recalcula progresso quando etapa anterior invalida", () => {
    const full = buildStepCompletionMap(
      draft({
        party,
        items: [item],
        invoiceType: "sale",
        freightMode: "cif",
        weightKg: "2",
        volumeCount: "2",
      }),
    );
    expect(progressPercent(full)).toBe(100);

    const brokenType = buildStepCompletionMap(
      draft({
        party,
        items: [item],
        invoiceType: "other",
        invoiceTypeOther: "",
        freightMode: "cif",
        weightKg: "2",
        volumeCount: "2",
      }),
    );
    expect(brokenType.invoiceType).toBe(false);
    expect(progressPercent(brokenType)).toBeLessThan(100);
    expect(canOpenStep("items", brokenType)).toBe(false);
  });

  it("computeStepStates diferencia current, complete e locked", () => {
    const completion = buildStepCompletionMap(draft({ party }));
    const states = computeStepStates({
      currentStepId: "invoiceType",
      completion,
    });
    expect(states.find((s) => s.id === "recipient")?.state).toBe("complete");
    expect(states.find((s) => s.id === "invoiceType")?.state).toBe("current");
    expect(states.find((s) => s.id === "items")?.state).toBe("locked");
  });

  it("returnToReview volta à conferência quando etapa ainda completa", () => {
    const completion = buildStepCompletionMap(
      draft({
        party,
        items: [item],
        invoiceType: "sale",
        freightMode: "cif",
        weightKg: "2",
        volumeCount: "2",
      }),
    );
    expect(
      resolveNextStepAfterEdit({
        editedStepId: "recipient",
        completion,
        returnToReview: true,
      }),
    ).toBe("review");
  });
});
