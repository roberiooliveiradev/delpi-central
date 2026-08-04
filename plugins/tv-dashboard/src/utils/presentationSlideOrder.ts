import type { PlaylistSection, Slide } from "../api/tvDashboardApi";

/**
 * Espelha `is_slide_visible_in_presentation` (tv-dashboard-api).
 * Present omite slides/seções pausados — o filmstrip deve numerar na mesma ordem.
 */
export function isSlideVisibleInPresentation(
  slide: Pick<Slide, "isActive">,
  section: Pick<PlaylistSection, "isActive"> | null | undefined,
): boolean {
  if (slide.isActive === false) return false;
  if (section != null && section.isActive === false) return false;
  return true;
}

/** Slides na ordem da TV (sortOrder), só os que entram no `/present/`. */
export function listPresentationOrderedSlides(
  slides: Slide[],
  sections: PlaylistSection[],
): Slide[] {
  const sectionById = new Map(sections.map((section) => [section.id, section]));
  return [...slides]
    .sort((a, b) => a.sortOrder - b.sortOrder)
    .filter((slide) => {
      const section = slide.sectionId ? sectionById.get(slide.sectionId) : undefined;
      return isSlideVisibleInPresentation(slide, section);
    });
}

/**
 * Índice 0-based na sequência da TV (badge «Ordem na TV»).
 * Slides pausados / seção inativa não entram no mapa.
 */
export function buildPresentationOrderIndexBySlideId(
  slides: Slide[],
  sections: PlaylistSection[],
): Map<string, number> {
  const map = new Map<string, number>();
  listPresentationOrderedSlides(slides, sections).forEach((slide, index) => {
    map.set(slide.id, index);
  });
  return map;
}
