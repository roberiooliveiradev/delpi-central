import type { DisplayFormatSpec } from "./types";
import {
  canvasNumberFormatFromSpec,
  categoryLabelFormatFromSpec,
  chartValueFormatFromSpec,
  kpiValueFormatFromSpec,
  tableValueFormatFromSpec,
  textProjectionFormatFromSpec,
  type LegacyCanvasNumberFormat,
  type LegacyCategoryLabelFormat,
  type LegacyChartValueFormat,
  type LegacyKpiValueFormat,
  type LegacyTableValueFormat,
  type LegacyTextProjectionFormat,
} from "./legacy";

export type ChartDisplayFormatPatch = {
  displayValueFormat?: DisplayFormatSpec;
  displayCategoryFormat?: DisplayFormatSpec;
  valueFormat?: LegacyChartValueFormat;
  decimalPlaces?: number | null;
  categoryLabelFormat?: LegacyCategoryLabelFormat;
};

export type TableDisplayFormatPatch = {
  displayValueFormat: DisplayFormatSpec;
  valueFormat: LegacyTableValueFormat;
};

export type KpiDisplayFormatPatch = {
  displayValueFormat: DisplayFormatSpec;
  valueFormat: LegacyKpiValueFormat;
  decimalPlaces?: number;
};

export type CanvasCellDisplayFormatPatch = {
  displayFormat: DisplayFormatSpec;
  format: LegacyCanvasNumberFormat;
};

export type TextDisplayFormatPatch = {
  displayFormat: DisplayFormatSpec;
  format: LegacyTextProjectionFormat;
  decimalPlaces?: number;
};

export type TableColumnDisplayFormatPatch = {
  displayFormat: DisplayFormatSpec;
  valueFormat: LegacyTableValueFormat;
};

/** Gravação: spec + espelho legado (nunca o contrário). */
export function chartValuePatchFromSpec(spec: DisplayFormatSpec): ChartDisplayFormatPatch {
  const mirror = chartValueFormatFromSpec(spec);
  return {
    displayValueFormat: spec,
    valueFormat: mirror.valueFormat,
    decimalPlaces: mirror.decimalPlaces,
  };
}

export function chartCategoryPatchFromSpec(spec: DisplayFormatSpec): ChartDisplayFormatPatch {
  return {
    displayCategoryFormat: spec,
    categoryLabelFormat: categoryLabelFormatFromSpec(spec),
  };
}

export function tablePatchFromSpec(spec: DisplayFormatSpec): TableDisplayFormatPatch {
  return {
    displayValueFormat: spec,
    valueFormat: tableValueFormatFromSpec(spec),
  };
}

export function kpiPatchFromSpec(spec: DisplayFormatSpec): KpiDisplayFormatPatch {
  const valueFormat = kpiValueFormatFromSpec(spec);
  const patch: KpiDisplayFormatPatch = {
    displayValueFormat: spec,
    valueFormat,
  };
  if (typeof spec.decimalPlaces === "number") patch.decimalPlaces = spec.decimalPlaces;
  return patch;
}

export function canvasCellPatchFromSpec(spec: DisplayFormatSpec): CanvasCellDisplayFormatPatch {
  return {
    displayFormat: spec,
    format: canvasNumberFormatFromSpec(spec),
  };
}

export function textPatchFromSpec(spec: DisplayFormatSpec): TextDisplayFormatPatch {
  const mirror = textProjectionFormatFromSpec(spec);
  const patch: TextDisplayFormatPatch = {
    displayFormat: spec,
    format: mirror.format,
  };
  if (typeof mirror.decimalPlaces === "number") patch.decimalPlaces = mirror.decimalPlaces;
  return patch;
}

export function tableColumnPatchFromSpec(spec: DisplayFormatSpec): TableColumnDisplayFormatPatch {
  return {
    displayFormat: spec,
    valueFormat: tableValueFormatFromSpec(spec),
  };
}
