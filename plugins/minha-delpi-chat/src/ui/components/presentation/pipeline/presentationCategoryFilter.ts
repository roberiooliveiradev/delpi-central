/** Import direto do util (evita barrel MF/`remoteEntry` no vitest). */
import { buildDataTableSearchText } from "../../../../../../plugin-ui/src/utils/dataTableSearch";

import { formatChartColumnLabel } from "./chartAxisSelection";
import type { FieldLabels } from "./presentationFieldLabels";

export type CategoryFilterMode = "equality" | "contains";

export type CategoryFilterOption = {
  key: string;
  label: string;
  values: string[];
  mode: CategoryFilterMode;
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

/** Acima deste limiar o 2º controle vira texto «contém» (evita lista infinita). */
const EQUALITY_MAX_VALUES = 40;
const EQUALITY_MIN_VALUES = 2;

function scoreFilterKey(key: string): number {
  const lowered = key.toLowerCase();
  const index = FILTER_KEY_PRIORITY.findIndex((token) => lowered.includes(token));

  return index >= 0 ? FILTER_KEY_PRIORITY.length - index : 0;
}

export function buildCategoryFilterOptions(
  rows: Record<string, unknown>[] | undefined | null,
  candidateKeys?: string[],
  fieldLabels?: FieldLabels | null,
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

    if (values.length < 1) {
      continue;
    }

    const mode: CategoryFilterMode =
      values.length >= EQUALITY_MIN_VALUES && values.length <= EQUALITY_MAX_VALUES
        ? "equality"
        : "contains";

    options.push({
      key,
      label: formatChartColumnLabel(key, fieldLabels),
      values: mode === "equality" ? values : [],
      mode,
    });
  }

  return options.sort((left, right) => scoreFilterKey(right.key) - scoreFilterKey(left.key));
}

export function applyCategoryFilter(
  rows: Record<string, unknown>[] | undefined | null,
  filterKey: string | null,
  filterValue: string | null,
  filterMode: CategoryFilterMode | null = "equality",
): Record<string, unknown>[] {
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!filterKey || !filterValue) {
    return safeRows;
  }

  const needle = filterValue.trim();
  if (!needle) {
    return safeRows;
  }

  if (filterMode === "contains") {
    const lowered = needle.toLowerCase();

    return safeRows.filter((row) =>
      String(row[filterKey] ?? "")
        .trim()
        .toLowerCase()
        .includes(lowered),
    );
  }

  return safeRows.filter((row) => String(row[filterKey] ?? "").trim() === needle);
}

export function applyTableSearchFilter(
  rows: Record<string, unknown>[] | undefined | null,
  query: string | null | undefined,
  columnKeys: readonly string[],
): Record<string, unknown>[] {
  const safeRows = Array.isArray(rows) ? rows : [];
  const needle = String(query ?? "")
    .trim()
    .toLowerCase();

  if (!needle || !columnKeys.length) {
    return safeRows;
  }

  const searchColumns = columnKeys.map((key) => ({
    render: (row: Record<string, unknown>) => row[key],
  }));

  return safeRows.filter((row) =>
    buildDataTableSearchText(row, searchColumns).includes(needle),
  );
}

export type PresentationRowPipelineInput = {
  searchQuery?: string | null;
  filterKey?: string | null;
  filterValue?: string | null;
  filterMode?: CategoryFilterMode | null;
  columnKeys: readonly string[];
};

/** Busca global AND filtro de coluna (igualdade ou contém). */
export function applyPresentationRowPipeline(
  rows: Record<string, unknown>[] | undefined | null,
  input: PresentationRowPipelineInput,
): Record<string, unknown>[] {
  const afterSearch = applyTableSearchFilter(rows, input.searchQuery, input.columnKeys);

  return applyCategoryFilter(
    afterSearch,
    input.filterKey ?? null,
    input.filterValue ?? null,
    input.filterMode ?? "equality",
  );
}
