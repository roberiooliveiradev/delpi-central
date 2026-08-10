import {
  canvasCellPatchFromSpec,
  chartCategoryPatchFromSpec,
  chartValuePatchFromSpec,
  isNumericDisplayCategory,
  kpiPatchFromSpec,
  resolveDisplayFormatSpec,
  resolveDisplayFormatTargetLabel,
  specFromCanvasNumberFormat,
  specFromCategoryLabelFormat,
  specFromChartValueFormat,
  specFromKpiValueFormat,
  specFromTableValueFormat,
  specFromTextProjectionFormat,
  tableColumnPatchFromSpec,
  tablePatchFromSpec,
  textPatchFromSpec,
  type DisplayFormatSpec,
  type DisplayFormatTarget,
} from "@delpi/plugin-ui/index";
import {
  findDataRefRunIndexInRange,
  formatTableProjectionColumns,
  mergeComunicadoChartOptions,
  mergeComunicadoKpiOptions,
  mergeComunicadoTableOptions,
  resolveEditableTableProjectionColumns,
  resolveTextBlockDisplayRuns,
  selectedTableProjectionColumnKeys,
  type ComunicadoBlock,
  type ComunicadoCanvasTableBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
  type ComunicadoContentRun,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiViewBlock,
  type ComunicadoTablePartRef,
  type ComunicadoTableViewBlock,
  type ComunicadoTextDataRef,
  type ComunicadoTextProjection,
} from "@delpi/tv-dashboard-presentation";

import type { ComunicadoCanvasTableCellSelection } from "../components/comunicadoEditorContextCore";

export type DisplayFormatTextEditSelection = {
  blockId: string;
  start: number;
  end: number;
};

export type DisplayFormatSelectionContext = {
  selected: ComunicadoBlock | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedTablePart?: ComunicadoTablePartRef | null;
  selectedTableParts?: ComunicadoTablePartRef[];
  selectedCanvasTableCell?: ComunicadoCanvasTableCellSelection | null;
  textEditSelection?: DisplayFormatTextEditSelection | null;
};

export type DisplayFormatSelectionDescriptor = {
  target: DisplayFormatTarget;
  hint: string;
};

function isVisualTextBlock(
  block: ComunicadoBlock,
): block is Extract<ComunicadoBlock, { type: "text" | "heading" | "shape" }> {
  return block.type === "text" || block.type === "heading" || block.type === "shape";
}

function resolveTextRuns(block: Extract<ComunicadoBlock, { type: "text" | "heading" | "shape" }>) {
  if (block.type === "shape") {
    return block.contentRuns?.length ? block.contentRuns : [{ text: block.content ?? "" }];
  }
  return resolveTextBlockDisplayRuns(block);
}

function resolveActiveDataRefRun(
  ctx: DisplayFormatSelectionContext,
): { runIndex: number; dataRef: ComunicadoTextDataRef } | null {
  const selected = ctx.selected;
  if (!selected || !isVisualTextBlock(selected)) return null;
  const selection = ctx.textEditSelection;
  if (!selection || selection.blockId !== selected.id) return null;
  const runs = resolveTextRuns(selected);
  const runIndex = findDataRefRunIndexInRange(runs, selection.start, selection.end);
  if (runIndex == null) return null;
  const dataRef = runs[runIndex]?.dataRef;
  if (!dataRef?.field?.trim()) return null;
  return { runIndex, dataRef };
}

function resolveTableColumnKeys(ctx: DisplayFormatSelectionContext): string[] {
  const selected = ctx.selected;
  if (!selected || selected.type !== "table_view") return [];
  const parts =
    ctx.selectedTableParts?.length
      ? ctx.selectedTableParts
      : ctx.selectedTablePart
        ? [ctx.selectedTablePart]
        : [];
  return selectedTableProjectionColumnKeys(selected, parts);
}

export function resolveDisplayFormatTarget(
  ctx: DisplayFormatSelectionContext,
): DisplayFormatTarget | null {
  return resolveDisplayFormatDescriptor(ctx)?.target ?? null;
}

