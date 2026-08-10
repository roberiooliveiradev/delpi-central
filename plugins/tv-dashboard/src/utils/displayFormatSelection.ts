import {
  canvasCellPatchFromSpec,
  chartCategoryPatchFromSpec,
  chartValuePatchFromSpec,
  isNumericDisplayCategory,
  kpiPatchFromSpec,
  resolveDisplayFormatSpec,
  specFromCanvasNumberFormat,
  specFromCategoryLabelFormat,
  specFromChartValueFormat,
  specFromKpiValueFormat,
  specFromTableValueFormat,
  tablePatchFromSpec,
  type DisplayFormatSpec,
  type DisplayFormatTarget,
} from "@delpi/plugin-ui/index";
import {
  mergeComunicadoChartOptions,
  mergeComunicadoKpiOptions,
  mergeComunicadoTableOptions,
  type ComunicadoBlock,
  type ComunicadoCanvasTableBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiViewBlock,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import type { ComunicadoCanvasTableCellSelection } from "../components/comunicadoEditorContextCore";

export type DisplayFormatSelectionContext = {
  selected: ComunicadoBlock | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedCanvasTableCell?: ComunicadoCanvasTableCellSelection | null;
};

export function resolveDisplayFormatTarget(
  ctx: DisplayFormatSelectionContext,
): DisplayFormatTarget | null {
  const { selected } = ctx;
  if (!selected) return null;
  if (selected.type === "chart_view") {
    if (ctx.selectedChartPart?.kind === "axis" && ctx.selectedChartPart.axis === "x") {
      return "chartCategory";
    }
    return "chartValue";
  }
  if (selected.type === "kpi_view") return "kpi";
  if (selected.type === "table_view") return "table";
  if (selected.type === "canvas_table") return "canvasCell";
  return null;
}

export function resolveCurrentDisplayFormatSpec(
  ctx: DisplayFormatSelectionContext,
): DisplayFormatSpec {
  const target = resolveDisplayFormatTarget(ctx);
  const selected = ctx.selected;
  if (!selected || !target) return { category: "general", presetId: "general" };

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
      specFromKpiValueFormat(metric?.format ?? options.valueFormat, metric?.decimalPlaces ?? options.decimalPlaces),
    );
  }

  if (selected.type === "table_view") {
    const options = mergeComunicadoTableOptions(selected.tableOptions, selected.tablePreset);
    return resolveDisplayFormatSpec(
      options.displayValueFormat,
      specFromTableValueFormat(options.valueFormat),
    );
  }

  if (selected.type === "canvas_table") {
    const cell = resolveSelectedCanvasCell(selected, ctx.selectedCanvasTableCell);
    return resolveDisplayFormatSpec(
      cell?.displayFormat,
      specFromCanvasNumberFormat(cell?.format ?? "decimal"),
    );
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
    Object.assign(cell, canvasCellPatchFromSpec(spec));
    return { cells } as Partial<ComunicadoCanvasTableBlock>;
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
