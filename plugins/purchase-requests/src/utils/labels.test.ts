import { describe, expect, it } from "vitest";

import {
  formatBuyerLabel,
  formatOrdersSummary,
  labelApprovalStatus,
  labelOverallStage,
} from "./labels";

describe("labels", () => {
  it("translates operational stages without calling residual closed cancelled", () => {
    expect(labelOverallStage("residual_closed")).toBe("Encerrada por resíduo");
    expect(labelOverallStage("awaiting_order")).toBe("Aguardando pedido");
  });

  it("does not map unknown approval to waiting approval", () => {
    expect(labelApprovalStatus("unknown")).toBe("Não identificada");
  });

  it("summarizes multiple purchase orders compactly", () => {
    expect(
      formatOrdersSummary([
        { order_number: "041446" },
        { order_number: "041447" },
      ]),
    ).toBe("2 pedidos");
  });

  it("does not use order_user as buyer fallback", () => {
    expect(formatBuyerLabel(null)).toBe("Comprador não informado");
    expect(formatBuyerLabel({ name: null, code: null })).toBe("Comprador não informado");
  });
});
