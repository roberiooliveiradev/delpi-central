import { describe, expect, it } from "vitest";

import type { SafetyStockProjectionSummary } from "../types/safetyStock";
import { projectionSituationText } from "./projectionSituation";

const summary: SafetyStockProjectionSummary = {
  as_of_date: "2026-07-17",
  initial_balance: 29768,
  safety_stock: 100,
  eligible_purchase_quantity: 50000,
  eligible_commitment_quantity: 9765,
  final_projected_balance: 70003,
  final_balance_after_safety: 69903,
  minimum_projected_balance: 27193,
  first_shortage_date: null,
  projected_remaining_to_buy: 0,
  status: "sufficient",
  eligible_warehouses: ["01", "98", "99"],
  warnings: [],
};

describe("projectionSituationText", () => {
  it("resume a projeção sem ruptura", () => {
    expect(projectionSituationText(summary)).toBe(
      "Partindo de um saldo de 29.768,00, com 50.000,00 de entradas previstas e 9.765,00 de consumo comprometido, o saldo final projetado é 70.003,00. O menor saldo previsto no período é 27.193,00. Não há ruptura projetada no período.",
    );
  });

  it("informa a primeira ruptura quando prevista", () => {
    expect(
      projectionSituationText({
        ...summary,
        minimum_projected_balance: -50,
        first_shortage_date: "2026-07-20",
        status: "temporary_shortage",
      }),
    ).toContain(
      "O menor saldo previsto no período é -50,00. A primeira ruptura está prevista para 20/07/2026.",
    );
  });
});
