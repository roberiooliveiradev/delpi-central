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
