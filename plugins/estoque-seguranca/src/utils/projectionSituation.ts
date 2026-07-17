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

export function projectionSituationText(summary: SafetyStockProjectionSummary): string {
  const parts = projectionSituationParts(summary);
  const base =
    `Partindo de um saldo de ${parts.initialBalance}, ` +
    `com ${parts.purchaseQuantity} de entradas previstas ` +
    `e ${parts.commitmentQuantity} de consumo comprometido, ` +
    `o saldo final projetado é ${parts.finalBalance}. ` +
    `O menor saldo previsto no período é ${parts.minimumBalance}.`;

  if (parts.shortageDate) {
    return `${base} A primeira ruptura está prevista para ${parts.shortageDate}.`;
  }

  return `${base} Não há ruptura projetada no período.`;
}
