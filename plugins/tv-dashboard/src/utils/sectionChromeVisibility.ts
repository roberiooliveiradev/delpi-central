import type { PlaylistSection } from "../api/tvDashboardApi";

/** Chrome de seções no filmstrip: oculto se não há seções ou só a Principal. */
export function shouldShowSectionChrome(sections: PlaylistSection[]): boolean {
  if (sections.length === 0) return false;
  if (sections.length === 1 && sections[0]?.isMain) return false;
  return sections.length >= 2;
}

/** Principal vazia não aparece no filmstrip (ainda existe no backend). */
export function shouldShowSectionInFilmstrip(
  section: PlaylistSection,
  slideCount: number,
): boolean {
  if (section.isMain && slideCount <= 0) return false;
  return true;
}

/** Seções listáveis no jump «Ir para seção» (mesma regra do chrome). */
export function sectionsVisibleInJump(sections: PlaylistSection[]): PlaylistSection[] {
  if (!shouldShowSectionChrome(sections)) return [];
  return [...sections].sort((a, b) => a.sortOrder - b.sortOrder);
}
