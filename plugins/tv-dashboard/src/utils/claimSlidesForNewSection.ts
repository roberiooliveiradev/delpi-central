import type { PlaylistSection, Slide } from "../api/tvDashboardApi";

export type ClaimSlidesForNewSectionResult = {
  beforeIds: string[];
  claimIds: string[];
  /** Seção atual do âncora (null se órfão / sem seção). */
  anchorSectionId: string | null;
};

/**
 * Define o intervalo engolido ao criar seção a partir de um slide:
 * âncora + seguintes até (exclusive) o primeiro slide de outra seção
 * já existente, ou o fim da playlist.
 */
export function claimSlidesForNewSection(
  slides: Slide[],
  _sections: PlaylistSection[],
  anchorSlideId: string,
): ClaimSlidesForNewSectionResult {
  const ordered = [...slides].sort((a, b) => a.sortOrder - b.sortOrder);
  const anchorIndex = ordered.findIndex((slide) => slide.id === anchorSlideId);
  if (anchorIndex < 0) {
    return { beforeIds: [], claimIds: [], anchorSectionId: null };
  }

  const anchor = ordered[anchorIndex]!;
  const anchorSectionId = anchor.sectionId?.trim() || null;
  const beforeIds = ordered.slice(0, anchorIndex).map((slide) => slide.id);
  const claimIds: string[] = [];

  for (let i = anchorIndex; i < ordered.length; i += 1) {
    const slide = ordered[i]!;
    const sectionId = slide.sectionId?.trim() || null;
    if (i > anchorIndex && sectionId !== anchorSectionId) {
      // Outra seção já existente — para antes dela.
      if (sectionId != null) break;
      // Órfão após âncora com seção: ainda engole até achar seção distinta.
      if (anchorSectionId != null && sectionId == null) {
        claimIds.push(slide.id);
        continue;
      }
    }
    claimIds.push(slide.id);
  }

  return { beforeIds, claimIds, anchorSectionId };
}
