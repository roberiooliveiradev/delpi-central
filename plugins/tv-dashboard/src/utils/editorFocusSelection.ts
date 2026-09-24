/**
 * IDs de bloco do canvas para o snapshot `editorFocus` (VISTA).
 * Não confundir com multi-seleção do filmstrip (`selectedSlideIds`).
 */
export function normalizeEditorFocusBlockIds(selectedIds: readonly string[]): string[] {
  const out: string[] = [];
  for (const raw of selectedIds) {
    const id = String(raw ?? "").trim();
    if (id && !out.includes(id)) out.push(id);
    if (out.length >= 100) break;
  }
  return out;
}
