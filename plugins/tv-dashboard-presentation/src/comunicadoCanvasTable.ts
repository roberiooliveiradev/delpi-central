/**
 * Grade canvas (`canvas_table`) — células tipadas, opções de design e helpers.
 * Ilustrativa com opcional `dataRef` por célula (≠ `table_view` live).
 */

import type {
  ComunicadoBlockStyle,
  ComunicadoCanvasTableBlock,
  ComunicadoContentRun,
  ComunicadoTextDataRef,
} from "./comunicadoTypes";
import { normalizeContentRuns, shouldPersistContentRuns } from "./comunicadoContentRuns";
import { normalizeTextDataRef } from "./textViewProjection";

export const CANVAS_TABLE_MIN_ROWS = 1;
export const CANVAS_TABLE_MAX_ROWS = 20;
export const CANVAS_TABLE_MIN_COLS = 1;
export const CANVAS_TABLE_MAX_COLS = 12;
export const CANVAS_TABLE_DEFAULT_FONT_SIZE = 18;
export const CANVAS_TABLE_SPARKLINE_MIN_POINTS = 5;
export const CANVAS_TABLE_SPARKLINE_MAX_POINTS = 60;

export type CanvasTableCellKind = "text" | "number" | "sparkline";

export type CanvasTableNumberFormat =
  | "plain"
  | "integer"
  | "decimal"
  | "percent"
  | "currency";

export type CanvasTableCellStyle = {
  fontSize?: number;
  fontWeight?: number;
  color?: string;
  backgroundColor?: string;
  textAlign?: "left" | "center" | "right";
};

export type CanvasTableCell = {
  kind: CanvasTableCellKind;
  text?: string;
  value?: number | null;
  format?: CanvasTableNumberFormat;
  /** Série estática do sparkline (5–60 pontos). */
  series?: number[];
  style?: CanvasTableCellStyle;
  /** Formatação parcial — sem runs = run implícito com `text` + `style`. */
  contentRuns?: ComunicadoContentRun[];
  /** Campo dinâmico (fonte efetiva = `dataSourceId` da célula ou do bloco). */
  dataRef?: ComunicadoTextDataRef;
  /**
   * Fonte desta célula (bloco `data_source` do slide).
   * Vazio = herda `ComunicadoCanvasTableBlock.dataSourceId`.
   */
  dataSourceId?: string;
};

export type CanvasTableHeaderStyle = "subtle" | "accent" | "none";
export type CanvasTableBorderStyle = "all" | "horizontal" | "none";

export type CanvasTableOptions = {
  fontSize?: number;
  bandedRows?: boolean;
  bandedColumns?: boolean;
  headerStyle?: CanvasTableHeaderStyle;
  borderStyle?: CanvasTableBorderStyle;
  /** Larguras relativas (%); soma ~100. */
  columnWidths?: number[];
};

export type CanvasTableCellRef = { row: number; col: number };

export function clampCanvasTableDimension(
  value: unknown,
  min: number,
  max: number,
  fallback: number,
): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(min, Math.min(max, Math.round(n)));
}

export function isCanvasTableCell(value: unknown): value is CanvasTableCell {
  if (!value || typeof value !== "object") return false;
  const kind = (value as CanvasTableCell).kind;
  return kind === "text" || kind === "number" || kind === "sparkline";
}

