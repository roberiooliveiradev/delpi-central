import { describe, expect, it } from "vitest";

import {
  buildStepCompletionMap,
  canOpenStep,
  computeMaxUnlockedIndex,
  computeSequentialCompletedCount,
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
  tax_id: null,
  blocked: false,
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

  it("defaults sem destinatário não contam progresso nem checkmarks futuros", () => {
    const empty = buildStepCompletionMap(draft());
    expect(empty.recipient).toBe(false);
    expect(empty.invoiceType).toBe(true);
    expect(empty.freight).toBe(true);
    expect(empty.extras).toBe(true);
    expect(computeSequentialCompletedCount(empty)).toBe(0);
    expect(progressPercent(empty)).toBe(0);
    expect(computeMaxUnlockedIndex(empty)).toBe(0);

    const states = computeStepStates({
      currentStepId: "recipient",
      completion: empty,
    });
    expect(states.find((s) => s.id === "recipient")?.state).toBe("current");
    expect(states.find((s) => s.id === "invoiceType")?.state).toBe("locked");
    expect(states.find((s) => s.id === "freight")?.state).toBe("locked");
    expect(states.find((s) => s.id === "extras")?.state).toBe("locked");
    expect(states.every((s) => s.state !== "complete")).toBe(true);
  });

  it("desbloqueia etapas em sequência e bloqueia futuras", () => {
    const withRecipient = buildStepCompletionMap(draft({ party }));
    expect(withRecipient.recipient).toBe(true);
    expect(withRecipient.invoiceType).toBe(true);
    expect(withRecipient.items).toBe(false);
    expect(computeSequentialCompletedCount(withRecipient)).toBe(2);
    expect(progressPercent(withRecipient)).toBe(33);
    expect(computeMaxUnlockedIndex(withRecipient)).toBe(2);
    expect(canOpenStep("items", withRecipient)).toBe(true);
    expect(canOpenStep("freight", withRecipient)).toBe(false);

    const withItems = buildStepCompletionMap(
      draft({
        party,
        items: [item],
        invoiceType: "sale",
        weightKg: "0",
        volumeCount: "0",
      }),
    );
    expect(withItems.items).toBe(true);
    expect(withItems.freight).toBe(true);
    expect(withItems.extras).toBe(false);
    expect(computeMaxUnlockedIndex(withItems)).toBe(4);
    expect(canOpenStep("freight", withItems)).toBe(true);
    expect(canOpenStep("extras", withItems)).toBe(true);
    expect(canOpenStep("review", withItems)).toBe(false);
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
    expect(computeSequentialCompletedCount(brokenType)).toBe(1);
    expect(progressPercent(brokenType)).toBe(17);
    expect(canOpenStep("items", brokenType)).toBe(false);
  });

  it("computeStepStates diferencia current, complete e locked", () => {
    const completion = buildStepCompletionMap(
      draft({ party, invoiceType: "other", invoiceTypeOther: "" }),
    );
    expect(completion.recipient).toBe(true);
    expect(completion.invoiceType).toBe(false);
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
