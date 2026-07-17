import type { DataQueryCompiledStep } from "../domain/dataQueryTypes";

export type PreviewSortState = {
  key: string;
  direction: "asc" | "desc";
};

/**
 * Extrai a última ordenação Table.Sort do script compilado (fonte de verdade M).
 * Quando `selectedStepName` é informado, considera só as etapas até ela — a
 * grade mostra a saída dessa etapa, então ordenações posteriores não contam.
 */
export function resolvePreviewSort(
  steps: DataQueryCompiledStep[] | null | undefined,
  selectedStepName?: string | null,
): PreviewSortState | null {
  if (!steps?.length) return null;
  let limit = steps.length;
  if (selectedStepName) {
    const selectedIndex = steps.findIndex((step) => step.name === selectedStepName);
    if (selectedIndex >= 0) limit = selectedIndex + 1;
    else if (selectedStepName === "Fonte") limit = 0;
  }
  for (let index = limit - 1; index >= 0; index -= 1) {
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
