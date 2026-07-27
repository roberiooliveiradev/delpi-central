import { formatNumber, formatPct } from "../../utils/localeFormat";
import { DECK_TABLE_DEFAULTS } from "../../theme/deckColorCatalog";
import type { ConfigurableTableClassNames } from "./configurableTableClasses";

export type PresentationTableColumn = {
  key: string;
  label: string;
  /** Largura relativa da coluna (% do total da tabela). Omitido = auto. */
  widthPct?: number;
};

export type ConfigurableTableTextAlign = "left" | "center" | "right";

export type ConfigurableTableValueFormat = "auto" | "number" | "currency" | "percent";

export type ConfigurableTablePreset = "grid" | "minimal" | "banded";

/** Estilo de traço da grade (caneta PPT — Desenhar Bordas). */
export type ConfigurableTableBorderStyle = "solid" | "dashed" | "dotted";

export type ConfigurableTableOptions = {
  title?: string;
  showTitle?: boolean;
  showHeader?: boolean;
  /** Linha de totais (Excel Table Design → Total Row). */
  showTotalRow?: boolean;
  /** Destaque na 1ª coluna (Excel → First Column). */
  emphasizeFirstColumn?: boolean;
  /** Destaque na última coluna (Excel → Last Column). */
  emphasizeLastColumn?: boolean;
  /** Listras nas colunas (Excel → Banded Columns). */
  bandedColumns?: boolean;
  headerBg?: string;
  headerTextColor?: string;
  cellBg?: string;
  cellTextColor?: string;
  borderColor?: string;
  /** Peso da grade entre células (px). */
  borderWidth?: number;
  /** Estilo de traço da grade (sólido / tracejado / pontilhado). */
  borderStyle?: ConfigurableTableBorderStyle;
  fontSize?: number;
  /** Família tipográfica da grade (global). */
  fontFamily?: string;
  /** Peso tipográfico global (`bold` / `normal` / número CSS). */
  fontWeight?: string | number;
  /** Estilo tipográfico global (`italic` / `normal`). */
  fontStyle?: string;
  textAlign?: ConfigurableTableTextAlign;
  /** Listras nas linhas (Excel → Banded Rows). */
  zebraStripe?: boolean;
  showBorders?: boolean;
  valueFormat?: ConfigurableTableValueFormat;
  headerUppercase?: boolean;
  /** Quebra texto nas células (Excel → Quebrar Texto Automaticamente). */
  wrapText?: boolean;
  /** Altura mínima das linhas de dados (px). */
  rowHeightPx?: number;
};

/** Cores herdadas do catálogo DECK_* (tema claro do gráfico). */
export const DEFAULT_CONFIGURABLE_TABLE_OPTIONS: ConfigurableTableOptions = {
  /** Ligado por padrão — vazio usa o label da rota (paridade com título do gráfico). */
  showTitle: true,
  showHeader: true,
  showTotalRow: false,
  emphasizeFirstColumn: false,
  emphasizeLastColumn: false,
  bandedColumns: false,
  textAlign: "left",
  zebraStripe: false,
  showBorders: true,
  valueFormat: "auto",
  headerUppercase: true,
  headerBg: DECK_TABLE_DEFAULTS.headerBg,
  headerTextColor: DECK_TABLE_DEFAULTS.headerTextColor,
  cellBg: DECK_TABLE_DEFAULTS.cellBg,
  cellTextColor: DECK_TABLE_DEFAULTS.cellTextColor,
  borderColor: DECK_TABLE_DEFAULTS.borderColor,
  borderWidth: DECK_TABLE_DEFAULTS.borderWidth,
  borderStyle: "solid",
};

export const CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS = [0.5, 1, 1.5, 2, 3, 4] as const;

export const CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS: Array<{
  value: ConfigurableTableBorderStyle;
  label: string;
}> = [
  { value: "solid", label: "Contínuo" },
  { value: "dashed", label: "Tracejado" },
  { value: "dotted", label: "Pontilhado" },
];

export const CONFIGURABLE_TABLE_VALUE_FORMAT_OPTIONS = [
  { value: "auto", label: "Automático" },
  { value: "number", label: "Número" },
  { value: "currency", label: "Moeda (R$)" },
  { value: "percent", label: "Percentual" },
] as const;

export const CONFIGURABLE_TABLE_TEXT_ALIGN_OPTIONS = [
  { value: "left", label: "Esquerda" },
  { value: "center", label: "Centro" },
  { value: "right", label: "Direita" },
] as const;

export function presetDefaultConfigurableTableOptions(preset: ConfigurableTablePreset): ConfigurableTableOptions {
  if (preset === "minimal") {
    return { ...DEFAULT_CONFIGURABLE_TABLE_OPTIONS, showBorders: false };
  }
  if (preset === "banded") {
    return { ...DEFAULT_CONFIGURABLE_TABLE_OPTIONS, zebraStripe: true };
  }
  return { ...DEFAULT_CONFIGURABLE_TABLE_OPTIONS };
}

export function mergeConfigurableTableOptions(
  partial?: ConfigurableTableOptions | null,
  preset?: ConfigurableTablePreset,
): ConfigurableTableOptions {
  const base = preset ? presetDefaultConfigurableTableOptions(preset) : { ...DEFAULT_CONFIGURABLE_TABLE_OPTIONS };
  return { ...base, ...(partial ?? {}) };
}

