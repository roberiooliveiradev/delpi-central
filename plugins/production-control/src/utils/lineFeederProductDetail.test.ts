import { describe, expect, it } from "vitest";

import type { LineFeederProductDetail } from "../types";
import {
  pointOfUseQty,
  sumKnownQuantities,
  summarizeLineFeederProductDetail,
  worstLineFeederStatus,
} from "./lineFeederProductDetail";

const DETAIL: LineFeederProductDetail = {
  branch: "01",
  cutoff: { at: "2026-09-22T14:00:00", date: "2026-09-22", time: "14:00" },
  product: {
    code: "50320064",
    description: "CHAPA",
    unit: "PC",
    pickup_location: "A-01",
  },
  work_centers: [
    {
      work_center: "CT-01",
      work_center_name: "BANCADA CT-01",
      required_qty: 10,
      to_deliver_qty: 0,
      status: "covered",
    },
    {
      work_center: "CT-02",
      work_center_name: "BANCADA CT-02",
      required_qty: 4,
      to_deliver_qty: 4,
      status: "to_pick",
    },
  ],
  stock: { available: true, warehouse: "01", quantity: 250 },
  transfers: { available: true, items: [] },
};

describe("lineFeederProductDetail", () => {
  it("escolhe a situação mais grave entre as bancadas", () => {
    expect(worstLineFeederStatus(["covered", "to_pick"])).toBe("to_pick");
    expect(worstLineFeederStatus(["to_pick", "at_risk"])).toBe("at_risk");
    expect(worstLineFeederStatus([])).toBeNull();
  });

  it("soma quantidades só quando todas foram medidas", () => {
    expect(sumKnownQuantities([10, 4])).toBe(14);
    expect(sumKnownQuantities([10, null])).toBeNull();
    expect(sumKnownQuantities([])).toBe(0);
  });

  it("estima o que já está na bancada pela diferença necessidade − a coletar", () => {
    expect(pointOfUseQty(14, 4)).toBe(10);
    expect(pointOfUseQty(10, null)).toBeNull();
  });

  it("agrega o recorte do detalhe para a visão geral", () => {
    const summary = summarizeLineFeederProductDetail(DETAIL);
    expect(summary.status).toBe("to_pick");
    expect(summary.requiredQty).toBe(14);
    expect(summary.toDeliverQty).toBe(4);
    expect(summary.pointOfUseQty).toBe(10);
    expect(summary.destinations).toBe("BANCADA CT-01, BANCADA CT-02");
  });
});
