/**
 * Reordenação visual de colunas do DataTable (HTML5 DnD).
 * Sem fantasma da coluna — só highlight in-place + indicador de soltura.
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

/**
 * Substitui a miniatura nativa do browser por imagem transparente (1×1).
 * Evita o fantasma da coluna flutuando sobre a tabela.
 */
export function applyTransparentColumnDragImage(dataTransfer: DataTransfer): void {
  if (typeof document === "undefined") return;
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  try {
    dataTransfer.setDragImage(canvas, 0, 0);
  } catch {
    /* alguns ambientes de teste não implementam setDragImage */
  }
}
