import type { CatalogLifecycle } from "./types";

/** Dias para considerar componente «Novo». */
export const CATALOG_NEW_WITHIN_DAYS = 30;

/** Dias para considerar componente «Atualizado» (se updatedAt ≠ addedAt). */
export const CATALOG_UPDATED_WITHIN_DAYS = 14;

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function isIsoDate(value: string): boolean {
  if (!ISO_DATE_RE.test(value)) return false;
  const t = Date.parse(`${value}T00:00:00.000Z`);
  return Number.isFinite(t);
}

export function resolveEffectiveUpdatedAt(addedAt: string, updatedAt?: string): string {
  return updatedAt && isIsoDate(updatedAt) ? updatedAt : addedAt;
}

function daysBetweenUtc(fromIso: string, toIso: string): number {
  const from = Date.parse(`${fromIso}T00:00:00.000Z`);
  const to = Date.parse(`${toIso}T00:00:00.000Z`);
  return Math.floor((to - from) / 86_400_000);
}

/**
 * Deriva lifecycle a partir das datas declarativas.
 * `today` injetável para testes determinísticos (YYYY-MM-DD).
 */
export function resolveLifecycle(
  addedAt: string,
  updatedAt: string | undefined,
  today: string,
): CatalogLifecycle {
  if (!isIsoDate(addedAt) || !isIsoDate(today)) return "stable";

  const effectiveUpdated = resolveEffectiveUpdatedAt(addedAt, updatedAt);
  const daysSinceAdded = daysBetweenUtc(addedAt, today);
  if (daysSinceAdded >= 0 && daysSinceAdded <= CATALOG_NEW_WITHIN_DAYS) {
    return "new";
  }

  if (
    effectiveUpdated !== addedAt &&
    daysBetweenUtc(effectiveUpdated, today) >= 0 &&
    daysBetweenUtc(effectiveUpdated, today) <= CATALOG_UPDATED_WITHIN_DAYS
  ) {
    return "updated";
  }

  return "stable";
}

/** Formata ISO date para exibição pt-BR (DD/MM/YYYY). */
export function formatCatalogDatePtBr(isoDate: string): string {
  if (!isIsoDate(isoDate)) return isoDate;
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

export function todayIsoUtc(now = new Date()): string {
  return now.toISOString().slice(0, 10);
}
