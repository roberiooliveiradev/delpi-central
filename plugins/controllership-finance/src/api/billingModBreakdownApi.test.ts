/**
 * Contrato R09 — normalização produtor→Portal no boundary do MFE.
 * Fixture fiel ao formato real emitido pela api-delpi
 * (`explodedProduct`, `unit`, `anchorProduct`, `modItemState`,
 * sem `product`/`modUnit`/`productDescription`/`costProduct`).
 */
import { describe, expect, it, vi } from "vitest";

const httpGetMock = vi.fn();
vi.mock("./httpClient", () => ({
  cfApiUrl: (path: string) => path,
  httpGet: (...args: unknown[]) => httpGetMock(...args),
}));

import { getBillingModBreakdown } from "./billingModBreakdownApi";

/** Forma real emitida por GetBillingModBreakdownUseCase (doc 154). */
const PRODUCER_PAYLOAD = {
  report: "billing-mod-breakdown",
  period: "2026-09",
  branch: "all",
  anchors: [
    {
      product: "80014579",
      branch: "01",
      billedQty: 0.01,
      productDescription: null,
      modLines: [
        {
          level: "02",
          anchorProduct: "80014579",
          explodedProduct: "80014579",
          modItem: "MOD349",
          modDescription: "Mão de obra inspeção",
          unit: "HH",
          operation: "030",
          operationDescription: "INSPECIONAR",
          resource: "CT-70",
          stdTime: { value: 0.01, state: "shy_frozen_op" },
          sourceOp: "000123",
          propagatedQty: 0.01,
          hours: { value: 0.0001, state: "computed" },
          costUnit: {
            value: null,
            state: "source_missing",
            reason: "cost_rate_basis_unavailable",
          },
          costTotal: { value: null, state: "source_missing" },
          modItemState: "mapped",
        },
        {
          level: "04",
          anchorProduct: "80014579",
          explodedProduct: "COMP-77",
          unit: "HH",
          operation: "040",
          resource: "CT-19",
          propagatedQty: 0.02,
          hours: { value: null, state: "source_missing" },
          modItemState: "mapped",
        },
      ],
      sourceMissing: ["cost_rate_basis"],
      diagnostics: {
        productsWithoutRouteOperations: [],
        unmappedResourceMod: [],
      },
    },
  ],
  limitations: [],
  officiality: "operational_view",
  officialParity: "pending",
};

describe("getBillingModBreakdown — normalização de contrato", () => {
  it("mapeia explodedProduct→product e unit→modUnit, preservando nomes originais", async () => {
    httpGetMock.mockResolvedValueOnce({
      success: true,
      data: PRODUCER_PAYLOAD,
    });
    const payload = await getBillingModBreakdown("2026-09", "all");
    const line = payload.anchors[0].modLines[0];
    // campos normalizados consumidos pela UI
    expect(line.product).toBe("80014579");
    expect(line.modUnit).toBe("HH");
    // proveniência do produtor preservada
    expect(line.explodedProduct).toBe("80014579");
    expect(line.unit).toBe("HH");
    expect(line.anchorProduct).toBe("80014579");
    // componente distinto da âncora
    expect(payload.anchors[0].modLines[1].product).toBe("COMP-77");
    expect(payload.anchors[0].modLines[1].modUnit).toBe("HH");
  });

  it("não inventa campos ausentes — costProduct/description seguem undefined", async () => {
    httpGetMock.mockResolvedValueOnce({
      success: true,
      data: PRODUCER_PAYLOAD,
    });
    const payload = await getBillingModBreakdown("2026-09");
    const line = payload.anchors[0].modLines[0];
    expect(line.costProduct).toBeUndefined();
    expect(line.productDescription).toBeUndefined();
    // estados tipados intactos
    expect(line.costUnit?.state).toBe("source_missing");
    expect(line.hours?.state).toBe("computed");
  });
});
