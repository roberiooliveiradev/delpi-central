import { describe, expect, it } from "vitest";

import { shouldSkipPresentationUpdatedReload } from "./presentationSyncReloadDecision";

const skip = (params: {
  eventRevision: number | null;
  trackedRevision: number;
  hasPendingOwnWrite: boolean;
}) => shouldSkipPresentationUpdatedReload(params);

describe("shouldSkipPresentationUpdatedReload", () => {
  it("suprime evento do próprio ACK já incorporado (rev <= tracked)", () => {
    expect(
      skip({ eventRevision: 5, trackedRevision: 5, hasPendingOwnWrite: false }),
    ).toBe(true);
  });

  it("suprime evento atrasado/duplicado (rev < tracked)", () => {
    expect(
      skip({ eventRevision: 3, trackedRevision: 7, hasPendingOwnWrite: false }),
    ).toBe(true);
  });

  it("WS antes do ACK: rev == tracked+1 com escrita em voo → suprime", () => {
    expect(
      skip({ eventRevision: 6, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe(true);
  });

  it("WS antes do ACK sem escrita em voo → estrangeiro, recarrega", () => {
    expect(
      skip({ eventRevision: 6, trackedRevision: 5, hasPendingOwnWrite: false }),
    ).toBe(false);
  });

  it("revisão estrangeira adiante mesmo com escrita em voo → recarrega", () => {
    // estrangeiro tomou tracked+2 — pendente próprio vira 409 server-wins,
    // mas o reload acontece agora, sem esperar o conflito.
    expect(
      skip({ eventRevision: 7, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe(false);
  });

  it("evento sem revisão (payload antigo/reconexão) → recarrega", () => {
    expect(
      skip({ eventRevision: null, trackedRevision: 5, hasPendingOwnWrite: true }),
    ).toBe(false);
  });

  it("revisão não-finita → recarrega", () => {
    expect(
      skip({
        eventRevision: Number.NaN,
        trackedRevision: 5,
        hasPendingOwnWrite: true,
      }),
    ).toBe(false);
  });

  it("estado inicial (tracked 0) com evento rev 1 e pendente → suprime", () => {
    // primeira escrita do editor: WS pode chegar antes do ACK.
    expect(
      skip({ eventRevision: 1, trackedRevision: 0, hasPendingOwnWrite: true }),
    ).toBe(true);
  });
});
