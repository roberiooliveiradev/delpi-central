/**
 * Insere `newSlide` imediatamente após o slide âncora.
 * Sem âncora (ou id inexistente) → final da lista.
 */
export function insertSlideAfterAnchor<T extends { id: string }>(
  slides: T[],
  newSlide: T,
  anchorId?: string | null,
): T[] {
  const withoutNew = slides.filter((slide) => slide.id !== newSlide.id);
  const anchorIndex =
    typeof anchorId === "string" && anchorId.trim()
      ? withoutNew.findIndex((slide) => slide.id === anchorId)
      : -1;
  const insertIndex = anchorIndex >= 0 ? anchorIndex + 1 : withoutNew.length;
  const next = [...withoutNew];
  next.splice(insertIndex, 0, newSlide);
  return next;
}
