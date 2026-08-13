/**
 * Reordenação visual de colunas do DataTable (HTML5 DnD + fantasma da coluna).
 */

export type ColumnDropEdge = "before" | "after";

export function reorderColumnKeys(keys: string[], fromKey: string, toKey: string): string[] {
  if (fromKey === toKey) return keys;
  const from = keys.indexOf(fromKey);
  const to = keys.indexOf(toKey);
  if (from < 0 || to < 0) return keys;
  const next = [...keys];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved!);
  return next;
}

/** Insere `fromKey` antes/depois de `targetKey` (após remover a origem). */
export function reorderColumnKeysWithEdge(
  keys: string[],
  fromKey: string,
  targetKey: string,
  edge: ColumnDropEdge,
): string[] {
  if (fromKey === targetKey) return keys;
  if (!keys.includes(fromKey) || !keys.includes(targetKey)) return keys;
  const next = keys.filter((key) => key !== fromKey);
  let insertAt = next.indexOf(targetKey);
  if (insertAt < 0) return keys;
  if (edge === "after") insertAt += 1;
  next.splice(insertAt, 0, fromKey);
  return next;
}

export function resolveColumnDropEdge(
  clientX: number,
  headerRect: DOMRect,
): ColumnDropEdge {
  if (!Number.isFinite(clientX)) return "before";
  if (!Number.isFinite(headerRect.width) || headerRect.width <= 0) return "before";
  const mid = headerRect.left + headerRect.width / 2;
  return clientX < mid ? "before" : "after";
}

const GHOST_MAX_BODY_ROWS = 8;

function escapeColumnKeySelector(columnKey: string): string {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(columnKey);
  }
  return columnKey.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

/**
 * Monta um fantasma da coluna (header + células) para setDragImage.
 * Retorna o nó anexado ao body — remover no dragend.
 */
export function createColumnDragGhost(
  table: HTMLTableElement,
  columnKey: string,
): HTMLElement | null {
  const cells = Array.from(
    table.querySelectorAll<HTMLElement>(
      `[data-column-key="${escapeColumnKeySelector(columnKey)}"]`,
    ),
  );
  if (cells.length === 0) return null;

  const width = Math.max(
    ...cells.slice(0, GHOST_MAX_BODY_ROWS + 1).map((cell) => cell.getBoundingClientRect().width),
    120,
  );

  const ghost = document.createElement("div");
  ghost.className = "delpi-ui-table__column-drag-ghost";
  ghost.setAttribute("aria-hidden", "true");
  ghost.style.width = `${Math.round(width)}px`;

  const slice = cells.slice(0, GHOST_MAX_BODY_ROWS + 1);
  for (const cell of slice) {
    const row = document.createElement("div");
    row.className =
      cell.tagName === "TH"
        ? "delpi-ui-table__column-drag-ghost__header"
        : "delpi-ui-table__column-drag-ghost__cell";
    row.textContent = (cell.innerText || cell.textContent || "").trim() || "—";
    ghost.appendChild(row);
  }

  if (cells.length > slice.length) {
    const more = document.createElement("div");
    more.className = "delpi-ui-table__column-drag-ghost__more";
    more.textContent = `+${cells.length - slice.length}`;
    ghost.appendChild(more);
  }

  Object.assign(ghost.style, {
    position: "fixed",
    top: "-10000px",
    left: "-10000px",
    pointerEvents: "none",
    zIndex: "9999",
  } as CSSStyleDeclaration);

  document.body.appendChild(ghost);
  return ghost;
}

export function disposeColumnDragGhost(ghost: HTMLElement | null | undefined): void {
  ghost?.remove();
}
