import type { ConsumptionAnalysisStatus } from "../types/consumptionAnalysis";
import type {
  PurchaseCoverageStatus,
  SafetyStockStatus,
  StockProjectionDateStatus,
  StockProjectionStatus,
} from "../types/safetyStock";
import type { StatusBadgeVariant } from "@delpi/plugin-ui/index";

export const SAFETY_STOCK_STATUS_LABELS: Record<SafetyStockStatus, string> = {
  without_safety_stock: "Sem estoque de segurança",
  below_safety_stock: "Abaixo do estoque de segurança",
  at_safety_stock: "No estoque de segurança",
  above_safety_stock: "Acima do estoque de segurança",
};

export const SAFETY_STOCK_STATUS_VARIANTS: Record<SafetyStockStatus, StatusBadgeVariant> = {
  without_safety_stock: "warning",
  below_safety_stock: "danger",
  at_safety_stock: "info",
  above_safety_stock: "success",
};

export function safetyStockStatusLabel(status: SafetyStockStatus): string {
  return SAFETY_STOCK_STATUS_LABELS[status] ?? status;
}

export function safetyStockStatusVariant(status: SafetyStockStatus): StatusBadgeVariant {
  return SAFETY_STOCK_STATUS_VARIANTS[status] ?? "neutral";
}

export const BRANCH_LABELS: Record<string, string> = {
  "01": "Filial 01 (SC)",
  "02": "Filial 02 (ES)",
};

export function branchLabel(branch: string): string {
  return BRANCH_LABELS[branch] ?? `Filial ${branch}`;
}

export const UNIT_DISPLAY_SUFFIX: Record<string, string> = {
  PC: "unidades",
  MT: "metros",
  KG: "quilos",
  UN: "unidades",
};

export function unitSuffix(unit: string): string {
  return UNIT_DISPLAY_SUFFIX[unit] ?? "unidades";
}

export const PURCHASE_COVERAGE_LABELS: Record<PurchaseCoverageStatus, string> = {
  sufficient: "Pedido suficiente",
  partial: "Pedido parcial",
  none: "Sem pedido em aberto",
};

export const PURCHASE_COVERAGE_VARIANTS: Record<
  PurchaseCoverageStatus,
  StatusBadgeVariant
> = {
  sufficient: "success",
  partial: "warning",
  none: "danger",
};

export function purchaseCoverageLabel(status: PurchaseCoverageStatus): string {
  return PURCHASE_COVERAGE_LABELS[status] ?? status;
}

export function purchaseCoverageVariant(status: PurchaseCoverageStatus): StatusBadgeVariant {
  return PURCHASE_COVERAGE_VARIANTS[status] ?? "neutral";
}

export function formatIsoDatePtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return value;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export const STOCK_PROJECTION_LABELS: Record<StockProjectionStatus, string> = {
  sufficient: "Cobertura projetada suficiente",
  temporary_shortage: "Falta temporária projetada",
  projected_deficit: "Déficit projetado",
};

export const STOCK_PROJECTION_VARIANTS: Record<
  StockProjectionStatus,
  StatusBadgeVariant
> = {
  sufficient: "success",
  temporary_shortage: "warning",
  projected_deficit: "danger",
};

export function stockProjectionLabel(status: StockProjectionStatus): string {
  return STOCK_PROJECTION_LABELS[status] ?? status;
}

export function stockProjectionVariant(status: StockProjectionStatus): StatusBadgeVariant {
  return STOCK_PROJECTION_VARIANTS[status] ?? "neutral";
}

export const DATE_STATUS_LABELS: Record<StockProjectionDateStatus, string> = {
  today: "Hoje",
  scheduled: "Previsto",
  overdue: "Atrasado",
  unscheduled: "Sem data",
};

export function dateStatusLabel(status: StockProjectionDateStatus): string {
  return DATE_STATUS_LABELS[status] ?? status;
}

export const ANALYSIS_STATUS_LABELS: Record<ConsumptionAnalysisStatus, string> = {
  below_suggested: "Abaixo do sugerido",
  above_suggested: "Acima do sugerido",
  adequate: "Adequado",
  inconsistent_data: "Dados inconsistentes",
};

export const ANALYSIS_STATUS_VARIANTS: Record<
  ConsumptionAnalysisStatus,
  StatusBadgeVariant
> = {
  below_suggested: "danger",
  above_suggested: "warning",
  adequate: "success",
  inconsistent_data: "neutral",
};

export function analysisStatusLabel(status: ConsumptionAnalysisStatus): string {
  return ANALYSIS_STATUS_LABELS[status] ?? status;
}

export function analysisStatusVariant(
  status: ConsumptionAnalysisStatus,
): StatusBadgeVariant {
  return ANALYSIS_STATUS_VARIANTS[status] ?? "neutral";
}

export const ANALYSIS_STATUS_HEADER_HINT =
  "Compara o ESTSEG cadastrado com o valor sugerido: " +
  "Abaixo do sugerido = ESTSEG menor que o necessário para cobrir o lead time; " +
  "Acima do sugerido = ESTSEG maior que o necessário; " +
  "Adequado = próximo do sugerido (até 5% de diferença); " +
  "Dados inconsistentes = consumo ou lead time insuficientes para calcular.";

export const ANALYSIS_QUALITY_WARNING_LABELS: Record<string, string> = {
  period_consumption_not_positive: "O consumo do período não é positivo",
  lead_time_missing_or_zero: "O lead time (BZ_PE) está zerado ou ausente",
  average_consumption_not_positive: "O consumo diário calculado não é positivo",
};

export function analysisQualityWarningLabel(code: string): string {
  return ANALYSIS_QUALITY_WARNING_LABELS[code] ?? code;
}