export function resolveConfigurableTableDisplayOptions(
  blockOptions: ConfigurableTableOptions | undefined,
  preset: ConfigurableTablePreset,
  resolved?: { label?: string },
): ConfigurableTableOptions {
  const merged = mergeConfigurableTableOptions(blockOptions, preset);
  const fallbackTitle = resolved?.label ?? "";
  return {
    ...merged,
    title: merged.title?.trim() || fallbackTitle,
  };
}

export function formatConfigurableTableCellValue(
  value: unknown,
  format: ConfigurableTableValueFormat = "auto",
): string {
  if (value === null || value === undefined) return "—";
  if (typeof value !== "number") return String(value);

  if (format === "currency") {
    return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  }
  if (format === "percent") {
    return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
  }
  if (format === "number") {
    return value.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  }
  if (Math.abs(value) <= 100 && !Number.isInteger(value)) return formatPct(value);
  return formatNumber(value);
}

/** Soma colunas numéricas; primeira coluna não numérica recebe o rótulo «Total». */
export function buildConfigurableTableTotalRow(
  columns: PresentationTableColumn[],
  rows: Array<Record<string, unknown>>,
): Record<string, unknown> {
  const total: Record<string, unknown> = {};
  let labeled = false;
  for (const column of columns) {
    const nums = rows
      .map((row) => row[column.key])
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
    if (nums.length > 0) {
      total[column.key] = nums.reduce((sum, value) => sum + value, 0);
    } else if (!labeled) {
      total[column.key] = "Total";
      labeled = true;
    } else {
      total[column.key] = "";
    }
  }
  return total;
}

export function configurableTableOptionsCssVars(
  options: ConfigurableTableOptions,
  cssVarPrefix = "delpi-ui-config-table",
): Record<string, string | number> {
  const vars: Record<string, string | number> = {};
  if (options.headerBg) vars[`--${cssVarPrefix}-header-bg`] = options.headerBg;
  if (options.headerTextColor) vars[`--${cssVarPrefix}-header-color`] = options.headerTextColor;
  if (options.cellBg) vars[`--${cssVarPrefix}-cell-bg`] = options.cellBg;
  if (options.cellTextColor) vars[`--${cssVarPrefix}-cell-color`] = options.cellTextColor;
  if (options.borderColor) vars[`--${cssVarPrefix}-border-color`] = options.borderColor;
  if (options.borderWidth != null && options.borderWidth >= 0) {
    vars[`--${cssVarPrefix}-border-width`] = `${options.borderWidth}px`;
  }
  if (options.borderStyle) vars[`--${cssVarPrefix}-border-style`] = options.borderStyle;
  if (options.fontSize != null && options.fontSize > 0) vars[`--${cssVarPrefix}-font-size`] = `${options.fontSize}px`;
  if (options.fontFamily?.trim()) vars[`--${cssVarPrefix}-font-family`] = options.fontFamily.trim();
  if (options.fontWeight != null && options.fontWeight !== "") {
    vars[`--${cssVarPrefix}-font-weight`] = String(options.fontWeight);
  }
  if (options.fontStyle?.trim()) vars[`--${cssVarPrefix}-font-style`] = options.fontStyle.trim();
  if (options.rowHeightPx != null && options.rowHeightPx > 0) {
    vars[`--${cssVarPrefix}-row-height`] = `${Math.max(16, Math.min(200, options.rowHeightPx))}px`;
  }
  return vars;
}

export function configurableTableOptionsModifierClasses(
  options: ConfigurableTableOptions,
  classNames?: Pick<
    ConfigurableTableClassNames,
    | "rootMinimal"
    | "rootBanded"
    | "rootBandedCols"
    | "rootFirstColumn"
    | "rootLastColumn"
    | "rootAlignCenter"
    | "rootAlignRight"
    | "rootHeaderNormalCase"
    | "rootWrap"
    | "rootFixedCols"
  >,
  hasColumnWidths = false,
): string[] {
  const cn = classNames ?? {
    rootMinimal: "delpi-ui-config-table--minimal",
    rootBanded: "delpi-ui-config-table--banded",
    rootBandedCols: "delpi-ui-config-table--banded-cols",
    rootFirstColumn: "delpi-ui-config-table--first-column",
    rootLastColumn: "delpi-ui-config-table--last-column",
    rootAlignCenter: "delpi-ui-config-table--align-center",
    rootAlignRight: "delpi-ui-config-table--align-right",
    rootHeaderNormalCase: "delpi-ui-config-table--header-normal-case",
    rootWrap: "delpi-ui-config-table--wrap",
    rootFixedCols: "delpi-ui-config-table--fixed-cols",
  };
  const classes: string[] = [];
  if (options.showBorders === false) classes.push(cn.rootMinimal);
  if (options.zebraStripe) classes.push(cn.rootBanded);
  if (options.bandedColumns) classes.push(cn.rootBandedCols);
  if (options.emphasizeFirstColumn) classes.push(cn.rootFirstColumn);
  if (options.emphasizeLastColumn) classes.push(cn.rootLastColumn);
  if (options.textAlign && options.textAlign !== "left") {
    classes.push(options.textAlign === "center" ? cn.rootAlignCenter : cn.rootAlignRight);
  }
  if (options.headerUppercase === false) classes.push(cn.rootHeaderNormalCase);
  if (options.wrapText || hasColumnWidths) classes.push(cn.rootWrap);
  if (hasColumnWidths) classes.push(cn.rootFixedCols);
  return classes;
}
