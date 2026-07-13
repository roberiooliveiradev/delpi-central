import type { CSSProperties } from "react";

import {
  DECK_COLOR_ACCENT,
  DECK_COLOR_SURFACE,
  DECK_COLOR_TEXT_STRONG,
  DECK_SHAPE_DEFAULTS,
  resolvePaintTextColor,
} from "@delpi/plugin-ui/index";

import { isComunicadoShapeKind } from "./comunicadoShapeCatalog";
import {
  COMUNICADO_MARKER_RADIUS_DEFAULT,
  geometryToPersistedFrame,
  resolveBlockPlacementStyle,
  resolveShapeGeometry,
} from "./comunicadoShapeGeometry";
import {
  defaultStrokeWidthForPrimitive,
  isLineShapeKind,
  isPointShapeKind,
  resolveShapePrimitive,
} from "./comunicadoVisualPrimitive";
import { normalizeShapeConnector } from "./comunicadoConnectors";
import {
  serializeContentRuns,
  shouldPersistContentRuns,
  syncTextBlockFields,
} from "./comunicadoContentRuns";
import { applyComunicadoTextEffectsToCss } from "./comunicadoTextEffects";
import { normalizeComunicadoImageCrop } from "./comunicadoImageCrop";
import {
  normalizeBlockAnimations,
  serializeBlockAnimations,
} from "./comunicadoBlockAnimations";
import { DEFAULT_COMUNICADO_CHART_OPTIONS, type ComunicadoChartOptions } from "./comunicadoChartOptions";
import {
  DEFAULT_COMUNICADO_KPI_OPTIONS,
  mergeComunicadoKpiOptions,
  type ComunicadoKpiOptions,
} from "./comunicadoKpiOptions";
import {
  kpiOptionsToParts,
  normalizeKpiPartsForLoad,
  partsToKpiOptions,
  type ComunicadoKpiPartsMap,
} from "./comunicadoKpiParts";
import {
  chartOptionsToParts,
  normalizeChartPartsForLoad,
  type ComunicadoChartPartsMap,
} from "./comunicadoChartParts";
import {
  presetDefaultTableOptions,
  type ComunicadoTableOptions,
} from "./comunicadoTableOptions";
import {
  normalizeTablePartsForLoad,
  tableOptionsToParts,
  type ComunicadoTablePartsMap,
} from "./comunicadoTableParts";
import {
  TABLE_VIEW_MAX_COLS_CAP,
  TABLE_VIEW_MAX_ROWS_CAP,
  normalizeTableViewLimit,
} from "./tableViewLimits";
import {
  comunicadoVerticalAlignToJustifyContent,
  defaultVerticalAlignForVisualBox,
  isComunicadoVisualBoxBlock,
  resolveVisualBoxProfile,
} from "./comunicadoVisualBox";
import type {
  ComunicadoBackground,
  ComunicadoBlock,
  ComunicadoBlockStyle,
  ComunicadoCanvasTableBlock,
  ComunicadoConfig,
  ComunicadoDataBinding,
  ComunicadoDataBlockType,
  ComunicadoDataFilters,
  ComunicadoDataResolved,
  ComunicadoChartType,
  ComunicadoTablePreset,
  ComunicadoFrame,
  ComunicadoGeometryVertex,
  ComunicadoCustomFontRef,
  ComunicadoShapeKind,
  ComunicadoTextDecoration,
  ComunicadoVerticalAlign,
} from "./comunicadoTypes";
import {
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
} from "./comunicadoTypes";
import {
  isDataBoundEditorBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
} from "./comunicadoDataArchitecture";

export {
  isDataBoundEditorBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
  getLinkedDataSourceIds,
  shouldHideDataSourceOnStage,
  listDataSourceBlocks,
  resolveDataSourceLabel,
  resolvePreferredDataSourceId,
  dataSourceOptionsForInspector,
} from "./comunicadoDataArchitecture";

