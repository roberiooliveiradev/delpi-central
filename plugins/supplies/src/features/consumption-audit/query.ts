import type { ConsumptionAuditBranch, ConsumptionAuditResponse } from "./types";
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
