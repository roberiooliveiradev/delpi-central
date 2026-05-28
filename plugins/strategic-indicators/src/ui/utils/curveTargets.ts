import type { GoalPeriodicity, MonthlyTargetItem } from "../../data/types/indicatorGoals";
import { expectedMonthlyCurvePointCount } from "./goalValuePolicy";

const MONTH_LABELS = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
];

export function buildEmptyCurveTargets(
  periodicity: GoalPeriodicity | string,
): MonthlyTargetItem[] {
  const count = expectedMonthlyCurvePointCount(periodicity);
  return Array.from({ length: count }, (_, index) => ({
    month_number: index + 1,
    target_value: 0,
  }));
}

export function normalizeCurveTargets(
  input: MonthlyTargetItem[] | null | undefined,
  periodicity: GoalPeriodicity | string,
): MonthlyTargetItem[] {
  const base = buildEmptyCurveTargets(periodicity);
  if (!input?.length) return base;

  const byPoint = new Map<number, number>();
  input.forEach((item) => {
    byPoint.set(item.month_number, Number(item.target_value || 0));
  });

  return base.map((item) => ({
    month_number: item.month_number,
    target_value: byPoint.get(item.month_number) ?? 0,
  }));
}

export function getCurvePointLabels(
  periodicity: GoalPeriodicity | string,
): string[] {
  const count = expectedMonthlyCurvePointCount(periodicity);
  switch (periodicity) {
    case "quarterly":
      return Array.from({ length: count }, (_, index) => `${index + 1}º trim.`);
    case "weekly":
      return Array.from({ length: count }, (_, index) => `Sem ${index + 1}`);
    case "annual":
      return ["Ano"];
    case "monthly":
    default:
      return MONTH_LABELS.slice(0, count);
  }
}

export function getCurveSectionTitle(
  periodicity: GoalPeriodicity | string,
): string {
  switch (periodicity) {
    case "quarterly":
      return "Curva trimestral da meta";
    case "weekly":
      return "Curva semanal da meta";
    case "annual":
      return "Meta anual (curva)";
    case "monthly":
    default:
      return "Curva mensal da meta";
  }
}

export function getCurveHintText(periodicity: GoalPeriodicity | string): string {
  const count = expectedMonthlyCurvePointCount(periodicity);
  return `Preencha ${count} valor(es) conforme a periodicidade. O cálculo usa cada ponto da curva — não há valor consolidado.`;
}