export function newBlockId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `block-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const DEFAULT_BACKGROUND: ComunicadoBackground = { type: "color", value: "#ffffff" };
const DEFAULT_HEADLINE = "Título";

/**
 * Escala tipográfica quando o palco já está no tamanho de design do `viewportProfile`.
 * Preferir `fontScale={1}` + escala CSS uniforme (`DesignViewportStage` / zoom do editor).
 * @deprecated Mantido em 1 para compatibilidade; não usar fator fixo (ex.: 0.35).
 */
export const COMUNICADO_EDITOR_FONT_SCALE = 1;

const DATA_BLOCK_TYPES = new Set(["data_kpi", "data_chart", "data_table", "data_metric"]);

export function isDataBlockType(type: string): type is ComunicadoDataBlockType {
  return DATA_BLOCK_TYPES.has(type);
}

export function mergeDataFilters(
  slideFilters?: ComunicadoDataFilters,
  blockParams?: ComunicadoDataBinding["params"],
): ComunicadoDataFilters {
  const merged: ComunicadoDataFilters = { ...(slideFilters ?? {}) };
  if (blockParams) {
    for (const [key, value] of Object.entries(blockParams)) {
      if (value !== null && value !== undefined && value !== "") {
        merged[key] = value;
      }
    }
  }
  return merged;
}

export function defaultDataBlockTypeForRoute(
  allowedModes: string[] | undefined,
): ComunicadoDataBlockType {
  const modes = allowedModes ?? [];
  if (modes.includes("kpi")) return "data_kpi";
  if (modes.includes("line_chart") || modes.includes("bar_chart")) return "data_chart";
  if (modes.includes("table")) return "data_table";
  return "data_kpi";
}

export function createDataSourceBlock(
  operationId: string,
  options: {
    label?: string;
    defaultParams?: Record<string, string | number | boolean | null>;
    refreshSec?: number;
  } = {},
): ComunicadoBlock {
  return {
    id: newBlockId(),
    type: "data_source",
    frame: { x: 8, y: 30, w: 18, h: 18 },
    style: { zIndex: 1, color: DECK_COLOR_ACCENT },
    dataBinding: {
      operationId,
      params: { ...(options.defaultParams ?? {}) },
      displayMode: "auto",
      label: options.label,
      refreshSec: options.refreshSec,
    },
  };
}

export function createChartViewBlock(chartType: ComunicadoChartType): ComunicadoBlock {
  const chartOptions = { ...DEFAULT_COMUNICADO_CHART_OPTIONS };
  return {
    id: newBlockId(),
    type: "chart_view",
    chartType,
    chartOptions,
    chartParts: chartOptionsToParts(chartOptions),
    frame: { x: 10, y: 28, w: 80, h: 45 },
    style: { zIndex: 2, borderRadius: 0, color: DECK_COLOR_TEXT_STRONG },
  };
}

export function createTableViewBlock(
  rows: number,
  cols: number,
  preset: ComunicadoTablePreset = "grid",
): ComunicadoBlock {
  const height = Math.min(55, 12 + rows * 4);
  const width = Math.min(92, 20 + cols * 8);
  return {
    id: newBlockId(),
    type: "table_view",
    tablePreset: preset,
    tableOptions: presetDefaultTableOptions(preset),
    tableParts: tableOptionsToParts(presetDefaultTableOptions(preset)),
    // rows/cols do picker só dimensionam o frame — limite de dados fica no binding da fonte.
    frame: { x: 5, y: 55 - height / 2, w: width, h: height },
    style: { zIndex: 2, borderRadius: 0, color: DECK_COLOR_TEXT_STRONG },
  };
}

export const CANVAS_TABLE_MIN_ROWS = 1;
export const CANVAS_TABLE_MAX_ROWS = 20;
export const CANVAS_TABLE_MIN_COLS = 1;
export const CANVAS_TABLE_MAX_COLS = 12;

function clampCanvasTableDimension(value: unknown, min: number, max: number, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, Math.round(parsed)));
}

export function normalizeCanvasTableCells(
  value: unknown,
  rows: number,
  cols: number,
): string[][] {
  const source = Array.isArray(value) ? value : [];
  return Array.from({ length: rows }, (_, rowIndex) => {
    const row = Array.isArray(source[rowIndex]) ? source[rowIndex] : [];
    return Array.from({ length: cols }, (_, colIndex) => {
      const cell = row[colIndex];
      return cell == null ? "" : String(cell);
    });
  });
}

export function createCanvasTableBlock(rows = 3, cols = 3): ComunicadoCanvasTableBlock {
  const safeRows = clampCanvasTableDimension(
    rows,
    CANVAS_TABLE_MIN_ROWS,
    CANVAS_TABLE_MAX_ROWS,
    3,
  );
  const safeCols = clampCanvasTableDimension(
    cols,
    CANVAS_TABLE_MIN_COLS,
    CANVAS_TABLE_MAX_COLS,
    3,
  );
  const height = Math.min(60, 10 + safeRows * 6);
  const width = Math.min(92, 18 + safeCols * 10);
  return {
    id: newBlockId(),
    type: "canvas_table",
    rows: safeRows,
    cols: safeCols,
    cells: normalizeCanvasTableCells([], safeRows, safeCols),
    headerRow: true,
    frame: { x: 50 - width / 2, y: 50 - height / 2, w: width, h: height },
    style: defaultStyle("canvas_table"),
  };
}

export function createKpiViewBlock(options?: Partial<ComunicadoKpiOptions>): ComunicadoBlock {
  const kpiOptions = mergeComunicadoKpiOptions({
    ...DEFAULT_COMUNICADO_KPI_OPTIONS,
    // Ícone só quando o caller pede explicitamente (evita «forma» Gauge fantasma na TV).
    ...(options?.iconName || options?.showIcon
      ? {
          iconName: options.iconName ?? "Gauge",
          showIcon: options.showIcon ?? true,
        }
      : { showIcon: false }),
    ...options,
  });
  return {
    id: newBlockId(),
    type: "kpi_view",
    kpiOptions,
    kpiParts: kpiOptionsToParts(kpiOptions),
    frame: { x: 8, y: 28, w: 32, h: 24 },
    style: { zIndex: 2, borderRadius: 0, color: DECK_COLOR_TEXT_STRONG },
  };
}

export function createDataBlock(
  operationId: string,
  options: {
    blockType?: ComunicadoDataBlockType;
    label?: string;
    displayMode?: ComunicadoDataBinding["displayMode"];
    defaultParams?: Record<string, string | number | boolean | null>;
  } = {},
): ComunicadoBlock {
  const blockType = options.blockType ?? "data_kpi";
  const frame =
    blockType === "data_chart"
      ? { x: 10, y: 28, w: 80, h: 45 }
      : blockType === "data_table"
        ? { x: 5, y: 55, w: 90, h: 35 }
        : { x: 5, y: 28, w: 28, h: 22 };
  return {
    id: newBlockId(),
    type: blockType,
    frame,
    style: { zIndex: 2, color: "#ffffff" },
    dataBinding: {
      operationId,
      params: { ...(options.defaultParams ?? {}) },
      displayMode:
        options.displayMode ??
        (blockType === "data_chart"
          ? "line_chart"
          : blockType === "data_table"
            ? "table"
            : "kpi"),
      label: options.label,
    },
  };
}

export function defaultFrame(type: ComunicadoBlock["type"], shape?: ComunicadoShapeKind): ComunicadoFrame {
  if (type === "data_kpi") return { x: 5, y: 28, w: 28, h: 22 };
  if (type === "data_chart") return { x: 10, y: 28, w: 80, h: 45 };
  if (type === "data_table") return { x: 5, y: 55, w: 90, h: 35 };
  if (type === "data_metric") return { x: 5, y: 28, w: 28, h: 22 };
  if (type === "data_source") return { x: 8, y: 30, w: 18, h: 18 };
  if (type === "chart_view") return { x: 10, y: 28, w: 80, h: 45 };
  if (type === "table_view") return { x: 5, y: 55, w: 90, h: 35 };
  if (type === "canvas_table") return { x: 20, y: 30, w: 60, h: 30 };
  if (type === "kpi_view") return { x: 8, y: 28, w: 32, h: 24 };
  if (type === "heading") return { x: 5, y: 12, w: 90, h: 18 };
  if (type === "text") return { x: 5, y: 34, w: 90, h: 14 };
  if (type === "image") return { x: 10, y: 22, w: 80, h: 56 };
  if (type === "video") return { x: 5, y: 15, w: 90, h: 70 };
  if (shape && isPointShapeKind(shape)) return { x: 45, y: 45, w: 0, h: 0 };
  if (shape && isLineShapeKind(shape)) return { x: 10, y: 48, w: 80, h: 4 };
  if (
    shape === "arrow-right" ||
    shape === "arrow-left" ||
    shape === "arrow-up" ||
    shape === "arrow-down" ||
    shape === "arrow-left-right" ||
    shape === "arrow-up-down" ||
    shape === "chevron-right" ||
    shape === "chevron-left" ||
    shape === "notched-arrow-right"
  ) {
    return { x: 35, y: 40, w: 30, h: 20 };
  }
  if (shape === "star" || shape === "star-4" || shape === "heart") return { x: 38, y: 35, w: 24, h: 24 };
  if (shape === "flowchart-terminator") return { x: 30, y: 42, w: 40, h: 16 };
  if (shape === "callout-rect") return { x: 28, y: 28, w: 44, h: 36 };
  if (type === "icon") return { x: 42, y: 40, w: 16, h: 16 };
  return { x: 30, y: 30, w: 40, h: 40 };
}

export function defaultStyle(type: ComunicadoBlock["type"], shape?: ComunicadoShapeKind) {
  if (type === "heading") {
    return {
      fontSize: 56,
      color: "auto" as const,
      fontFamily: "Inter, system-ui, sans-serif",
      textAlign: "center" as const,
      verticalAlign: "middle" as const,
      lineHeight: 1.15,
      fontWeight: "bold" as const,
      fill: "transparent",
      backgroundColor: "transparent",
      stroke: "transparent",
      strokeWidth: 0,
      borderWidth: 0,
      borderColor: "transparent",
      zIndex: 2,
    };
  }
  if (type === "text") {
    return {
      fontSize: 28,
      color: "auto" as const,
      fontFamily: "Inter, system-ui, sans-serif",
      textAlign: "center" as const,
      verticalAlign: "top" as const,
      lineHeight: 1.15,
      fontWeight: "normal" as const,
      fill: "transparent",
      backgroundColor: "transparent",
      stroke: "transparent",
      strokeWidth: 0,
      borderWidth: 0,
      borderColor: "transparent",
      zIndex: 2,
    };
  }
  if (type === "image" || type === "video") {
    return { objectFit: "contain" as const, zIndex: 1 };
  }
  if (type === "shape") {
    const primitive = shape ? resolveShapePrimitive(shape) : "area";
    const base = {
      zIndex: 1,
      fill: DECK_SHAPE_DEFAULTS.fill,
      stroke: primitive === "line" ? DECK_SHAPE_DEFAULTS.lineStroke : DECK_SHAPE_DEFAULTS.stroke,
      strokeWidth: defaultStrokeWidthForPrimitive(primitive),
      opacity: primitive === "area" ? 0.9 : 1,
      color: "auto" as const,
      fontSize: 18,
      fontFamily: "Inter, system-ui, sans-serif",
      textAlign: "center" as const,
      verticalAlign: "middle" as const,
      fontWeight: "normal" as const,
    };
    if (shape && isPointShapeKind(shape)) {
      return { ...base, markerRadius: COMUNICADO_MARKER_RADIUS_DEFAULT };
    }
    if (shape === "rounded-rect" || shape === "callout-rect" || shape === "callout-rounded") {
      return { ...base, borderRadius: 16 };
    }
    if (shape === "round-same-side-rect") return { ...base, borderRadius: 12 };
    if (shape === "ellipse" || shape === "flowchart-terminator") return { ...base, borderRadius: 9999 };
    if (shape === "flowchart-process") return { ...base, borderRadius: 4 };
    return base;
  }
  if (type === "icon") {
    return { zIndex: 2, color: DECK_COLOR_SURFACE, strokeWidth: 2 };
  }
  if (isDataBlockType(type) || isDataSourceBlockType(type)) {
    return { zIndex: 2, color: DECK_COLOR_TEXT_STRONG };
  }
  if (isDataViewBlockType(type)) {
    return { zIndex: 2, color: DECK_COLOR_TEXT_STRONG };
  }
  if (type === "canvas_table") {
    return {
      zIndex: 2,
      color: DECK_COLOR_TEXT_STRONG,
      backgroundColor: "#ffffff",
      borderColor: "#94a3b8",
      borderWidth: 1,
      fontSize: 18,
      fontFamily: "Inter, system-ui, sans-serif",
      textAlign: "left" as const,
    };
  }
  return {};
}

export function createBlock(
  type: ComunicadoBlock["type"],
  content = "",
  shape?: ComunicadoShapeKind,
): ComunicadoBlock {
  const base = {
    id: newBlockId(),
    type,
    frame: defaultFrame(type, shape),
    style: defaultStyle(type, shape),
  };
  if (type === "heading" || type === "text") {
    return { ...base, type, content };
  }
  if (type === "shape") {
    const kind = shape ?? "rectangle";
    const shapeBlock = { ...base, type, shape: kind, content: content || "" } as ComunicadoBlock;
    if (shapeBlock.type === "shape") {
      return { ...shapeBlock, frame: geometryToPersistedFrame(shapeBlock) };
    }
    return shapeBlock;
  }
  if (type === "image" || type === "video") {
    return { ...base, type };
  }
  if (type === "icon") {
    return { ...base, type: "icon", iconName: content || "Star" };
  }
  if (isDataBlockType(type)) {
    return createDataBlock("", { blockType: type });
  }
  return { ...base, type: "text", content };
}

export function createShapeBlock(shape: ComunicadoShapeKind): ComunicadoBlock {
  return createBlock("shape", "", shape);
}

export function createIconBlock(iconName: string): ComunicadoBlock {
  return createBlock("icon", iconName);
}

function readGroupId(block: Record<string, unknown>): string | undefined {
  return typeof block.groupId === "string" && block.groupId.trim() ? block.groupId.trim() : undefined;
}

function readLinkFields(block: Record<string, unknown>) {
  return {
    href: typeof block.href === "string" && block.href.trim() ? block.href.trim() : undefined,
    linkTarget:
      block.linkTarget === "_self" ? ("_self" as const) : block.linkTarget === "_blank" ? ("_blank" as const) : undefined,
  };
}

function normalizeVertices(value: unknown): ComunicadoGeometryVertex[] | undefined {
  if (!Array.isArray(value) || value.length === 0) return undefined;
  const points: ComunicadoGeometryVertex[] = [];
  for (const item of value) {
    if (!item || typeof item !== "object") continue;
    const raw = item as Record<string, unknown>;
    const x = Number(raw.x);
    const y = Number(raw.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    points.push({
      x: Math.max(0, Math.min(100, x)),
      y: Math.max(0, Math.min(100, y)),
    });
  }
  return points.length > 0 ? points : undefined;
}

export function parseComunicadoConfig(raw: Record<string, unknown> | undefined | null): ComunicadoConfig {
  const cfg = raw ?? {};

  // Array explícito (inclusive vazio) — não remigrar headline em blocos padrão.
  if (Array.isArray(cfg.blocks)) {
    const blocks = cfg.blocks as ComunicadoBlock[];
    return {
      version: Number(cfg.version) || (blocks.length > 0 ? detectConfigVersion(blocks) : 2),
      headline: String(cfg.headline ?? ""),
      subtitle: String(cfg.subtitle ?? ""),
      background: normalizeBackground(cfg.background),
      blocks: blocks.map(normalizeBlock),
      dataFilters: normalizeDataFilters(cfg.dataFilters),
      customFonts: normalizeCustomFonts(cfg.customFonts),
      speakerNotes: typeof cfg.speakerNotes === "string" ? cfg.speakerNotes : undefined,
    };
  }

  const headline = String(cfg.headline ?? DEFAULT_HEADLINE);
  const subtitle = String(cfg.subtitle ?? "");
  return {
    version: 2,
    headline,
    subtitle,
    background: normalizeBackground(cfg.background),
    customFonts: normalizeCustomFonts(cfg.customFonts),
    blocks: [
      createBlock("heading", headline),
      ...(subtitle ? [createBlock("text", subtitle)] : []),
    ],
    speakerNotes: typeof cfg.speakerNotes === "string" ? cfg.speakerNotes : undefined,
  };
}

function detectConfigVersion(blocks: ComunicadoBlock[]): number {
  if (blocks.some((block) => isDataSourceBlockType(block.type) || isDataViewBlockType(block.type))) {
    return 5;
  }
  if (blocks.some((block) => isDataBlockType(block.type))) return 4;
  const hasV3 = blocks.some((block) => {
    if (block.type === "shape" || block.type === "icon") return true;
    if (block.groupId) return true;
    if (block.type === "heading" || block.type === "text") {
      if (block.href) return true;
      if (block.contentRuns && shouldPersistContentRuns(block.contentRuns)) return true;
    } else if (block.type === "image" || block.type === "video") {
      if (block.href) return true;
    }
    const style = block.style ?? {};
    return Boolean(
      style.fontFamily ||
        style.fontStyle ||
        style.textDecoration ||
        style.rotation ||
        style.fill ||
        style.stroke,
    );
  });
  return hasV3 ? 3 : 2;
}

export function serializeComunicadoConfig(config: ComunicadoConfig): Record<string, unknown> {
  const headingBlock = config.blocks?.find((b) => b.type === "heading");
  const textBlock = config.blocks?.find((b) => b.type === "text");
  const background = config.background ?? DEFAULT_BACKGROUND;
  const serializedBackground =
    background.type === "image"
      ? { type: "image", assetId: background.assetId }
      : background.type === "gradient"
        ? {
            type: "gradient",
            from: background.from,
            to: background.to,
            angle: background.angle ?? 180,
          }
        : { type: "color", value: background.value || "#ffffff" };
  const blocks = (config.blocks ?? []).map(serializeBlock);
  const version = config.version ?? detectConfigVersion(config.blocks ?? []);
  const payload: Record<string, unknown> = {
    version,
    headline:
      headingBlock && "content" in headingBlock
        ? headingBlock.content
        : (config.headline ?? ""),
    subtitle: textBlock && "content" in textBlock ? textBlock.content : config.subtitle ?? "",
    background: serializedBackground,
    blocks,
  };
  if (config.dataFilters && Object.keys(config.dataFilters).length > 0) {
    payload.dataFilters = config.dataFilters;
  }
  if (config.customFonts?.length) {
    payload.customFonts = config.customFonts.map(({ assetId, familyName }) => ({
      assetId,
      familyName,
    }));
  }
  if (config.speakerNotes) payload.speakerNotes = config.speakerNotes;
  return payload;
}

function serializeBlock(block: ComunicadoBlock): Record<string, unknown> {
  const base: Record<string, unknown> = {
    id: block.id,
    type: block.type,
    frame: block.frame,
    style: block.style ?? {},
  };
  if (block.groupId) base.groupId = block.groupId;
  const serializedAnimations = serializeBlockAnimations(block.animations);
  if (serializedAnimations) base.animations = serializedAnimations;
  if (block.type === "heading" || block.type === "text") {
    const textFields = serializeTextBlockFields(block);
    Object.assign(base, textFields);
    if (block.href) base.href = block.href;
    if (block.linkTarget) base.linkTarget = block.linkTarget;
  } else if (block.type === "image" || block.type === "video") {
    base.assetId = block.assetId;
    if (block.href) base.href = block.href;
    if (block.linkTarget) base.linkTarget = block.linkTarget;
    if (block.type === "image" && block.imageCrop) base.imageCrop = block.imageCrop;
  } else if (block.type === "shape") {
    base.shape = block.shape;
    if (block.content) base.content = block.content;
    if (block.href) base.href = block.href;
    if (block.linkTarget) base.linkTarget = block.linkTarget;
    if (block.vertices && block.vertices.length > 0) {
      base.vertices = block.vertices.map((point) => ({ x: point.x, y: point.y }));
    }
    if (block.connector) {
      base.connector = {
        fromBlockId: block.connector.fromBlockId,
        toBlockId: block.connector.toBlockId,
        fromAnchor: block.connector.fromAnchor ?? "center",
        toAnchor: block.connector.toAnchor ?? "center",
      };
    }
  } else if (block.type === "icon") {
    base.iconName = block.iconName;
    if (block.href) base.href = block.href;
    if (block.linkTarget) base.linkTarget = block.linkTarget;
  } else if (isDataBlockType(block.type) && "dataBinding" in block) {
    base.dataBinding = {
      operationId: block.dataBinding.operationId,
      params: block.dataBinding.params ?? {},
      displayMode: block.dataBinding.displayMode,
      label: block.dataBinding.label,
      valueField: block.dataBinding.valueField,
      maxRows: block.dataBinding.maxRows,
      refreshSec: block.dataBinding.refreshSec,
    };
  } else if (block.type === "data_source" && "dataBinding" in block) {
    base.dataBinding = {
      operationId: block.dataBinding.operationId,
      params: block.dataBinding.params ?? {},
      displayMode: block.dataBinding.displayMode,
      label: block.dataBinding.label,
      valueField: block.dataBinding.valueField,
      maxRows: block.dataBinding.maxRows,
      refreshSec: block.dataBinding.refreshSec,
    };
  } else if (block.type === "chart_view") {
    base.chartType = block.chartType;
    if (block.dataSourceId) base.dataSourceId = block.dataSourceId;
    if (block.chartOptions) base.chartOptions = { ...block.chartOptions };
    if (block.chartParts) base.chartParts = { ...block.chartParts };
  } else if (block.type === "table_view") {
    base.tablePreset = block.tablePreset;
    if (block.dataSourceId) base.dataSourceId = block.dataSourceId;
    if (block.maxRows != null) base.maxRows = block.maxRows;
    if (block.maxCols != null) base.maxCols = block.maxCols;
    if (block.tableOptions) base.tableOptions = { ...block.tableOptions };
    if (block.tableParts) base.tableParts = { ...block.tableParts };
  } else if (block.type === "canvas_table") {
    base.rows = block.rows;
    base.cols = block.cols;
    base.cells = block.cells.map((row) => [...row]);
    if (block.headerRow != null) base.headerRow = block.headerRow;
  } else if (block.type === "kpi_view") {
    if (block.dataSourceId) base.dataSourceId = block.dataSourceId;
    if (block.kpiOptions) base.kpiOptions = { ...block.kpiOptions };
    if (block.kpiParts) base.kpiParts = { ...block.kpiParts };
  }
  return base;
}

function serializeTextBlockFields(
  block: Extract<ComunicadoBlock, { type: "heading" } | { type: "text" }>,
): Record<string, unknown> {
  const payload: Record<string, unknown> = { content: block.content };
  const serializedRuns = serializeContentRuns(block.contentRuns);
  if (serializedRuns) payload.contentRuns = serializedRuns;
  return payload;
}

function normalizeDataFilters(value: unknown): ComunicadoDataFilters | undefined {
  if (!value || typeof value !== "object") return undefined;
  const filters: ComunicadoDataFilters = {};
  for (const [key, raw] of Object.entries(value as Record<string, unknown>)) {
    if (raw === null || raw === undefined || raw === "") continue;
    if (typeof raw === "string" || typeof raw === "number" || typeof raw === "boolean") {
      filters[key] = raw;
    }
  }
  return Object.keys(filters).length > 0 ? filters : undefined;
}

function normalizeCustomFonts(value: unknown): ComunicadoCustomFontRef[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const fonts = value.flatMap((item): ComunicadoCustomFontRef[] => {
    if (!item || typeof item !== "object") return [];
    const raw = item as Record<string, unknown>;
    const assetId = typeof raw.assetId === "string" ? raw.assetId.trim() : "";
    const familyName = typeof raw.familyName === "string" ? raw.familyName.trim() : "";
    if (!assetId || !familyName) return [];
    return [{
      assetId,
      familyName,
      url: typeof raw.url === "string" && raw.url.trim() ? raw.url.trim() : undefined,
    }];
  });
  return fonts.length ? fonts : undefined;
}

function normalizeBackground(value: unknown): ComunicadoBackground {
  if (!value || typeof value !== "object") return DEFAULT_BACKGROUND;
  const bg = value as Record<string, unknown>;
  if (bg.type === "image") {
    return {
      type: "image",
      assetId: typeof bg.assetId === "string" ? bg.assetId : undefined,
      url: typeof bg.url === "string" ? bg.url : undefined,
      value: typeof bg.value === "string" ? bg.value : undefined,
    };
  }
  if (bg.type === "gradient") {
    const from = typeof bg.from === "string" && bg.from.trim() ? bg.from : "#0f172a";
    const to = typeof bg.to === "string" && bg.to.trim() ? bg.to : "#1e3a5f";
    const angle = typeof bg.angle === "number" ? bg.angle : 180;
    return { type: "gradient", from, to, angle };
  }
  const color = typeof bg.value === "string" && bg.value.trim() ? bg.value : "#ffffff";
  return { type: "color", value: color };
}

function attachBlockAnimations<T extends ComunicadoBlock>(
  block: T,
  raw: Record<string, unknown>,
): T {
  const animations = normalizeBlockAnimations(raw.animations);
  return animations?.length ? { ...block, animations } : block;
}

function normalizeBlock(value: unknown): ComunicadoBlock {
  if (!value || typeof value !== "object") {
    return createBlock("text", "");
  }
  const block = value as Record<string, unknown>;
  const type = (block.type as ComunicadoBlock["type"]) ?? "text";
  const frame = normalizeFrame(block.frame, type);
  const shape = typeof block.shape === "string" ? (block.shape as ComunicadoShapeKind) : undefined;
  const rawStyle = (block.style as ComunicadoBlock["style"]) ?? {};
  const style = { ...defaultStyle(type, shape), ...rawStyle };
  const id = typeof block.id === "string" ? block.id : newBlockId();
  const groupId = readGroupId(block);
  const links = readLinkFields(block);
  if (type === "heading" || type === "text") {
    const legacyContent = typeof block.content === "string" ? block.content : "";
    const textFields = syncTextBlockFields(legacyContent, block.contentRuns);
    return attachBlockAnimations(
      {
        id,
        type,
        frame,
        style,
        groupId,
        ...textFields,
        href: links.href,
        linkTarget: links.linkTarget,
      },
      block,
    );
  }
  if (type === "shape") {
    const kind = shape && isComunicadoShapeKind(shape) ? shape : "rectangle";
    const vertices = normalizeVertices(block.vertices);
    const connector = normalizeShapeConnector(block.connector);
    return attachBlockAnimations(
      {
        id,
        type,
        frame,
        style: { ...defaultStyle("shape", kind), ...style },
        shape: kind,
        groupId,
        content: typeof block.content === "string" ? block.content : "",
        href: links.href,
        linkTarget: links.linkTarget,
        ...(vertices ? { vertices } : {}),
        ...(connector ? { connector } : {}),
      },
      block,
    );
  }
  if (type === "icon") {
    const iconName =
      typeof block.iconName === "string" && block.iconName.trim() ? block.iconName.trim() : "Star";
    return attachBlockAnimations(
      {
        id,
        type: "icon",
        frame,
        style: { ...defaultStyle("icon"), ...style },
        iconName,
        groupId,
        href: links.href,
        linkTarget: links.linkTarget,
      },
      block,
    );
  }
  if (isDataBlockType(type)) {
    const bindingRaw = block.dataBinding;
    const binding =
      bindingRaw && typeof bindingRaw === "object"
        ? (bindingRaw as ComunicadoDataBinding)
        : { operationId: "" };
    return attachBlockAnimations(
      {
        id,
        type,
        frame,
        style: { ...defaultStyle(type), ...style },
        groupId,
        dataBinding: {
          operationId: String(binding.operationId ?? ""),
          params: (binding.params as ComunicadoDataBinding["params"]) ?? {},
          displayMode: binding.displayMode,
          label: binding.label,
          valueField: binding.valueField,
          maxRows: binding.maxRows,
          refreshSec: binding.refreshSec,
        },
        resolved:
          block.resolved && typeof block.resolved === "object"
            ? (block.resolved as ComunicadoDataResolved)
            : undefined,
      } as ComunicadoBlock,
      block,
    );
  }
  if (type === "data_source") {
    const bindingRaw = block.dataBinding;
    const binding =
      bindingRaw && typeof bindingRaw === "object"
        ? (bindingRaw as ComunicadoDataBinding)
        : { operationId: "" };
    return attachBlockAnimations(
      {
        id,
        type: "data_source",
        frame,
        style: { ...defaultStyle("data_source"), ...style },
        groupId,
        dataBinding: {
          operationId: String(binding.operationId ?? ""),
          params: (binding.params as ComunicadoDataBinding["params"]) ?? {},
          displayMode: binding.displayMode ?? "auto",
          label: binding.label,
          valueField: binding.valueField,
          maxRows: binding.maxRows,
          refreshSec: binding.refreshSec,
        },
        resolved:
          block.resolved && typeof block.resolved === "object"
            ? (block.resolved as ComunicadoDataResolved)
            : undefined,
      } as ComunicadoBlock,
      block,
    );
  }
  if (type === "chart_view") {
    const chartType = typeof block.chartType === "string" ? (block.chartType as ComunicadoChartType) : "line";
    const chartOptions =
      block.chartOptions && typeof block.chartOptions === "object"
        ? ({ ...DEFAULT_COMUNICADO_CHART_OPTIONS, ...(block.chartOptions as ComunicadoChartOptions) })
        : { ...DEFAULT_COMUNICADO_CHART_OPTIONS };
    const rawParts =
      block.chartParts && typeof block.chartParts === "object"
        ? (block.chartParts as ComunicadoChartPartsMap)
        : undefined;
    const chartParts = normalizeChartPartsForLoad(rawParts, chartOptions);
    return attachBlockAnimations(
      {
        id,
        type: "chart_view",
        frame,
        style: { ...defaultStyle("chart_view"), ...style },
        groupId,
        chartType,
        chartOptions,
        chartParts,
        dataSourceId: typeof block.dataSourceId === "string" ? block.dataSourceId : undefined,
        resolved:
          block.resolved && typeof block.resolved === "object"
            ? (block.resolved as ComunicadoDataResolved)
            : undefined,
      } as ComunicadoBlock,
      block,
    );
  }
  if (type === "table_view") {
    const tablePreset =
      typeof block.tablePreset === "string" ? (block.tablePreset as ComunicadoTablePreset) : "grid";
    const tableOptions =
      block.tableOptions && typeof block.tableOptions === "object"
        ? (block.tableOptions as ComunicadoTableOptions)
        : undefined;
    const rawParts =
      block.tableParts && typeof block.tableParts === "object"
        ? (block.tableParts as ComunicadoTablePartsMap)
        : undefined;
    const tableParts = normalizeTablePartsForLoad(rawParts, tableOptions, style);
    return attachBlockAnimations(
      {
        id,
        type: "table_view",
        frame,
        style: { ...defaultStyle("table_view"), ...style, borderRadius: style.borderRadius ?? 0 },
        groupId,
        tablePreset,
        tableOptions,
        tableParts,
        dataSourceId: typeof block.dataSourceId === "string" ? block.dataSourceId : undefined,
        maxRows: normalizeTableViewLimit(block.maxRows, TABLE_VIEW_MAX_ROWS_CAP),
        maxCols: normalizeTableViewLimit(block.maxCols, TABLE_VIEW_MAX_COLS_CAP),
        resolved:
          block.resolved && typeof block.resolved === "object"
            ? (block.resolved as ComunicadoDataResolved)
            : undefined,
      } as ComunicadoBlock,
      block,
    );
  }
  if (type === "canvas_table") {
    const rows = clampCanvasTableDimension(
      block.rows,
      CANVAS_TABLE_MIN_ROWS,
      CANVAS_TABLE_MAX_ROWS,
      3,
    );
    const cols = clampCanvasTableDimension(
      block.cols,
      CANVAS_TABLE_MIN_COLS,
      CANVAS_TABLE_MAX_COLS,
      3,
    );
    return attachBlockAnimations(
      {
        id,
        type: "canvas_table",
        frame,
        style: { ...defaultStyle("canvas_table"), ...style },
        groupId,
        rows,
        cols,
        cells: normalizeCanvasTableCells(block.cells, rows, cols),
        headerRow: block.headerRow !== false,
      },
      block,
    );
  }
  if (type === "kpi_view") {
    const baseOptions =
      block.kpiOptions && typeof block.kpiOptions === "object"
        ? mergeComunicadoKpiOptions(block.kpiOptions as ComunicadoKpiOptions)
        : mergeComunicadoKpiOptions(DEFAULT_COMUNICADO_KPI_OPTIONS);
    const rawParts =
      block.kpiParts && typeof block.kpiParts === "object"
        ? (block.kpiParts as ComunicadoKpiPartsMap)
        : undefined;
    const kpiParts = normalizeKpiPartsForLoad(rawParts, baseOptions);
    // Parts mandam na visibilidade (evita ícone Gauge «fantasma» quando options
    // ainda dizem showIcon:true após o gestor ocultar a parte no editor).
    const kpiOptions = mergeComunicadoKpiOptions({
      ...baseOptions,
      ...partsToKpiOptions(kpiParts),
    });
    return attachBlockAnimations(
      {
        id,
        type: "kpi_view",
        frame,
        style: { ...defaultStyle("kpi_view"), ...style },
        groupId,
        dataSourceId: typeof block.dataSourceId === "string" ? block.dataSourceId : undefined,
        kpiOptions,
        kpiParts,
        resolved:
          block.resolved && typeof block.resolved === "object"
            ? (block.resolved as ComunicadoDataResolved)
            : undefined,
      } as ComunicadoBlock,
      block,
    );
  }
  if (type === "image" || type === "video") {
    return attachBlockAnimations(
      {
        id,
        type,
        frame,
        style,
        groupId,
        assetId: typeof block.assetId === "string" ? block.assetId : undefined,
        url: typeof block.url === "string" ? block.url : undefined,
        href: links.href,
        linkTarget: links.linkTarget,
        ...(type === "image"
          ? { imageCrop: normalizeComunicadoImageCrop(block.imageCrop) }
          : {}),
      },
      block,
    );
  }
  return createBlock("text", "");
}

function isShapeKind(value: string): value is ComunicadoShapeKind {
  return isComunicadoShapeKind(value);
}

function normalizeFrame(value: unknown, type: ComunicadoBlock["type"]): ComunicadoFrame {
  if (!value || typeof value !== "object") return defaultFrame(type);
  const frame = value as Record<string, unknown>;
  const num = (key: keyof ComunicadoFrame, fallback: number) => {
    const raw = frame[key];
    const parsed = typeof raw === "number" ? raw : Number(raw);
    return Number.isFinite(parsed) ? parsed : fallback;
  };
  return {
    x: Math.max(0, Math.min(100, num("x", 5))),
    y: Math.max(0, Math.min(100, num("y", 10))),
    w: Math.max(2, Math.min(100, num("w", 90))),
    h: Math.max(1, Math.min(100, num("h", 20))),
  };
}

export function frameStyle(frame: ComunicadoFrame): CSSProperties {
  return {
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: `${frame.w}%`,
    height: `${frame.h}%`,
  };
}

export { comunicadoVerticalAlignToJustifyContent } from "./comunicadoVisualBox";

export function defaultVerticalAlignForBlock(type: "heading" | "text"): ComunicadoVerticalAlign {
  return defaultVerticalAlignForVisualBox({ id: "", type, content: "", frame: { x: 0, y: 0, w: 1, h: 1 } });
}

export function defaultTextBlockStyle(type: "heading" | "text"): ComunicadoBlockStyle {
  return { ...(defaultStyle(type) as ComunicadoBlockStyle) };
}

export function clampFontSize(size: number): number {
  return Math.max(
    COMUNICADO_FONT_SIZE_MIN,
    Math.min(COMUNICADO_FONT_SIZE_MAX, Math.round(size)),
  );
}

export function parseTextDecorationFlags(
  value?: ComunicadoTextDecoration,
): { underline: boolean; strikethrough: boolean } {
  return {
    underline: value?.includes("underline") ?? false,
    strikethrough: value?.includes("line-through") ?? false,
  };
}

export function buildTextDecoration(
  underline: boolean,
  strikethrough: boolean,
): ComunicadoTextDecoration {
  if (underline && strikethrough) return "underline line-through";
  if (underline) return "underline";
  if (strikethrough) return "line-through";
  return "none";
}

export function comunicadoTextInnerStyle(
  block: Extract<ComunicadoBlock, { type: "heading" } | { type: "text" }>,
  options?: { fontScale?: number },
): CSSProperties {
  const fontScale = options?.fontScale ?? 1;
  const style = block.style ?? {};
  const css: CSSProperties = {};

  if (style.lineHeight != null) css.lineHeight = style.lineHeight;
  if (style.letterSpacing != null) css.letterSpacing = `${style.letterSpacing}px`;
  if (style.textHighlight) css.backgroundColor = style.textHighlight;
  if (style.textDecoration) css.textDecoration = style.textDecoration;
  if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
  const paintColor = resolvePaintTextColor(style.color, style.backgroundColor ?? style.fill ?? "#ffffff", {
    unsetIsAutomatic: false,
  });
  if (paintColor) css.color = paintColor;
  else if (style.color && style.color !== "auto") css.color = style.color;
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.fontWeight) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;

  return css;
}

function applySharedBlockVisualStyle(
  style: NonNullable<ComunicadoBlock["style"]>,
  css: CSSProperties,
  fontScale = 1,
) {
  if (style.backgroundColor) css.backgroundColor = style.backgroundColor;
  if (style.borderWidth != null && style.borderWidth > 0 && (style.borderColor || style.stroke)) {
    css.border = `${style.borderWidth * fontScale}px solid ${style.borderColor ?? style.stroke}`;
  } else if (style.strokeWidth != null && style.strokeWidth > 0 && style.stroke) {
    css.border = `${style.strokeWidth * fontScale}px solid ${style.stroke}`;
  }
  if (style.borderRadius != null) css.borderRadius = style.borderRadius * fontScale;
  if (style.boxShadow) css.boxShadow = style.boxShadow;
}

/** Remove chrome de moldura do wrapper quando o gráfico/card interno já desenha borda/fill. */
function stripOuterChromeStyle(css: CSSProperties) {
  delete css.backgroundColor;
  delete css.border;
  delete css.borderColor;
  delete css.borderWidth;
  delete css.borderStyle;
  delete css.borderRadius;
}

/**
 * KPI/chart/tabela: sombra na moldura interna (já com fill + radius), não no wrapper.
 * Wrapper retangular + box-shadow cria “placa” extra e ignora o raio do card.
 */
function promoteBlockShadowToInnerChrome(
  css: CSSProperties,
  style: NonNullable<ComunicadoBlock["style"]>,
) {
  const shadow = typeof style.boxShadow === "string" ? style.boxShadow.trim() : "";
  if (!shadow) {
    delete css.boxShadow;
    return;
  }
  (css as CSSProperties & Record<string, string>)["--tdp-block-box-shadow"] = shadow;
  delete css.boxShadow;
}

export function blockCssStyle(block: ComunicadoBlock, options?: { fontScale?: number }): CSSProperties {
  const fontScale = options?.fontScale ?? 1;
  const style = block.style ?? {};
  const placement = resolveBlockPlacementStyle(block);
  const css: CSSProperties = {
    ...placement,
    zIndex: style.zIndex ?? 1,
    opacity: style.opacity ?? 1,
  };
  if (style.rotation) {
    // Ponto: placement já é bbox (não centro com translate); só rotaciona no próprio box.
    css.transform = `rotate(${style.rotation}deg)`;
  }
  applySharedBlockVisualStyle(style, css, fontScale);

  if (isComunicadoVisualBoxBlock(block)) {
    const profile = resolveVisualBoxProfile(block);
    if (profile.mode === "text") {
      css.display = "flex";
      css.flexDirection = "column";
      css.alignItems = "stretch";
      const verticalAlign = style.verticalAlign ?? defaultVerticalAlignForVisualBox(block);
      css.justifyContent = comunicadoVerticalAlignToJustifyContent(verticalAlign);
      if (style.textAlign) css.textAlign = style.textAlign;
      if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
      const textPaint = resolvePaintTextColor(
        style.color,
        style.backgroundColor ?? style.fill ?? "#ffffff",
        { unsetIsAutomatic: false },
      );
      if (textPaint) css.color = textPaint;
      else if (style.color && style.color !== "auto") css.color = style.color;
      if (style.fontFamily) css.fontFamily = style.fontFamily;
      if (style.fontWeight) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;
  if (style.lineHeight != null) css.lineHeight = style.lineHeight;
  applyComunicadoTextEffectsToCss(style, css);
  return css;
    }

    /* Forma: fill/stroke/radius só no ComunicadoShapeGraphic — evita borda dupla no wrapper. */
    stripOuterChromeStyle(css);
    if (block.content) {
      if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
      const shapeFill = style.fill ?? DECK_SHAPE_DEFAULTS.fill;
      css.color = resolvePaintTextColor(style.color, shapeFill) ?? DECK_COLOR_TEXT_STRONG;
      if (style.fontFamily) css.fontFamily = style.fontFamily;
      if (style.textAlign) css.textAlign = style.textAlign;
      if (style.fontWeight) css.fontWeight = style.fontWeight;
      if (style.fontStyle) css.fontStyle = style.fontStyle;
      if (style.textDecoration) css.textDecoration = style.textDecoration;
      applyComunicadoTextEffectsToCss(style, css);
    }
    return css;
  }

  if (block.type === "icon") {
    css.display = "flex";
    css.alignItems = "center";
    css.justifyContent = "center";
    if (style.color) css.color = style.color;
  }

  /* KPI/chart/tabela: moldura no componente interno (DelpiKpiCard / chart / table). */
  if (block.type === "kpi_view" || block.type === "chart_view" || block.type === "table_view") {
    stripOuterChromeStyle(css);
    promoteBlockShadowToInnerChrome(css, style);
  }

  return css;
}

export function sortBlocksByZIndex(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  return [...blocks].sort((a, b) => (a.style?.zIndex ?? 1) - (b.style?.zIndex ?? 1));
}

export function hasRichComunicado(data: ComunicadoScreenDataLike): boolean {
  // Array presente (mesmo vazio) = layout de compositor WYSIWYG.
  // Sem `blocks` = legado headline/subtitle (`tdp-message`).
  return Array.isArray(data.blocks);
}

export type ComunicadoScreenDataLike = {
  blocks?: ComunicadoBlock[];
  headline?: string;
  subtitle?: string;
  customFonts?: ComunicadoCustomFontRef[];
};

export function clampFrame(frame: ComunicadoFrame): ComunicadoFrame {
  return {
    x: Math.max(0, Math.min(100 - frame.w, frame.x)),
    y: Math.max(0, Math.min(100 - frame.h, frame.y)),
    w: Math.max(2, Math.min(100, frame.w)),
    h: Math.max(1, Math.min(100, frame.h)),
  };
}

export function nextZIndex(blocks: ComunicadoBlock[]): number {
  const max = blocks.reduce((acc, block) => Math.max(acc, block.style?.zIndex ?? 1), 0);
  return max + 1;
}
