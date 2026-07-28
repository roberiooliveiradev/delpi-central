import type { PlaylistSection, Slide } from "../api/tvDashboardApi";

export type SlidesBySection = {
  unsectioned: Slide[];
  sections: Array<{ section: PlaylistSection; slides: Slide[] }>;
};

/** Agrupa slides pela seção (ordem das seções + sortOrder dos slides).
 * Órfãos (sectionId null) caem na Principal quando ela existe. */
export function groupSlidesBySection(
  slides: Slide[],
  sections: PlaylistSection[],
): SlidesBySection {
  const orderedSections = [...sections].sort((a, b) => a.sortOrder - b.sortOrder);
  const byId = new Map(orderedSections.map((section) => [section.id, [] as Slide[]]));
  const main = orderedSections.find((section) => section.isMain);
  const unsectioned: Slide[] = [];
  const sortedSlides = [...slides].sort((a, b) => a.sortOrder - b.sortOrder);
  for (const slide of sortedSlides) {
    const sectionId = slide.sectionId?.trim();
    if (sectionId && byId.has(sectionId)) {
      byId.get(sectionId)!.push(slide);
    } else if (main) {
      byId.get(main.id)!.push(slide);
    } else {
      unsectioned.push(slide);
    }
  }
  return {
    unsectioned,
    sections: orderedSections.map((section) => ({
      section,
      slides: byId.get(section.id) ?? [],
    })),
  };
}