/** String legado ou objeto → célula tipada. */
export function normalizeCanvasTableCell(value: unknown): CanvasTableCell {
  if (isCanvasTableCell(value)) {
    const cell: CanvasTableCell = { kind: value.kind };
    if (typeof value.text === "string") cell.text = value.text;
    if (value.value === null || (typeof value.value === "number" && Number.isFinite(value.value))) {
      cell.value = value.value ?? null;
    }
    if (
      value.format === "plain" ||
      value.format === "integer" ||
      value.format === "decimal" ||
      value.format === "percent" ||
      value.format === "currency"
    ) {
      cell.format = value.format;
    }
    if (Array.isArray(value.series)) {
      cell.series = value.series
        .map((n) => Number(n))
        .filter((n) => Number.isFinite(n))
        .slice(0, CANVAS_TABLE_SPARKLINE_MAX_POINTS);
    }
    if (value.style && typeof value.style === "object") {
      cell.style = { ...value.style };
    }
    const runs = normalizeContentRuns((value as CanvasTableCell).contentRuns);
    if (runs && shouldPersistContentRuns(runs)) cell.contentRuns = runs;
    const dataRef = normalizeTextDataRef((value as CanvasTableCell).dataRef);
    if (dataRef) cell.dataRef = dataRef;
    const cellSource =
      typeof (value as CanvasTableCell).dataSourceId === "string"
        ? (value as CanvasTableCell).dataSourceId.trim()
        : "";
    if (cellSource) cell.dataSourceId = cellSource;
    return cell;
  }
  return { kind: "text", text: value == null ? "" : String(value) };
}

/**
 * Runs de exibição da célula — contentRuns ou um run implícito com estilo monolítico.
 */
export function canvasTableCellDisplayRuns(
  cell: CanvasTableCell,
  displayText: string,
): ComunicadoContentRun[] {
  if (cell.contentRuns?.length) return cell.contentRuns;
  const style = cell.style
    ? {
        fontSize: cell.style.fontSize,
        color: cell.style.color,
        fontWeight:
          cell.style.fontWeight != null && cell.style.fontWeight >= 600
            ? ("bold" as const)
            : undefined,
      }
    : undefined;
  const hasStyle = Boolean(style && Object.values(style).some((v) => v != null));
  return [{ text: displayText, style: hasStyle ? style : undefined }];
}

export function normalizeCanvasTableCells(
  value: unknown,
  rows: number,
  cols: number,
): CanvasTableCell[][] {
  const source = Array.isArray(value) ? value : [];
  return Array.from({ length: rows }, (_, rowIndex) => {
    const row = Array.isArray(source[rowIndex]) ? source[rowIndex] : [];
    return Array.from({ length: cols }, (_, colIndex) =>
      normalizeCanvasTableCell(row[colIndex]),
    );
  });
}

export function canvasTableCellPlainText(cell: CanvasTableCell | string | null | undefined): string {
  const normalized = normalizeCanvasTableCell(cell);
  if (normalized.kind === "number") {
    if (normalized.value != null && Number.isFinite(normalized.value)) {
      return formatCanvasTableNumber(normalized.value, normalized.format ?? "decimal");
    }
    return normalized.text ?? "";
  }
  if (normalized.kind === "sparkline") {
    if (normalized.value != null && Number.isFinite(normalized.value)) {
      return formatCanvasTableNumber(normalized.value, normalized.format ?? "decimal");
    }
    return normalized.text ?? "";
  }
  return normalized.text ?? "";
}

export function canvasTableCellsToStringMatrix(
  cells: CanvasTableCell[][] | string[][] | undefined,
): string[][] {
  if (!cells?.length) return [];
  return cells.map((row) => row.map((cell) => canvasTableCellPlainText(cell)));
}

export function parseLooseNumber(raw: string): number | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  // pt-BR: 1.400,5 ou 1400.5
  const normalized = trimmed
    .replace(/\s/g, "")
    .replace(/[R$\u00a4%]/g, "")
    .replace(/\.(?=\d{3}(\D|$))/g, "")
    .replace(",", ".");
  const n = Number(normalized);
  return Number.isFinite(n) ? n : null;
}

export function formatCanvasTableNumber(
  value: number,
  format: CanvasTableNumberFormat = "decimal",
): string {
  if (!Number.isFinite(value)) return "";
  switch (format) {
    case "integer":
      return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(value);
    case "percent":
      return new Intl.NumberFormat("pt-BR", {
        style: "percent",
        maximumFractionDigits: 1,
      }).format(value > 1 || value < -1 ? value / 100 : value);
    case "currency":
      return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
      }).format(value);
    case "plain":
      return String(value);
    case "decimal":
    default:
      return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(value);
  }
}

