import type { DataQueryCompiledStep } from "../domain/dataQueryTypes";

export type PreviewSortState = {
  key: string;
  direction: "asc" | "desc";
};

/** Extrai a última ordenação Table.Sort do script compilado (fonte de verdade M). */
export function resolvePreviewSort(
  steps: DataQueryCompiledStep[] | null | undefined,
): PreviewSortState | null {
  if (!steps?.length) return null;
  for (let index = steps.length - 1; index >= 0; index -= 1) {
    const step = steps[index]!;
    if (step.operation !== "Table.Sort") continue;
    const match = step.formula.match(
      /\{\{\s*"([^"]+)"\s*,\s*Order\.(Ascending|Descending)\s*\}\}/,
    );
    if (!match) continue;
    return {
      key: match[1]!,
      direction: match[2] === "Descending" ? "desc" : "asc",
    };
  }
  return null;
}

/** Alterna direção ao reordenar a mesma coluna; caso contrário começa em asc. */
export function nextSortDirection(
  current: PreviewSortState | null,
  columnKey: string,
): "asc" | "desc" {
  if (current?.key === columnKey && current.direction === "asc") return "desc";
  return "asc";
}
