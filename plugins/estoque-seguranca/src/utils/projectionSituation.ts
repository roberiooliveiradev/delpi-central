import type { SafetyStockProjectionSummary } from "../types/safetyStock";
import { formatNumberPtBr } from "./formatters";
import { formatIsoDatePtBr } from "./safetyStockStatus";

export type ProjectionSituationParts = {
  initialBalance: string;
  purchaseQuantity: string;
  commitmentQuantity: string;
  finalBalance: string;
  minimumBalance: string;
  shortageDate: string | null;
};

export function projectionSituationParts(
  summary: SafetyStockProjectionSummary,
): ProjectionSituationParts {
  return {
    initialBalance: formatNumberPtBr(summary.initial_balance),
    purchaseQuantity: formatNumberPtBr(summary.eligible_purchase_quantity),
    commitmentQuantity: formatNumberPtBr(summary.eligible_commitment_quantity),
    finalBalance: formatNumberPtBr(summary.final_projected_balance),
    minimumBalance: formatNumberPtBr(summary.minimum_projected_balance),
    shortageDate: summary.first_shortage_date
      ? formatIsoDatePtBr(summary.first_shortage_date)
      : null,
  };
}
