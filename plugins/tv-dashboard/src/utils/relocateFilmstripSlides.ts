import type { Slide } from "../api/tvDashboardApi";

export type FilmstripRelocateTarget =
  | { kind: "index"; targetIndex: number; edge?: "before" | "after" }
  | { kind: "section"; sectionId: string | null };

/**
 * Move um ou mais slides (ordem flat) para um índice-alvo ou para o fim de uma seção.
 * Preserva a ordem relativa dos slides movidos.
 */
export function relocateFilmstripSlides(
  slides: Slide[],
  movingIds: readonly string[],
  target: FilmstripRelocateTarget,
): Slide[] {
  const ordered = [...slides].sort((a, b) => a.sortOrder - b.sortOrder);
  const movingIdSet = new Set(movingIds);
  const moving = ordered.filter((slide) => movingIdSet.has(slide.id));
  if (moving.length === 0) return ordered;

  const remaining = ordered.filter((slide) => !movingIdSet.has(slide.id));

  if (target.kind === "section") {
    const sectionId = target.sectionId;
    const updatedMoving = moving.map((slide) => ({ ...slide, sectionId }));
    const sameSection = remaining.filter((slide) => (slide.sectionId ?? null) === sectionId);
    if (sameSection.length === 0) {
      return [...remaining, ...updatedMoving].map((slide, sortOrder) => ({
        ...slide,
        sortOrder,
      }));
    }
    const lastPeer = sameSection[sameSection.length - 1]!;
    const insertAfter = remaining.findIndex((slide) => slide.id === lastPeer.id);
    const next = [...remaining];
    next.splice(insertAfter + 1, 0, ...updatedMoving);
    return next.map((slide, sortOrder) => ({ ...slide, sortOrder }));
  }

  const { targetIndex } = target;
  if (targetIndex < 0 || targetIndex >= ordered.length) {
    return ordered;
  }

  const targetSlide = ordered[targetIndex]!;
  // Soltar sobre um item do próprio bloco movido = no-op.
  if (movingIdSet.has(targetSlide.id)) {
    return ordered.map((slide, sortOrder) => ({ ...slide, sortOrder }));
  }

  const sectionId = targetSlide.sectionId ?? null;
  const updatedMoving = moving.map((slide) => ({ ...slide, sectionId }));
  const insertAt = remaining.findIndex((slide) => slide.id === targetSlide.id);
  if (insertAt < 0) {
    return ordered.map((slide, sortOrder) => ({ ...slide, sortOrder }));
  }
  const next = [...remaining];
  const spliceAt = target.edge === "after" ? insertAt + 1 : insertAt;
  next.splice(spliceAt, 0, ...updatedMoving);
  return next.map((slide, sortOrder) => ({ ...slide, sortOrder }));
}
