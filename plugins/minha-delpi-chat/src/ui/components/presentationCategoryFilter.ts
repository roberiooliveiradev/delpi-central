import { formatChartColumnLabel } from "./chartAxisSelection";

export type CategoryFilterOption = {
  key: string;
  label: string;
  values: string[];
};

const FILTER_KEY_PRIORITY = [
  "filial",
  "centro",
  "operador",
  "nome_operador",
  "produto",
  "op",
  "turno",
  "status",
];

const MAX_FILTER_VALUES = 40;
const MIN_FILTER_VALUES = 2;

function scoreFilterKey(key: string): number {
  const lowered = key.toLowerCase();
  const index = FILTER_KEY_PRIORITY.findIndex((token) => lowered.includes(token));

  return index >= 0 ? FILTER_KEY_PRIORITY.length - index : 0;
}

export function buildCategoryFilterOptions(
  rows: Record<string, unknown>[] | undefined | null,
  candidateKeys?: string[],
): CategoryFilterOption[] {
  if (!Array.isArray(rows) || !rows.length) {
    return [];
  }

  const sample = rows[0] ?? {};
  const keys =
    candidateKeys?.length
      ? candidateKeys
      : Object.keys(sample).filter((key) => {
          const value = sample[key];

          return typeof value === "string" || (value != null && !Number.isFinite(Number(value)));
        });

  const options: CategoryFilterOption[] = [];

  for (const key of keys) {
    const values = [
      ...new Set(
        rows
          .map((row) => String(row[key] ?? "").trim())
          .filter((value) => value.length > 0),
      ),
    ].sort((left, right) => left.localeCompare(right, "pt-BR"));

    if (values.length < MIN_FILTER_VALUES || values.length > MAX_FILTER_VALUES) {
      continue;
    }

    options.push({
      key,
      label: formatChartColumnLabel(key),
      values,
    });
  }

  return options.sort((left, right) => scoreFilterKey(right.key) - scoreFilterKey(left.key));
}

export function applyCategoryFilter(
  rows: Record<string, unknown>[] | undefined | null,
  filterKey: string | null,
  filterValue: string | null,
): Record<string, unknown>[] {
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!filterKey || !filterValue) {
    return safeRows;
  }

  return safeRows.filter((row) => String(row[filterKey] ?? "").trim() === filterValue);
}
