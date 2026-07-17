const MIN_COLUMN_WIDTH_PX = 48;

export type DataTableColumnWidths = Record<string, number>;

export function clampColumnWidthPx(widthPx: number): number {
  return Math.max(MIN_COLUMN_WIDTH_PX, Math.round(widthPx));
}

export function startDataTableColumnResize(options: {
  event: PointerEvent | ReactPointerLike;
  columnKey: string;
  currentWidthPx: number;
  onResize: (columnKey: string, widthPx: number) => void;
}): void {
  const { event, columnKey, currentWidthPx, onResize } = options;
  event.preventDefault();
  event.stopPropagation();

  const startX = event.clientX;
  const startWidth = clampColumnWidthPx(currentWidthPx);

  const handleMove = (moveEvent: PointerEvent) => {
    const delta = moveEvent.clientX - startX;
    onResize(columnKey, clampColumnWidthPx(startWidth + delta));
  };

  const handleUp = () => {
    window.removeEventListener("pointermove", handleMove);
    window.removeEventListener("pointerup", handleUp);
  };

  window.addEventListener("pointermove", handleMove);
  window.addEventListener("pointerup", handleUp);
}

type ReactPointerLike = {
  preventDefault: () => void;
  stopPropagation: () => void;
  clientX: number;
};

function escapeAttrValue(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

/** Mede a largura natural da coluna (header + células) e devolve px. */
export function measureDataTableColumnWidthPx(
  table: HTMLTableElement,
  columnKey: string,
): number | null {
  const cells = table.querySelectorAll<HTMLElement>(
    `[data-column-key="${escapeAttrValue(columnKey)}"]`,
  );
  if (cells.length === 0) return null;

  let maxWidth = 0;
  for (const cell of cells) {
    const previousWidth = cell.style.width;
    const previousWhiteSpace = cell.style.whiteSpace;
    cell.style.width = "auto";
    cell.style.whiteSpace = "nowrap";
    maxWidth = Math.max(maxWidth, cell.scrollWidth);
    cell.style.width = previousWidth;
    cell.style.whiteSpace = previousWhiteSpace;
  }

  return maxWidth > 0 ? clampColumnWidthPx(maxWidth + 16) : null;
}

export function autofitDataTableColumn(options: {
  table: HTMLTableElement | null;
  columnKey: string;
  onResize: (columnKey: string, widthPx: number) => void;
}): void {
  const { table, columnKey, onResize } = options;
  if (!table) return;
  const width = measureDataTableColumnWidthPx(table, columnKey);
  if (width == null) return;
  onResize(columnKey, width);
}