export function resolveDisplayFormatDescriptor(
  ctx: DisplayFormatSelectionContext,
): DisplayFormatSelectionDescriptor | null {
  const { selected } = ctx;
  if (!selected) return null;

  if (selected.type === "chart_view") {
    if (ctx.selectedChartPart?.kind === "axis" && ctx.selectedChartPart.axis === "x") {
      return {
        target: "chartCategory",
        hint: resolveDisplayFormatTargetLabel("chartCategory"),
      };
    }
    return {
      target: "chartValue",
      hint: resolveDisplayFormatTargetLabel("chartValue"),
    };
  }

  if (selected.type === "kpi_view") {
    const metricField =
      ctx.selectedKpiPart?.kind === "metricCard" ? ctx.selectedKpiPart.field : null;
    return {
      target: "kpi",
      hint: metricField ? `Métrica ${metricField}` : resolveDisplayFormatTargetLabel("kpi"),
    };
  }

  if (selected.type === "table_view") {
    const keys = resolveTableColumnKeys(ctx);
    if (keys.length > 0) {
      const columns = resolveEditableTableProjectionColumns(selected);
      const labels = keys.map((key) => {
        const column = columns.find((item) => item.key === key);
        return column?.label?.trim() || key;
      });
      return {
        target: "tableColumn",
        hint:
          labels.length === 1
            ? `Coluna "${labels[0]}"`
            : `Colunas (${labels.length})`,
      };
    }
    return {
      target: "table",
      hint: resolveDisplayFormatTargetLabel("table"),
    };
  }

  if (selected.type === "canvas_table") {
    const cell = resolveSelectedCanvasCell(selected, ctx.selectedCanvasTableCell);
    const ref = cell?.dataRef?.field?.trim();
    return {
      target: "canvasCell",
      hint: ref
        ? `Campo "${cell?.dataRef?.label?.trim() || ref}"`
        : resolveDisplayFormatTargetLabel("canvasCell"),
    };
  }

  if (isVisualTextBlock(selected)) {
    const activeRun = resolveActiveDataRefRun(ctx);
    if (activeRun) {
      const label = activeRun.dataRef.label?.trim() || activeRun.dataRef.field;
      return {
        target: "textDataRef",
        hint: `Campo "${label}"`,
      };
    }
    if (selected.textProjection?.field?.trim()) {
      const field = selected.textProjection.field.trim();
      return {
        target: "textProjection",
        hint: `Campo "${field}"`,
      };
    }
  }

  return null;
}

export function resolveCurrentDisplayFormatSpec(
  ctx: DisplayFormatSelectionContext,
): DisplayFormatSpec {
  const descriptor = resolveDisplayFormatDescriptor(ctx);
  const selected = ctx.selected;
  if (!selected || !descriptor) return { category: "general", presetId: "general" };
  const { target } = descriptor;

  if (selected.type === "chart_view") {
    const options = mergeComunicadoChartOptions(selected.chartOptions);
    if (target === "chartCategory") {
      return resolveDisplayFormatSpec(
        options.displayCategoryFormat,
        specFromCategoryLabelFormat(options.categoryLabelFormat),
      );
    }
    return resolveDisplayFormatSpec(
      options.displayValueFormat,
      specFromChartValueFormat(options.valueFormat, options.decimalPlaces),
    );
  }

  if (selected.type === "kpi_view") {
    const options = mergeComunicadoKpiOptions(selected.kpiOptions);
    const metricField =
      ctx.selectedKpiPart?.kind === "metricCard" ? ctx.selectedKpiPart.field : null;
    const metric = metricField
      ? selected.kpiProjection?.metrics?.find((item) => item.field === metricField)
      : null;
    return resolveDisplayFormatSpec(
      metric?.displayFormat ?? options.displayValueFormat,
      specFromKpiValueFormat(
        metric?.format ?? options.valueFormat,
        metric?.decimalPlaces ?? options.decimalPlaces,
      ),
    );
  }

  if (selected.type === "table_view") {
    const options = mergeComunicadoTableOptions(selected.tableOptions, selected.tablePreset);
    const keys = resolveTableColumnKeys(ctx);
    if (keys.length > 0) {
      const columns = resolveEditableTableProjectionColumns(selected);
      const first = columns.find((column) => column.key === keys[0]);
      return resolveDisplayFormatSpec(
        first?.displayFormat ?? options.displayValueFormat,
        specFromTableValueFormat(first?.valueFormat ?? options.valueFormat),
      );
    }
    return resolveDisplayFormatSpec(
      options.displayValueFormat,
      specFromTableValueFormat(options.valueFormat),
    );
  }

  if (selected.type === "canvas_table") {
    const cell = resolveSelectedCanvasCell(selected, ctx.selectedCanvasTableCell);
    const dataRef = cell?.dataRef;
    if (dataRef?.field?.trim()) {
      return resolveDisplayFormatSpec(
        dataRef.displayFormat ?? cell?.displayFormat,
        specFromTextProjectionFormat(dataRef.format, dataRef.decimalPlaces),
      );
    }
    return resolveDisplayFormatSpec(
      cell?.displayFormat,
      specFromCanvasNumberFormat(cell?.format ?? "decimal"),
    );
  }

  if (isVisualTextBlock(selected)) {
    const activeRun = resolveActiveDataRefRun(ctx);
    if (activeRun) {
      const ref = activeRun.dataRef;
      return resolveDisplayFormatSpec(
        ref.displayFormat,
        specFromTextProjectionFormat(ref.format, ref.decimalPlaces),
      );
    }
    const projection = selected.textProjection;
    if (projection?.field?.trim()) {
      return resolveDisplayFormatSpec(
        projection.displayFormat,
        specFromTextProjectionFormat(projection.format, projection.decimalPlaces),
      );
    }
  }

  return { category: "general", presetId: "general" };
}

