/**
 * Alvos de exportação da aba Tela: programação, primária ou seleção do filmstrip.
 * Ordem = sortOrder da playlist (não a ordem do clique).
 */

import type { Slide } from "../api/tvDashboardApi";
import { isCustomMessageSlide } from "./applySlideBatchPatch";

export type ExportSlideScope = "playlist" | "current" | "selected";

export function orderSlidesForExport(
  targets: readonly Slide[],
  playlistSlides: readonly Slide[],
): Slide[] {
  if (targets.length <= 1) return [...targets];
  const ids = new Set(targets.map((slide) => slide.id));
  return playlistSlides.filter((slide) => ids.has(slide.id));
}

export function resolveExportSlideTargets(input: {
  scope: ExportSlideScope;
  slides: readonly Slide[];
  selectedSlides: readonly Slide[];
  primary: Slide | null;
}): Slide[] {
  if (input.scope === "selected") {
    const selected =
      input.selectedSlides.length > 0
        ? input.selectedSlides
        : input.primary
          ? [input.primary]
          : [];
    return orderSlidesForExport(selected, input.slides);
  }
  if (input.scope === "current") {
    return input.primary ? [input.primary] : [];
  }
  return input.slides
    .filter((slide) => slide.isActive !== false)
    .slice()
    .sort((a, b) => a.sortOrder - b.sortOrder);
}

export function resolveExportPptxTargets(
  selectedSlides: readonly Slide[],
  primary: Slide | null,
  playlistSlides: readonly Slide[],
): { targets: Slide[]; skipped: number } {
  const pool =
    selectedSlides.length > 0 ? selectedSlides : primary ? [primary] : [];
  const ordered = orderSlidesForExport(pool, playlistSlides);
  const targets = ordered.filter(isCustomMessageSlide);
  return { targets, skipped: ordered.length - targets.length };
}

export function uniqueExportFileName(
  title: string,
  used: Set<string>,
  ext: string,
): string {
  const base = title.replace(/[^\w\-]+/g, "_").slice(0, 40) || "slide";
  const suffix = ext.startsWith(".") ? ext : `.${ext}`;
  let name = `${base}${suffix}`;
  let index = 2;
  while (used.has(name)) {
    name = `${base}-${index}${suffix}`;
    index += 1;
  }
  used.add(name);
  return name;
}
