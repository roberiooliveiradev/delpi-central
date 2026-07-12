/**
 * Onda 4G.8 — partes endereçáveis de `table_view` (mesmo padrão de ChartPartRef).
 */

import type { MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from "react";

import type { ConfigurableTableOptions } from "./configurableTableOptions";
import { mergeConfigurableTableOptions } from "./configurableTableOptions";

export const TABLE_PART_DATA_ATTR = "data-table-part";

export type TablePartRef =
  | { kind: "title" }
  | { kind: "header" }
  | { kind: "headerCell"; colIndex: number }
  | { kind: "cell"; rowIndex: number; colIndex: number };

export type TablePartStyle = {
  fill?: string;
  color?: string;
  fontWeight?: string | number;
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
  title: { movable: false, editable: true, deletable: true, resizable: false },
  header: { movable: false, editable: false, deletable: true, resizable: false },
  headerCell: { movable: false, editable: true, deletable: false, resizable: false },
  cell: { movable: false, editable: false, deletable: false, resizable: false },
};

export function serializeTablePartRef(ref: TablePartRef): string {
  switch (ref.kind) {
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

/** Projeta options flat → parts (título/cabeçalho). */
export function tableOptionsToParts(
  options?: ConfigurableTableOptions | null,
): TablePartsMap {
  const config = mergeConfigurableTableOptions(options);
  return {
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
  return { ...fromOptions, ...(parts ?? {}) };
}

/** Delete Excel: oculta título/cabeçalho; células só deselecionam no caller. */
export function deleteTablePart(
  parts: TablePartsMap | null | undefined,
  ref: TablePartRef,
  options?: ConfigurableTableOptions | null,
): { parts: TablePartsMap; options: ConfigurableTableOptions } {
  const nextParts = upsertTablePartState(parts, ref, { visible: false });
  const nextOptions = mergeConfigurableTableOptions({
    ...options,
    ...partsToTableOptions(nextParts),
  });
  return { parts: nextParts, options: nextOptions };
}

export function tableElementPrimaryPartRef(
  elementId: "tableTitle" | "header" | "borders" | "zebraStripe",
): TablePartRef | null {
  if (elementId === "tableTitle") return { kind: "title" };
  if (elementId === "header") return { kind: "header" };
  return null;
}
