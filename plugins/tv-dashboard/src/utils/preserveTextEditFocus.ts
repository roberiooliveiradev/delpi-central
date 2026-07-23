/**
 * Controles da ribbon/painel que aplicam tipografia na seleção do contentEditable.
 * `mousedown` + `preventDefault` evita blur/perda da seleção (bug: negrito no bloco inteiro).
 */
export const PRESERVE_TEXT_EDIT_FOCUS_ATTR = "data-delpi-preserve-text-edit";

export function shouldPreserveTextEditOnBlur(
  relatedTarget: EventTarget | null | undefined,
): boolean {
  if (!(relatedTarget instanceof Element)) return false;
  return Boolean(relatedTarget.closest(`[${PRESERVE_TEXT_EDIT_FOCUS_ATTR}]`));
}
