import type { OverviewKpiStrategic, OverviewUnitValueMap } from "../../api/overview";

export const STRATEGIC_UNIT_ORDER = ["consolidated", "01", "02"] as const;

export type StrategicUnitKey = (typeof STRATEGIC_UNIT_ORDER)[number];

const UNIT_LABEL: Record<StrategicUnitKey, string> = {
  consolidated: "Consolidado",
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export type StrategicUnitRow = {
  key: StrategicUnitKey;
  label: string;
  realizedLabel: string;
  goalLabel: string;
  goalCaption: string;
};

export function formatDepartmentScore(score: number | null | undefined): string | null {
  if (typeof score !== "number" || !Number.isFinite(score)) return null;
  return score.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function periodGoalCaption(goalPeriodKind: string | null | undefined): string {
  if (goalPeriodKind === "partial") return "Meta parcial";
  if (goalPeriodKind === "accumulated") return "Meta acumulada";
  return "Meta";
}

export function formatStrategicNumber(
  value: number | null | undefined,
  strategic: Pick<OverviewKpiStrategic, "valuePrefix" | "valueSuffix" | "valueDecimals">,
): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  const decimals = strategic.valueDecimals ?? 1;
  const formatted = value.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  const prefix = strategic.valuePrefix ? `${strategic.valuePrefix} ` : "";
  const suffix = strategic.valueSuffix ?? "";
  return `${prefix}${formatted}${suffix}`.trim();
}

function hasKey(map: OverviewUnitValueMap | undefined, key: StrategicUnitKey): boolean {
  return Boolean(map && Object.prototype.hasOwnProperty.call(map, key));
}

export function buildStrategicUnitRows(
  strategic: OverviewKpiStrategic | null | undefined,
): StrategicUnitRow[] {
  if (!strategic?.indicatorId) return [];
  const caption = periodGoalCaption(strategic.goalPeriodKind);
  const rows: StrategicUnitRow[] = [];
  for (const key of STRATEGIC_UNIT_ORDER) {
    const hasRealized = hasKey(strategic.realized, key);
    const hasGoal = hasKey(strategic.goals, key);
    if (!hasRealized && !hasGoal) continue;
    const goalValue = hasGoal ? strategic.goals[key] : undefined;
    rows.push({
      key,
      label: UNIT_LABEL[key],
      realizedLabel: hasRealized
        ? formatStrategicNumber(strategic.realized[key], strategic)
        : "—",
      goalLabel:
        hasGoal && (goalValue == null || !Number.isFinite(goalValue))
          ? "Meta não cadastrada"
          : hasGoal
            ? formatStrategicNumber(goalValue, strategic)
            : "Meta não cadastrada",
      goalCaption: caption,
    });
  }
  return rows;
}