export function sampleValueForDisplayFormat(ctx: DisplayFormatSelectionContext): unknown {
  const target = resolveDisplayFormatTarget(ctx);
  const selected = ctx.selected;
  const resolved = selected && "resolved" in selected ? selected.resolved : undefined;
  if (target === "chartCategory") {
    const row = resolved?.table?.rows?.[0];
    const key = resolved?.table?.columns?.[0]?.key;
    if (row && key != null && row[key] != null) return row[key];
    return "2026-08-03";
  }
  if (target === "kpi") {
    return resolved?.kpi?.value ?? 41.7;
  }
  if (target === "canvasCell" && selected?.type === "canvas_table") {
    const cell = resolveSelectedCanvasCell(selected, ctx.selectedCanvasTableCell);
    if (cell?.value != null) return cell.value;
  }
  if ((target === "textProjection" || target === "textDataRef") && selected && "resolved" in selected) {
    return selected.resolved?.kpi?.value ?? 30;
  }
  if (target === "tableColumn" && selected?.type === "table_view") {
    const keys = resolveTableColumnKeys(ctx);
    const row = resolved?.table?.rows?.[0];
    if (keys[0] && row && row[keys[0]] != null) return row[keys[0]];
  }
  const row = resolved?.table?.rows?.[0];
  const valueKey = resolved?.table?.columns?.[1]?.key;
  if (row && valueKey != null && row[valueKey] != null) return row[valueKey];
  return 30;
}

