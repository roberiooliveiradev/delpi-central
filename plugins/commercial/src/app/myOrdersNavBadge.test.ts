import { describe, expect, it } from "vitest";

import { resolveReadyToInvoiceBadgeCount } from "./myOrdersNavBadge";

describe("resolveReadyToInvoiceBadgeCount", () => {
  it("lê lineCount de ready_to_invoice", () => {
    expect(
      resolveReadyToInvoiceBadgeCount({
        stages: [
          { id: "upcoming", lineCount: 3 },
          { id: "ready_to_invoice", lineCount: 5 },
        ],
      }),
    ).toBe(5);
  });

  it("retorna 0 quando etapa ausente ou inválida", () => {
    expect(resolveReadyToInvoiceBadgeCount(null)).toBe(0);
    expect(resolveReadyToInvoiceBadgeCount({ stages: [] })).toBe(0);
    expect(
      resolveReadyToInvoiceBadgeCount({
        stages: [{ id: "ready_to_invoice", lineCount: -1 }],
      }),
    ).toBe(0);
  });
});
