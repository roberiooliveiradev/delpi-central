import type { PlaylistSection, Slide } from "../api/tvDashboardApi";

export type SlidesBySection = {
  unsectioned: Slide[];
  sections: Array<{ section: PlaylistSection; slides: Slide[] }>;
};

/** Agrupa slides pela seção (ordem das seções + sortOrder dos slides). */
export function groupSlidesBySection(
  slides: Slide[],
  sections: PlaylistSection[],
): SlidesBySection {
  const orderedSections = [...sections].sort((a, b) => a.sortOrder - b.sortOrder);
  const byId = new Map(orderedSections.map((section) => [section.id, [] as Slide[]]));
  const unsectioned: Slide[] = [];
  const sortedSlides = [...slides].sort((a, b) => a.sortOrder - b.sortOrder);
  for (const slide of sortedSlides) {
    const sectionId = slide.sectionId?.trim();
    if (sectionId && byId.has(sectionId)) {
      byId.get(sectionId)!.push(slide);
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
