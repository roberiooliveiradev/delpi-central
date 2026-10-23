import { describe, expect, it } from "vitest";

import {
  resolvePresentationSyncReloadDecision,
  shouldRecoverAmbiguousSyncEvent,
} from "./presentationSyncReloadDecision";

const decide = (params: {
  eventRevision: number | null;
  trackedRevision: number;
  hasPendingOwnWrite: boolean;
}) => resolvePresentationSyncReloadDecision(params);

describe("resolvePresentationSyncReloadDecision", () => {
  it("A1 ack incorporado: rev <= tracked → skip_incorporated", () => {
    expect(
      decide({ eventRevision: 5, trackedRevision: 5, hasPendingOwnWrite: false }),
    ).toBe("skip_incorporated");
  });

  it("evento atrasado/duplicado (rev < tracked) → skip_incorporated", () => {
    expect(
      decide({ eventRevision: 3, trackedRevision: 7, hasPendingOwnWrite: false }),
    ).toBe("skip_incorporated");
  });

  it("WS antes do ACK: rev == tracked+1 com escrita em voo → skip_ambiguous_pending", () => {
    expect(
      decide({ eventRevision: 6, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe("skip_ambiguous_pending");
  });

  it("rev == tracked+1 sem escrita em voo → estrangeiro, recarrega", () => {
    expect(
      decide({ eventRevision: 6, trackedRevision: 5, hasPendingOwnWrite: false }),
    ).toBe("reload");
  });

  it("A5 — revisão adiante mesmo com escrita em voo → recarrega (nunca suprime)", () => {
    expect(
      decide({ eventRevision: 7, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe("reload");
    expect(
      decide({ eventRevision: 8, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe("reload");
  });

  it("evento sem revisão (payload antigo/reconexão) → recarrega", () => {
    expect(
      decide({ eventRevision: null, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe("reload");
  });

  it("revisão não-finita → recarrega", () => {
    expect(
      decide({ eventRevision: Number.NaN, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe("reload");
  });

  it("estado inicial (tracked 0) com rev 1 e pendente → ambíguo", () => {
    expect(
      decide({ eventRevision: 1, trackedRevision: 0, hasPendingOwnWrite: true }),
    ).toBe("skip_ambiguous_pending");
  });
});

describe("shouldRecoverAmbiguousSyncEvent — reconciliação diferida no settle", () => {
  it("A1 — ACK próprio cobriu a revisão ambígua → não recupera", () => {
    expect(
      shouldRecoverAmbiguousSyncEvent({ ambiguousRevision: 6, trackedRevision: 6 }),
    ).toBe(false);
  });

  it("A2/A3/A4 — rejeição/timeout/cancelamento sem cobertura → recupera", () => {
    expect(
      shouldRecoverAmbiguousSyncEvent({ ambiguousRevision: 6, trackedRevision: 5 }),
    ).toBe(true);
  });

  it("sem evento ambíguo registrado → não recupera", () => {
    expect(
      shouldRecoverAmbiguousSyncEvent({ ambiguousRevision: null, trackedRevision: 5 }),
    ).toBe(false);
  });

  it("A6 — reload do 409 já cobriu (tracked avançou) → não recupera", () => {
    expect(
      shouldRecoverAmbiguousSyncEvent({ ambiguousRevision: 6, trackedRevision: 9 }),
    ).toBe(false);
  });
});