export function inferCanvasTableCellFromText(text: string): CanvasTableCell {
  const trimmed = text.trim();
  if (!trimmed) return { kind: "text", text: "" };
  const seriesParts = trimmed.split(/[;\s]+/).map((p) => parseLooseNumber(p)).filter((n): n is number => n != null);
  if (seriesParts.length >= CANVAS_TABLE_SPARKLINE_MIN_POINTS) {
    return {
      kind: "sparkline",
      series: seriesParts.slice(0, CANVAS_TABLE_SPARKLINE_MAX_POINTS),
      value: seriesParts[seriesParts.length - 1] ?? null,
      text: trimmed,
    };
  }
  const asNumber = parseLooseNumber(trimmed);
  if (asNumber != null && /[\d]/.test(trimmed) && !/[a-zA-ZÀ-ú]{2,}/.test(trimmed)) {
    return { kind: "number", value: asNumber, text: trimmed, format: "decimal" };
  }
  return { kind: "text", text };
}

export function mergeCanvasTableOptions(
  options?: CanvasTableOptions | null,
): Required<
  Pick<
    CanvasTableOptions,
    "fontSize" | "bandedRows" | "bandedColumns" | "headerStyle" | "borderStyle"
  >
> &
  CanvasTableOptions {
  return {
    fontSize: options?.fontSize ?? CANVAS_TABLE_DEFAULT_FONT_SIZE,
    bandedRows: options?.bandedRows ?? false,
    bandedColumns: options?.bandedColumns ?? false,
    headerStyle: options?.headerStyle ?? "subtle",
    borderStyle: options?.borderStyle ?? "all",
    columnWidths: options?.columnWidths,
  };
}

export type CanvasTableStylePresetId = "grid" | "minimal" | "banded";

export function canvasTablePresetOptions(
  preset: CanvasTableStylePresetId,
): Partial<CanvasTableOptions> {
  if (preset === "minimal") {
    return {
      bandedRows: false,
      bandedColumns: false,
      headerStyle: "none",
      borderStyle: "horizontal",
    };
  }
  if (preset === "banded") {
    return {
      bandedRows: true,
      bandedColumns: false,
      headerStyle: "accent",
      borderStyle: "all",
    };
  }
  return {
    bandedRows: false,
    bandedColumns: false,
    headerStyle: "subtle",
    borderStyle: "all",
  };
}

export function resolveCanvasTableFontSize(
  block: Pick<ComunicadoCanvasTableBlock, "style" | "canvasTableOptions">,
): number {
  const fromOptions = block.canvasTableOptions?.fontSize;
  if (fromOptions != null && Number.isFinite(fromOptions) && fromOptions > 0) {
    return Math.round(fromOptions);
  }
  const fromStyle = block.style?.fontSize;
  if (fromStyle != null && Number.isFinite(fromStyle) && fromStyle > 0) {
    return Math.round(fromStyle);
  }
  return CANVAS_TABLE_DEFAULT_FONT_SIZE;
}

/** CSS vars + tipografia do host da grade. */
export function resolveCanvasTableHostStyle(
  block: Pick<ComunicadoCanvasTableBlock, "style" | "canvasTableOptions" | "headerRow">,
): Record<string, string | number | undefined> {
  const opts = mergeCanvasTableOptions(block.canvasTableOptions);
  const fontSize = resolveCanvasTableFontSize(block);
  const style = block.style ?? {};
  const headerBg =
    opts.headerStyle === "accent"
      ? "#089bdb"
      : opts.headerStyle === "none"
        ? "transparent"
        : "#e2e8f0";
  const headerColor = opts.headerStyle === "accent" ? "#ffffff" : style.color ?? "#0f172a";
  const border =
    opts.borderStyle === "none" ? "transparent" : style.borderColor ?? "#94a3b8";
  return {
    color: style.color,
    fontSize: `${fontSize}px`,
    fontFamily: style.fontFamily,
    textAlign: style.textAlign,
    ["--tdp-canvas-table-border" as string]: border,
    ["--tdp-canvas-table-header-bg" as string]: headerBg,
    ["--tdp-canvas-table-header-fg" as string]: headerColor,
    ["--tdp-canvas-table-band" as string]: "rgba(8, 155, 219, 0.06)",
    ["--tdp-canvas-table-border-mode" as string]: opts.borderStyle,
  };
}

