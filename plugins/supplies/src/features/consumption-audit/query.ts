import type {
  ConsumptionAuditBranch,
  ConsumptionAuditDateType,
  ConsumptionAuditResponse,
} from "./types";
import { PRODUCTION_ORDER_RE } from "./api";

/** Estado da consulta na URL — F5 e compartilhamento restauram o mesmo alvo. */
export type ConsumptionAuditTarget = {
  unit: ConsumptionAuditBranch;
  productionOrder: string;
};

const VALID_UNITS = new Set<ConsumptionAuditBranch>(["01", "02"]);

export function normalizeUnit(raw: string | null | undefined): ConsumptionAuditBranch | null {
  const unit = String(raw ?? "").trim();
  return (VALID_UNITS as Set<string>).has(unit)
    ? (unit as ConsumptionAuditBranch)
    : null;
}

export function normalizeProductionOrder(raw: string | null | undefined): string {
  return String(raw ?? "").trim().toUpperCase();
}

export function isValidProductionOrder(op: string): boolean {
  return PRODUCTION_ORDER_RE.test(op);
}

export function parseTargetFromSearch(search: string): ConsumptionAuditTarget | null {
  try {
    const params = new URLSearchParams(search || "");
    const unit = normalizeUnit(params.get("unit"));
    const productionOrder = normalizeProductionOrder(params.get("op"));
    if (!unit || !isValidProductionOrder(productionOrder)) return null;
    return { unit, productionOrder };
  } catch {
    return null;
  }
}

export function buildTargetSearch(target: ConsumptionAuditTarget): string {
  const params = new URLSearchParams({
    unit: target.unit,
    op: target.productionOrder,
  });
  return `?${params.toString()}`;
}

export function sameTarget(
  a: ConsumptionAuditTarget | null,
  b: ConsumptionAuditTarget | null,
): boolean {
  if (!a || !b) return a === b;
  return a.unit === b.unit && a.productionOrder === b.productionOrder;
}

// ——— F3 · estado dos filtros avançados na URL ———

const DATE_TYPES = new Set<ConsumptionAuditDateType>([
  "emission",
  "finished",
  "appointment",
]);

export type ConsumptionAuditFilterState = {
  dateType: ConsumptionAuditDateType;
  periodStart: string;
  periodEnd: string;
  product: string;
  status: string;
  workCenter: string;
  operation: string;
};

export const EMPTY_FILTERS: ConsumptionAuditFilterState = {
  dateType: "emission",
  periodStart: "",
  periodEnd: "",
  product: "",
  status: "",
  workCenter: "",
  operation: "",
};

function normalizeDateType(raw: string | null): ConsumptionAuditDateType {
  const value = String(raw ?? "").trim();
  return (DATE_TYPES as Set<string>).has(value)
    ? (value as ConsumptionAuditDateType)
    : "emission";
}

function normalizeDateParam(raw: string | null): string {
  const value = String(raw ?? "").trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return "";
  // Rejeita datas inexistentes (ex.: 2026-13-99) — mesma regra do backend.
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? "" : value;
}

export function parseFiltersFromSearch(search: string): {
  unit: ConsumptionAuditBranch | null;
  filters: ConsumptionAuditFilterState;
} {
  try {
    const params = new URLSearchParams(search || "");
    return {
      unit: normalizeUnit(params.get("unit")),
      filters: {
        dateType: normalizeDateType(params.get("date_type")),
        periodStart: normalizeDateParam(params.get("period_start")),
        periodEnd: normalizeDateParam(params.get("period_end")),
        product: String(params.get("product") ?? "").trim(),
        status: String(params.get("status") ?? "").trim().toUpperCase(),
        workCenter: String(params.get("work_center") ?? "").trim().toUpperCase(),
        operation: String(params.get("operation") ?? "").trim(),
      },
    };
  } catch {
    return { unit: null, filters: EMPTY_FILTERS };
  }
}

export function buildSearchQuery(
  unit: ConsumptionAuditBranch,
  filters: ConsumptionAuditFilterState,
  search?: string,
): string {
  const params = new URLSearchParams({ unit });
  const fragment = normalizeProductionOrder(search ?? "");
  if (fragment) params.set("search", fragment);
  if (filters.dateType !== "emission") params.set("date_type", filters.dateType);
  if (filters.periodStart) params.set("period_start", filters.periodStart);
  if (filters.periodEnd) params.set("period_end", filters.periodEnd);
  if (filters.product) params.set("product", filters.product);
  if (filters.status) params.set("status", filters.status);
  if (filters.workCenter) params.set("work_center", filters.workCenter);
  if (filters.operation) params.set("operation", filters.operation);
  return `?${params.toString()}`;
}

export function filtersAreEmpty(filters: ConsumptionAuditFilterState): boolean {
  return (
    filters.dateType === "emission" &&
    !filters.periodStart &&
    !filters.periodEnd &&
    !filters.product &&
    !filters.status &&
    !filters.workCenter &&
    !filters.operation
  );
}

// ——— Formatação PT-BR ———

export function formatQuantity(
  value: number | null | undefined,
  digits = 2,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  });
}

export function formatDatePtBr(raw: string | null | undefined): string {
  const value = String(raw ?? "").trim();
  if (!value) return "—";
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (iso) return `${iso[3]}/${iso[2]}/${iso[1]}`;
  const ymd = /^(\d{4})(\d{2})(\d{2})$/.exec(value);
  if (ymd) return `${ymd[3]}/${ymd[2]}/${ymd[1]}`;
  return value;
}

export function formatDateTimePtBr(raw: string | null | undefined): string {
  const value = String(raw ?? "").trim();
  if (!value) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/.exec(value);
  if (match) return `${match[3]}/${match[2]}/${match[1]} ${match[4]}:${match[5]}`;
  return formatDatePtBr(value);
}

// ——— Derivações de exibição (sem recálculo de regra) ———

/** Soma das evidências elegíveis por unidade de medida — comparável só dentro da mesma UM. */
export function eligibleConsumptionByUnit(
  response: ConsumptionAuditResponse,
): Array<{ unit: string; quantity: number }> {
  const totals = new Map<string, number>();
  for (const operation of response.operations) {
    for (const component of operation.components) {
      const qty = component.movements.eligible_consumption_quantity;
      if (qty === null || qty === undefined) continue;
      const unit = component.unit_of_measure || "?";
      totals.set(unit, (totals.get(unit) ?? 0) + qty);
    }
  }
  return [...totals.entries()]
    .map(([unit, quantity]) => ({ unit, quantity }))
    .sort((a, b) => a.unit.localeCompare(b.unit));
}
