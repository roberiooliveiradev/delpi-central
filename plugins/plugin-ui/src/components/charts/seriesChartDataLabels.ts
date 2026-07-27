/**
 * Rótulos de dados — contrato alinhado ao Excel/PowerPoint
 * (Label Contains + Label Position + Leader Lines).
 *
 * @see https://support.microsoft.com/office/change-the-format-of-data-labels-in-a-chart
 */

import type { SeriesChartKind, SeriesChartValueFormat } from "./seriesChartOptions";
import { formatSeriesChartValue } from "./seriesChartOptions";

/** Posição do rótulo (galeria «Adicionar elemento» / Format Data Labels). */
export type SeriesChartDataLabelPosition =
  | "center"
  | "insideEnd"
  | "outsideEnd"
  | "bestFit";

export type SeriesChartDataLabelSeparator = "space" | "comma" | "newline" | "semicolon";

/**
 * Conteúdo e layout dos rótulos (Label Contains + Position).
 * Só aplica quando `showDataLabels` está ligado.
 */
export type SeriesChartDataLabelsConfig = {
  showCategoryName?: boolean;
  showValue?: boolean;
  showPercentage?: boolean;
  showSeriesName?: boolean;
  showLeaderLines?: boolean;
  /** Cor do texto = cor da fatia/série (comum em pizza PPT). */
  colorFromCategory?: boolean;
  position?: SeriesChartDataLabelPosition;
  separator?: SeriesChartDataLabelSeparator;
  /**
   * Oculta rótulo se |valor|/total < limiar (0–1).
   * Ex.: `0.01` esconde fatias &lt; 1%. Default 0 = mostra zeros.
   */
  hideBelowPercent?: number;
};

export type SeriesChartDataLabelsResolved = {
  showCategoryName: boolean;
  showValue: boolean;
  showPercentage: boolean;
  showSeriesName: boolean;
  showLeaderLines: boolean;
  colorFromCategory: boolean;
  position: SeriesChartDataLabelPosition;
  separator: SeriesChartDataLabelSeparator;
  hideBelowPercent: number;
};

export const DEFAULT_SERIES_CHART_DATA_LABELS: SeriesChartDataLabelsResolved = {
  showCategoryName: false,
  showValue: true,
  showPercentage: false,
  showSeriesName: false,
  showLeaderLines: false,
  colorFromCategory: false,
  position: "center",
  separator: "space",
  hideBelowPercent: 0,
};

/** Posição efetiva: `bestFit` ≈ fora (pizza) ou centro (cartesiano). */
export function resolveDataLabelPosition(
  chartType: SeriesChartKind,
  position: SeriesChartDataLabelPosition,
): Exclude<SeriesChartDataLabelPosition, "bestFit"> {
  if (position !== "bestFit") return position;
  if (chartType === "pie" || chartType === "funnel") return "outsideEnd";
  return "center";
}

export function mergeSeriesChartDataLabels(
  partial?: SeriesChartDataLabelsConfig | null,
): SeriesChartDataLabelsResolved {
  const base = DEFAULT_SERIES_CHART_DATA_LABELS;
  if (!partial) return { ...base };
  return {
    showCategoryName: partial.showCategoryName ?? base.showCategoryName,
    showValue: partial.showValue ?? base.showValue,
    showPercentage: partial.showPercentage ?? base.showPercentage,
    showSeriesName: partial.showSeriesName ?? base.showSeriesName,
    showLeaderLines: partial.showLeaderLines ?? base.showLeaderLines,
    colorFromCategory: partial.colorFromCategory ?? base.colorFromCategory,
    position: partial.position ?? base.position,
    separator: partial.separator ?? base.separator,
    hideBelowPercent:
      partial.hideBelowPercent != null && Number.isFinite(partial.hideBelowPercent)
        ? Math.max(0, Math.min(1, partial.hideBelowPercent))
        : base.hideBelowPercent,
  };
}

/**
 * Resolve config ativa. `null` = rótulos desligados.
 * Com `showDataLabels` e sem campos de conteúdo, assume valor (legado).
 */
export function resolveSeriesChartDataLabels(args: {
  showDataLabels?: boolean;
  dataLabels?: SeriesChartDataLabelsConfig | null;
}): SeriesChartDataLabelsResolved | null {
  if (!args.showDataLabels) return null;
  const merged = mergeSeriesChartDataLabels(args.dataLabels);
  const hasExplicitContent =
    args.dataLabels != null &&
    (args.dataLabels.showCategoryName != null ||
      args.dataLabels.showValue != null ||
      args.dataLabels.showPercentage != null ||
      args.dataLabels.showSeriesName != null);
  if (!hasExplicitContent) {
    return { ...merged, showValue: true };
  }
  const anyContent =
    merged.showCategoryName ||
    merged.showValue ||
    merged.showPercentage ||
    merged.showSeriesName;
  if (!anyContent) {
    return { ...merged, showValue: true };
  }
  return merged;
}

function separatorToken(sep: SeriesChartDataLabelSeparator): string {
  switch (sep) {
    case "comma":
      return ", ";
    case "semicolon":
      return "; ";
    case "newline":
      return "\n";
    case "space":
    default:
      return " ";
  }
}

