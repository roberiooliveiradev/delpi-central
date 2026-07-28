import type { Slide } from "../api/tvDashboardApi";

/**
 * Reordena slides movendo `slideId` para o fim do bloco da seção alvo
 * (ou para o fim do bucket sem seção quando `sectionId` é null).
 * Retorna a lista com `sectionId` e `sortOrder` atualizados.
 */
export function assignSlideToSectionOrder(
  slides: Slide[],
  slideId: string,
  sectionId: string | null,
): Slide[] {
  const ordered = [...slides].sort((a, b) => a.sortOrder - b.sortOrder);
  const moving = ordered.find((slide) => slide.id === slideId);
  if (!moving) return ordered;

  const without = ordered.filter((slide) => slide.id !== slideId);
  const updated: Slide = { ...moving, sectionId };

  const sameSection = without.filter((slide) => (slide.sectionId ?? null) === sectionId);
  const other = without.filter((slide) => (slide.sectionId ?? null) !== sectionId);

  if (sameSection.length === 0) {
    // Sem peers: coloca no fim da playlist.
    return [...other, updated].map((slide, sortOrder) => ({ ...slide, sortOrder }));
  }

  const lastPeer = sameSection[sameSection.length - 1]!;
  const insertAfterGlobal = without.findIndex((slide) => slide.id === lastPeer.id);
  const next = [...without];
  next.splice(insertAfterGlobal + 1, 0, updated);
  return next.map((slide, sortOrder) => ({ ...slide, sortOrder }));
}
