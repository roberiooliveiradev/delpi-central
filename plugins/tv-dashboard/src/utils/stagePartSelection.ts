/**
 * Subseleção de filho no palco (partes compostas + célula da Grade).
 * Fonte única para Esc `clear-parts` e flags de chrome.
 */

export function resolveStageHasPartSelection(flags: {
  selectedChartPart?: unknown;
  selectedKpiPart?: unknown;
  selectedTablePart?: unknown;
  selectedInputPart?: unknown;
  selectedCanvasTableCell?: unknown;
}): boolean {
  return Boolean(
    flags.selectedChartPart ||
      flags.selectedKpiPart ||
      flags.selectedTablePart ||
      flags.selectedInputPart ||
      flags.selectedCanvasTableCell,
  );
}