export function applyDisplayFormatSpecToBlock(
  ctx: DisplayFormatSelectionContext,
  spec: DisplayFormatSpec,
): Partial<ComunicadoBlock> | null {
  const selected = ctx.selected;
  let target = resolveDisplayFormatTarget(ctx);
  if (!selected || !target) return null;

  if (selected.type === "chart_view") {
    /*
     * Eixo X selecionado + formato numérico (% / moeda / número): aplica nos valores.
     * Caso típico — usuário tenta % com o eixo de período focado; o atalho ficava
     * disabled (categoria=date) ou gravava percent no rótulo sem mudar as barras.
     */
    if (target === "chartCategory" && isNumericDisplayCategory(spec.category) && spec.category !== "general") {
      target = "chartValue";
    }
    const current = mergeComunicadoChartOptions(selected.chartOptions);
    const patch =
      target === "chartCategory" ? chartCategoryPatchFromSpec(spec) : chartValuePatchFromSpec(spec);
    return {
      chartOptions: { ...current, ...patch },
    } as Partial<ComunicadoChartViewBlock>;
  }

  if (selected.type === "kpi_view") {
    const current = mergeComunicadoKpiOptions(selected.kpiOptions);
    const kpiPatch = kpiPatchFromSpec(spec);
    const metricField =
      ctx.selectedKpiPart?.kind === "metricCard" ? ctx.selectedKpiPart.field : null;
    if (metricField && selected.kpiProjection?.metrics) {
      return {
        kpiOptions: { ...current, ...kpiPatch },
        kpiProjection: {
          ...selected.kpiProjection,
          metrics: selected.kpiProjection.metrics.map((metric) =>
            metric.field === metricField
              ? {
                  ...metric,
                  displayFormat: spec,
                  format: kpiPatch.valueFormat,
                  decimalPlaces: kpiPatch.decimalPlaces,
                }
              : metric,
          ),
        },
      } as Partial<ComunicadoKpiViewBlock>;
    }
    return { kpiOptions: { ...current, ...kpiPatch } } as Partial<ComunicadoKpiViewBlock>;
  }

  if (selected.type === "table_view") {
    const keys = resolveTableColumnKeys(ctx);
    if (keys.length > 0) {
      const columnPatch = tableColumnPatchFromSpec(spec);
      return {
        tableProjection: formatTableProjectionColumns(selected, keys, columnPatch),
      } as Partial<ComunicadoTableViewBlock>;
    }
    const current = mergeComunicadoTableOptions(selected.tableOptions, selected.tablePreset);
    return {
      tableOptions: { ...current, ...tablePatchFromSpec(spec) },
    } as Partial<ComunicadoTableViewBlock>;
  }

  if (selected.type === "canvas_table") {
    const cellRef = ctx.selectedCanvasTableCell;
    if (!cellRef) return null;
    const cells = selected.cells.map((row) => row.map((cell) => ({ ...cell })));
    const cell = cells[cellRef.row]?.[cellRef.col];
    if (!cell) return null;
    if (cell.dataRef?.field?.trim()) {
      const textPatch = textPatchFromSpec(spec);
      const nextRef: ComunicadoTextDataRef = {
        ...cell.dataRef,
        displayFormat: textPatch.displayFormat,
        format: textPatch.format,
      };
      if (typeof textPatch.decimalPlaces === "number") {
        nextRef.decimalPlaces = textPatch.decimalPlaces;
      } else {
        delete nextRef.decimalPlaces;
      }
      cell.dataRef = nextRef;
      Object.assign(cell, canvasCellPatchFromSpec(spec));
    } else {
      Object.assign(cell, canvasCellPatchFromSpec(spec));
    }
    return { cells } as Partial<ComunicadoCanvasTableBlock>;
  }

  if (isVisualTextBlock(selected)) {
    const textPatch = textPatchFromSpec(spec);
    const activeRun = resolveActiveDataRefRun(ctx);
    if (activeRun) {
      const runs = resolveTextRuns(selected).map((run, index) => {
        if (index !== activeRun.runIndex || !run.dataRef) return run;
        const nextRef: ComunicadoTextDataRef = {
          ...run.dataRef,
          displayFormat: textPatch.displayFormat,
          format: textPatch.format,
        };
        if (typeof textPatch.decimalPlaces === "number") {
          nextRef.decimalPlaces = textPatch.decimalPlaces;
        } else {
          delete nextRef.decimalPlaces;
        }
        return { ...run, dataRef: nextRef } satisfies ComunicadoContentRun;
      });
      return { contentRuns: runs } as Partial<ComunicadoBlock>;
    }
    if (selected.textProjection?.field?.trim()) {
      const next: ComunicadoTextProjection = {
        ...selected.textProjection,
        displayFormat: textPatch.displayFormat,
        format: textPatch.format,
      };
      if (typeof textPatch.decimalPlaces === "number") {
        next.decimalPlaces = textPatch.decimalPlaces;
      } else {
        delete next.decimalPlaces;
      }
      return { textProjection: next } as Partial<ComunicadoBlock>;
    }
  }

  return null;
}

function resolveSelectedCanvasCell(
  block: ComunicadoCanvasTableBlock,
  ref?: ComunicadoCanvasTableCellSelection | null,
) {
  if (!ref || (ref.blockId && ref.blockId !== block.id)) return block.cells[0]?.[0];
  return block.cells[ref.row]?.[ref.col];
}