export function scaleCanvasTableBlockTypography(
  block: ComunicadoCanvasTableBlock,
  scale: number,
  scaleFontPx: (px: number, scale: number) => number,
): ComunicadoCanvasTableBlock {
  const baseFont = resolveCanvasTableFontSize(block);
  const nextFont = scaleFontPx(baseFont, scale);
  const nextStyle: ComunicadoBlockStyle = {
    ...(block.style ?? {}),
    fontSize: nextFont,
  };
  const nextOptions: CanvasTableOptions = {
    ...(block.canvasTableOptions ?? {}),
    fontSize: nextFont,
  };
  const nextCells = block.cells.map((row) =>
    row.map((cell) => {
      const normalized = normalizeCanvasTableCell(cell);
      if (!normalized.style?.fontSize) return normalized;
      return {
        ...normalized,
        style: {
          ...normalized.style,
          fontSize: scaleFontPx(normalized.style.fontSize, scale),
        },
      };
    }),
  );
  return {
    ...block,
    style: nextStyle,
    canvasTableOptions: nextOptions,
    cells: nextCells,
  };
}

export function buildCanvasTableSparklinePath(
  points: number[],
  width = 100,
  height = 28,
  yMin?: number,
  yMax?: number,
): string | null {
  const series = points.filter((n) => Number.isFinite(n));
  if (series.length < 2) return null;
  const min = yMin ?? Math.min(...series);
  const max = yMax ?? Math.max(...series);
  const span = max - min || 1;
  return series
    .map((point, index) => {
      const x = (index / (series.length - 1)) * width;
      const y = height - ((point - min) / span) * (height - 4) - 2;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

/** Eixo Y pinado para sparklines da mesma coluna. */
export function resolveColumnSparklineAxis(
  cells: CanvasTableCell[][],
  col: number,
): { min: number; max: number } | null {
  const values: number[] = [];
  for (const row of cells) {
    const cell = normalizeCanvasTableCell(row[col]);
    if (cell.kind === "sparkline" && cell.series?.length) {
      for (const n of cell.series) {
        if (Number.isFinite(n)) values.push(n);
      }
    }
  }
  if (values.length < 2) return null;
  return { min: Math.min(...values), max: Math.max(...values) };
}

export function parseCanvasTableOptions(raw: unknown): CanvasTableOptions | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const src = raw as Record<string, unknown>;
  const next: CanvasTableOptions = {};
  if (typeof src.fontSize === "number" && Number.isFinite(src.fontSize) && src.fontSize > 0) {
    next.fontSize = Math.round(src.fontSize);
  }
  if (typeof src.bandedRows === "boolean") next.bandedRows = src.bandedRows;
  if (typeof src.bandedColumns === "boolean") next.bandedColumns = src.bandedColumns;
  if (src.headerStyle === "subtle" || src.headerStyle === "accent" || src.headerStyle === "none") {
    next.headerStyle = src.headerStyle;
  }
  if (src.borderStyle === "all" || src.borderStyle === "horizontal" || src.borderStyle === "none") {
    next.borderStyle = src.borderStyle;
  }
  if (Array.isArray(src.columnWidths)) {
    next.columnWidths = src.columnWidths
      .map((n) => Number(n))
      .filter((n) => Number.isFinite(n) && n > 0);
  }
  return Object.keys(next).length ? next : undefined;
}
