import type {
  ComunicadoChartPartRef,
  ComunicadoTablePartRef,
} from "@delpi/tv-dashboard-presentation";

/**
 * Reconcilia seleção de partes compostas após mudar a projeção visível.
 * Identidade estável = chave do campo (não o índice). Toggle/remoção/re-adição
 * de coluna ou série não deixa colIndex/seriesIndex fantasma nem exige if pontual
 * em cada editor.
 */

export function reconcileTableHeaderPartsAfterVisibleKeysChange(options: {
  prevVisibleKeys: string[];
  nextVisibleKeys: string[];
  selectedParts: ComunicadoTablePartRef[];
}): ComunicadoTablePartRef[] {
  const { prevVisibleKeys, nextVisibleKeys, selectedParts } = options;
  const next: ComunicadoTablePartRef[] = [];
  for (const part of selectedParts) {
    if (part.kind !== "headerCell" || part.colIndex == null) {
      next.push(part);
      continue;
    }
    const key = prevVisibleKeys[part.colIndex];
    if (!key) continue;
    const colIndex = nextVisibleKeys.indexOf(key);
    if (colIndex < 0) continue;
    next.push({ kind: "headerCell", colIndex });
  }
  return next;
}

export function reconcileChartSeriesPartAfterSeriesFieldsChange(options: {
  prevSeriesFields: string[];
  nextSeriesFields: string[];
  selectedPart: ComunicadoChartPartRef | null;
}): ComunicadoChartPartRef | null {
  const { prevSeriesFields, nextSeriesFields, selectedPart } = options;
  if (!selectedPart) return null;
  if (selectedPart.kind !== "series" && selectedPart.kind !== "marker") {
    return selectedPart;
  }
  const index = selectedPart.seriesIndex ?? 0;
  const field = prevSeriesFields[index];
  if (!field) return null;
  const seriesIndex = nextSeriesFields.indexOf(field);
  if (seriesIndex < 0) return null;
  return { ...selectedPart, seriesIndex };
}
