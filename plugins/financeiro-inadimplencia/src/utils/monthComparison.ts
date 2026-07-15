import type { InadimplenciaMensalItem } from "../types/inadimplencia";

function monthKey(value: string | null | undefined): string | null {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})/.exec(value.trim());
  return match ? `${match[1]}-${match[2]}` : null;
}

export function formatYearMonthKey(referenceDate = new Date()): string {
  const month = String(referenceDate.getMonth() + 1).padStart(2, "0");
  return `${referenceDate.getFullYear()}-${month}`;
}

/**
 * Seleciona o mês corrente na série (ou o último disponível) e o mês imediatamente anterior.
 */
export function resolveMonthComparison(
  items: InadimplenciaMensalItem[],
  referenceDate = new Date(),
): {
  current: InadimplenciaMensalItem | null;
  previous: InadimplenciaMensalItem | null;
} {
  if (!items.length) {
    return { current: null, previous: null };
  }

  const targetKey = formatYearMonthKey(referenceDate);
  let currentIndex = items.findIndex((item) => monthKey(item.ano_mes || item.mes) === targetKey);
  if (currentIndex < 0) {
    currentIndex = items.length - 1;
  }

  return {
    current: items[currentIndex] ?? null,
    previous: currentIndex > 0 ? (items[currentIndex - 1] ?? null) : null,
  };
}

export type PontualidadeTrend = "melhor" | "pior" | "estavel" | "indisponivel";

export function comparePontualidadeQtd(
  current: number | null | undefined,
  previous: number | null | undefined,
): { deltaPp: number | null; trend: PontualidadeTrend } {
  if (
    current == null ||
    previous == null ||
    Number.isNaN(current) ||
    Number.isNaN(previous)
  ) {
    return { deltaPp: null, trend: "indisponivel" };
  }

  const deltaPp = current - previous;
  if (Math.abs(deltaPp) < 0.005) {
    return { deltaPp: 0, trend: "estavel" };
  }
  return {
    deltaPp,
    trend: deltaPp > 0 ? "melhor" : "pior",
  };
}
