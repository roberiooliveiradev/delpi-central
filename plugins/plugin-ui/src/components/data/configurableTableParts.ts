/**
 * Onda 4G.8 — partes endereçáveis de `table_view` (mesmo padrão de ChartPartRef).
 */

import type { MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from "react";

import { DECK_TABLE_DEFAULTS } from "../../theme/deckColorCatalog";
import type { ConfigurableTableOptions } from "./configurableTableOptions";
import { mergeConfigurableTableOptions } from "./configurableTableOptions";
import type { ConfigurableTableElementId } from "./configurableTableElementCatalog";

export const TABLE_PART_DATA_ATTR = "data-table-part";

export type TablePartRef =
  | { kind: "frame" }
  | { kind: "title" }
  | { kind: "header" }
  | { kind: "headerCell"; colIndex: number }
  | { kind: "cell"; rowIndex: number; colIndex: number };

export type TablePartStyle = {
  fill?: string;
  color?: string;
  fontWeight?: string | number;
  /** Contorno da moldura (parte `frame`). */
  stroke?: string;
  strokeWidth?: number;
  /** Cantos da moldura (px). */
  borderRadius?: number;
};

export type TablePartState = {
  visible?: boolean;
  style?: TablePartStyle;
  content?: string;
};

export type TablePartsMap = Record<string, TablePartState>;

export type TableInteraction = {
  selectedPart?: TablePartRef | null;
  editingPart?: TablePartRef | null;
  onPartPointerDown?: (ref: TablePartRef, event: ReactPointerEvent) => void;
  onPartDoubleClick?: (ref: TablePartRef, event: ReactPointerEvent | ReactMouseEvent) => void;
  onPartContentCommit?: (ref: TablePartRef, content: string) => void;
  onPartEditCancel?: () => void;
};

export type TablePartCapabilities = {
  movable: boolean;
  editable: boolean;
  deletable: boolean;
  resizable: boolean;
};

const TABLE_PART_KIND_CAPABILITIES: Record<TablePartRef["kind"], TablePartCapabilities> = {
  frame: { movable: false, editable: false, deletable: false, resizable: false },
  title: { movable: false, editable: true, deletable: true, resizable: false },
  header: { movable: false, editable: false, deletable: true, resizable: false },
  headerCell: { movable: false, editable: true, deletable: false, resizable: false },
  cell: { movable: false, editable: false, deletable: false, resizable: false },
};

export function serializeTablePartRef(ref: TablePartRef): string {
  switch (ref.kind) {
    case "frame":
      return "frame";
    case "title":
      return "title";
    case "header":
      return "header";
    case "headerCell":
      return `headerCell:${ref.colIndex}`;
    case "cell":
      return `cell:${ref.rowIndex}:${ref.colIndex}`;
    default: {
      const _exhaustive: never = ref;
      return String(_exhaustive);
    }
  }
}

export function parseTablePartRef(raw: string | null | undefined): TablePartRef | null {
  const value = (raw ?? "").trim();
  if (!value) return null;
  if (value === "frame") return { kind: "frame" };
  if (value === "title") return { kind: "title" };
  if (value === "header") return { kind: "header" };
  const headerCell = /^headerCell:(\d+)$/.exec(value);
  if (headerCell) return { kind: "headerCell", colIndex: Number(headerCell[1]) };
  const cell = /^cell:(\d+):(\d+)$/.exec(value);
  if (cell) return { kind: "cell", rowIndex: Number(cell[1]), colIndex: Number(cell[2]) };
  return null;
}

export function isTablePartRefEqual(a?: TablePartRef | null, b?: TablePartRef | null): boolean {
  if (!a || !b) return false;
  return serializeTablePartRef(a) === serializeTablePartRef(b);
}

export function tablePartCapabilities(ref: TablePartRef): TablePartCapabilities {
  return TABLE_PART_KIND_CAPABILITIES[ref.kind];
}

export function tablePartAllowsDelete(ref: TablePartRef): boolean {
  return tablePartCapabilities(ref).deletable;
}

export function tablePartAllowsEdit(ref: TablePartRef): boolean {
  return tablePartCapabilities(ref).editable;
}

export function getTablePartState(
  parts: TablePartsMap | null | undefined,
  ref: TablePartRef,
): TablePartState | undefined {
  return parts?.[serializeTablePartRef(ref)];
}

export function upsertTablePartState(
  parts: TablePartsMap | null | undefined,
  ref: TablePartRef,
  patch: TablePartState,
): TablePartsMap {
  const key = serializeTablePartRef(ref);
  const prev = parts?.[key] ?? {};
  return {
    ...(parts ?? {}),
    [key]: {
      ...prev,
      ...patch,
      style: patch.style ? { ...prev.style, ...patch.style } : prev.style,
    },
  };
}

export function tablePartDomProps(ref: TablePartRef, selectedPart?: TablePartRef | null) {
  const selected = isTablePartRefEqual(ref, selectedPart);
  return {
    [TABLE_PART_DATA_ATTR]: serializeTablePartRef(ref),
    "aria-selected": selected ? true : undefined,
  };
}

export function bindTablePartPointer(ref: TablePartRef, interaction?: TableInteraction | null) {
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const selected = isTablePartRefEqual(ref, interaction?.selectedPart);
  const editing = isTablePartRefEqual(ref, interaction?.editingPart);
  const dom = tablePartDomProps(ref, interaction?.selectedPart);

  if (!interactive) {
    return {
      ...dom,
      selected,
      editing,
      onPointerDown: undefined as undefined,
      onDoubleClick: undefined as undefined,
    };
  }

  return {
    ...dom,
    selected,
    editing,
    onPointerDown: (event: ReactPointerEvent) => {
      event.stopPropagation();
      interaction?.onPartPointerDown?.(ref, event);
    },
    onDoubleClick: (event: ReactMouseEvent) => {
      event.stopPropagation();
      event.preventDefault();
      interaction?.onPartDoubleClick?.(ref, event);
    },
  };
}

export function findTablePartFromTarget(target: EventTarget | null): TablePartRef | null {
  if (!(target instanceof Element)) return null;
  const host = target.closest(`[${TABLE_PART_DATA_ATTR}]`);
  if (!host) return null;
  return parseTablePartRef(host.getAttribute(TABLE_PART_DATA_ATTR));
}

/** Projeta options flat → parts (moldura + título/cabeçalho). */
export function tableOptionsToParts(
  options?: ConfigurableTableOptions | null,
): TablePartsMap {
  const config = mergeConfigurableTableOptions(options);
  return {
    frame: {
      visible: true,
      style: {
        fill: DECK_TABLE_DEFAULTS.frameFill,
        stroke: DECK_TABLE_DEFAULTS.frameStroke,
        strokeWidth: 1,
        borderRadius: 0,
      },
    },
    title: { visible: config.showTitle !== false, content: config.title },
    header: { visible: config.showHeader !== false },
  };
}

/** Projeta parts → patch de options flat. */
export function partsToTableOptions(parts?: TablePartsMap | null): Partial<ConfigurableTableOptions> {
  if (!parts) return {};
  const title = parts.title;
  const header = parts.header;
  const patch: Partial<ConfigurableTableOptions> = {};
  if (title?.visible != null) patch.showTitle = title.visible !== false;
  if (title?.content != null) patch.title = title.content;
  if (header?.visible != null) patch.showHeader = header.visible !== false;
  return patch;
}

export function mergeTablePartsWithOptions(
  parts: TablePartsMap | null | undefined,
  options?: ConfigurableTableOptions | null,
): TablePartsMap {
  const fromOptions = tableOptionsToParts(options);
  const merged: TablePartsMap = { ...fromOptions };
  for (const [key, state] of Object.entries(parts ?? {})) {
    merged[key] = {
      ...fromOptions[key],
      ...state,
      style: { ...fromOptions[key]?.style, ...state.style },
    };
  }
  return merged;
}

/** Format Table Area (Excel) — preenchimento + contorno + cantos da moldura. */
export function resolveTableFrameStyle(
  parts?: TablePartsMap | null,
): { fill: string; stroke: string; strokeWidth: number; borderRadius: number } {
  const merged = mergeTablePartsWithOptions(parts);
  const frame = getTablePartState(merged, { kind: "frame" });
  return {
    fill: frame?.style?.fill ?? DECK_TABLE_DEFAULTS.frameFill,
    stroke: frame?.style?.stroke ?? DECK_TABLE_DEFAULTS.frameStroke,
    strokeWidth: frame?.style?.strokeWidth ?? 1,
    borderRadius: frame?.style?.borderRadius ?? 0,
  };
}

type LegacyTableChromeStyle = {
  fill?: string;
  backgroundColor?: string;
  stroke?: string;
  borderColor?: string;
  strokeWidth?: number;
  borderWidth?: number;
  borderRadius?: number;
} | null | undefined;

/**
 * Migra chrome legado em `block.style` para `tableParts.frame` (Onda 4O.A).
 * Só preenche campos ainda ausentes na parte `frame` explícita do payload.
 */
export function migrateLegacyTableChromeToFrame(
  parts: TablePartsMap | null | undefined,
  style?: LegacyTableChromeStyle,
): TablePartsMap {
  const rawFrameStyle = parts?.frame?.style;
  const merged = mergeTablePartsWithOptions(parts);
  if (!style) return merged;
  const legacyFill = style.backgroundColor ?? style.fill;
  const legacyStroke = style.borderColor ?? style.stroke;
  const legacyWidth = style.borderWidth ?? style.strokeWidth;
  const legacyRadius = style.borderRadius;
  const hasLegacy =
    legacyFill != null || legacyStroke != null || legacyWidth != null || legacyRadius != null;
  if (!hasLegacy) return merged;
  return upsertTablePartState(merged, { kind: "frame" }, {
    style: {
      fill: rawFrameStyle?.fill ?? legacyFill ?? merged.frame?.style?.fill,
      stroke: rawFrameStyle?.stroke ?? legacyStroke ?? merged.frame?.style?.stroke,
      strokeWidth: rawFrameStyle?.strokeWidth ?? legacyWidth ?? merged.frame?.style?.strokeWidth,
      borderRadius:
        rawFrameStyle?.borderRadius ?? legacyRadius ?? merged.frame?.style?.borderRadius ?? 0,
    },
  });
}

export function normalizeTablePartsForLoad(
  parts: TablePartsMap | null | undefined,
  options?: ConfigurableTableOptions | null,
  style?: LegacyTableChromeStyle,
): TablePartsMap {
  return migrateLegacyTableChromeToFrame(mergeTablePartsWithOptions(parts, options), style);
}

/** Delete Excel: oculta título/cabeçalho; células só deselecionam no caller. */
export function deleteTablePart(
  parts: TablePartsMap | null | undefined,
  ref: TablePartRef,
  options?: ConfigurableTableOptions | null,
): { parts: TablePartsMap; options: ConfigurableTableOptions } {
  if (ref.kind === "frame") {
    return {
      parts: mergeTablePartsWithOptions(parts, options),
      options: mergeConfigurableTableOptions(options),
    };
  }
  const nextParts = upsertTablePartState(parts, ref, { visible: false });
  const nextOptions = mergeConfigurableTableOptions({
    ...options,
    ...partsToTableOptions(nextParts),
  });
  return { parts: nextParts, options: nextOptions };
}

export function tableElementPrimaryPartRef(
  elementId: ConfigurableTableElementId,
): TablePartRef | null {
  if (elementId === "tableTitle") return { kind: "title" };
  if (elementId === "header") return { kind: "header" };
  return null;
}

/** Estilo de pintura (fundo/texto) de uma parte — usado no render. */
export function resolveTablePartPaintStyle(
  parts: TablePartsMap | null | undefined,
  ref: TablePartRef,
): { backgroundColor?: string; color?: string; fontWeight?: string | number } {
  const style = getTablePartState(parts, ref)?.style;
  if (!style) return {};
  return {
    ...(style.fill != null ? { backgroundColor: style.fill } : {}),
    ...(style.color != null ? { color: style.color } : {}),
    ...(style.fontWeight != null ? { fontWeight: style.fontWeight } : {}),
  };
}

/**
 * Pintura de célula de cabeçalho: `headerCell` sobrescreve `header`.
 */
export function resolveTableHeaderCellPaintStyle(
  parts: TablePartsMap | null | undefined,
  colIndex: number,
): { backgroundColor?: string; color?: string; fontWeight?: string | number } {
  const header = resolveTablePartPaintStyle(parts, { kind: "header" });
  const cell = resolveTablePartPaintStyle(parts, { kind: "headerCell", colIndex });
  return {
    backgroundColor: cell.backgroundColor ?? header.backgroundColor,
    color: cell.color ?? header.color,
    fontWeight: cell.fontWeight ?? header.fontWeight,
  };
}