export function formatSeriesChartDataLabelText(args: {
  config: SeriesChartDataLabelsResolved;
  categoryLabel?: string | null;
  seriesName?: string | null;
  value: number;
  total: number;
  valueFormat: SeriesChartValueFormat;
}): string {
  const { config, value, total, valueFormat } = args;
  const parts: string[] = [];
  if (config.showSeriesName) {
    const name = args.seriesName?.trim();
    if (name) parts.push(name);
  }
  if (config.showCategoryName) {
    const cat = args.categoryLabel?.trim();
    if (cat) parts.push(cat);
  }
  if (config.showValue) {
    parts.push(formatSeriesChartValue(value, valueFormat));
  }
  if (config.showPercentage) {
    const pct = total > 0 ? Math.round((Math.abs(value) / total) * 100) : 0;
    parts.push(`${pct}%`);
  }
  return parts.join(separatorToken(config.separator));
}

export function shouldHideDataLabel(args: {
  config: SeriesChartDataLabelsResolved;
  value: number;
  total: number;
}): boolean {
  const { config, value, total } = args;
  if (!(config.hideBelowPercent > 0) || !(total > 0)) return false;
  return Math.abs(value) / total < config.hideBelowPercent;
}

/** Folga extra no plot centralizado quando rótulos ficam fora (evita clip). */
export function dataLabelOutsideGutterPx(
  config: SeriesChartDataLabelsResolved | null,
  chartType: SeriesChartKind,
): number {
  if (!config) return 0;
  const pos = resolveDataLabelPosition(chartType, config.position);
  if (pos !== "outsideEnd") return 0;
  if (chartType === "pie" || chartType === "funnel" || chartType === "radar") return 40;
  return 16;
}

/** Presets da galeria (espelho PPT: posição + Label Contains). */
export type SeriesChartDataLabelsPresetId =
  | "none"
  | "center"
  | "insideEnd"
  | "outsideEnd"
  | "bestFit"
  | "categoryPercent"
  | "valuePercent"
  | "percent"
  | "category"
  | "show";

export function dataLabelsConfigFromPreset(
  preset: SeriesChartDataLabelsPresetId,
): { showDataLabels: boolean; dataLabels: SeriesChartDataLabelsConfig } {
  switch (preset) {
    case "none":
      return { showDataLabels: false, dataLabels: {} };
    case "show":
    case "center":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: true,
          showCategoryName: false,
          showPercentage: false,
          showSeriesName: false,
          showLeaderLines: false,
          colorFromCategory: false,
          position: "center",
          separator: "space",
        },
      };
    case "insideEnd":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: true,
          showCategoryName: false,
          showPercentage: false,
          showSeriesName: false,
          showLeaderLines: false,
          colorFromCategory: false,
          position: "insideEnd",
          separator: "space",
        },
      };
    case "outsideEnd":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: true,
          showCategoryName: false,
          showPercentage: false,
          showSeriesName: false,
          showLeaderLines: true,
          colorFromCategory: false,
          position: "outsideEnd",
          separator: "space",
        },
      };
    case "bestFit":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: true,
          showCategoryName: false,
          showPercentage: false,
          showSeriesName: false,
          showLeaderLines: true,
          colorFromCategory: false,
          position: "bestFit",
          separator: "space",
        },
      };
    case "categoryPercent":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: false,
          showCategoryName: true,
          showPercentage: true,
          showSeriesName: false,
          showLeaderLines: true,
          colorFromCategory: true,
          position: "outsideEnd",
          separator: "space",
        },
      };
    case "valuePercent":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: true,
          showCategoryName: false,
          showPercentage: true,
          showSeriesName: false,
          showLeaderLines: true,
          colorFromCategory: false,
          position: "outsideEnd",
          separator: "space",
        },
      };
    case "percent":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: false,
          showCategoryName: false,
          showPercentage: true,
          showSeriesName: false,
          showLeaderLines: false,
          colorFromCategory: false,
          position: "center",
          separator: "space",
        },
      };
    case "category":
      return {
        showDataLabels: true,
        dataLabels: {
          showValue: false,
          showCategoryName: true,
          showPercentage: false,
          showSeriesName: false,
          showLeaderLines: true,
          colorFromCategory: true,
          position: "outsideEnd",
          separator: "space",
        },
      };
    default: {
      const _exhaustive: never = preset;
      return _exhaustive;
    }
  }
}

export function matchDataLabelsPreset(
  showDataLabels: boolean | undefined,
  dataLabels: SeriesChartDataLabelsConfig | null | undefined,
): SeriesChartDataLabelsPresetId {
  if (!showDataLabels) return "none";
  const resolved = resolveSeriesChartDataLabels({ showDataLabels: true, dataLabels });
  if (!resolved) return "none";

  const presets: SeriesChartDataLabelsPresetId[] = [
    "categoryPercent",
    "valuePercent",
    "percent",
    "category",
    "outsideEnd",
    "insideEnd",
    "bestFit",
    "center",
  ];
  for (const id of presets) {
    const { dataLabels: expected } = dataLabelsConfigFromPreset(id);
    const e = mergeSeriesChartDataLabels(expected);
    if (
      e.showCategoryName === resolved.showCategoryName &&
      e.showValue === resolved.showValue &&
      e.showPercentage === resolved.showPercentage &&
      e.showSeriesName === resolved.showSeriesName &&
      e.position === resolved.position &&
      e.showLeaderLines === resolved.showLeaderLines &&
      e.colorFromCategory === resolved.colorFromCategory
    ) {
      return id;
    }
  }
  return "center";
}
