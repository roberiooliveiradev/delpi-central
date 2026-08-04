import { describe, expect, it } from "vitest";

import type { PlaylistSection, Slide } from "../api/tvDashboardApi";
import {
  buildPresentationOrderIndexBySlideId,
  isSlideVisibleInPresentation,
  listPresentationOrderedSlides,
} from "./presentationSlideOrder";

function slide(partial: Partial<Slide> & Pick<Slide, "id" | "sortOrder">): Slide {
  return {
    id: partial.id,
    playlistId: "p1",
    sortOrder: partial.sortOrder,
    slideType: "native",
    title: partial.title ?? partial.id,
    durationSec: 20,
    isActive: partial.isActive ?? true,
    sectionId: partial.sectionId ?? null,
    nativeScreenKey: null,
    nativeConfig: null,
    externalUrl: null,
    transitionStyle: null,
  };
}

function section(
  partial: Partial<PlaylistSection> & Pick<PlaylistSection, "id" | "sortOrder">,
): PlaylistSection {
  return {
    id: partial.id,
    playlistId: "p1",
    name: partial.name ?? partial.id,
    sortOrder: partial.sortOrder,
    isCollapsed: false,
    isActive: partial.isActive ?? true,
    isMain: partial.isMain ?? false,
    defaultDurationSec: null,
    transitionStyle: null,
    masterConfig: null,
  };
}

describe("presentationSlideOrder", () => {
  it("omite slide pausado e seção inativa (paridade present)", () => {
    expect(isSlideVisibleInPresentation({ isActive: false }, { isActive: true })).toBe(false);
    expect(isSlideVisibleInPresentation({ isActive: true }, { isActive: false })).toBe(false);
    expect(isSlideVisibleInPresentation({ isActive: true }, null)).toBe(true);
  });

  it("índice TV ignora pausados — slide Refugo não vira «4» se houver pausados antes", () => {
    const sections = [
      section({ id: "sec-main", sortOrder: 0, isMain: true, isActive: true }),
    ];
    const slides = [
      slide({ id: "paused-1", sortOrder: 0, isActive: false, sectionId: "sec-main" }),
      slide({ id: "paused-2", sortOrder: 1, isActive: false, sectionId: "sec-main" }),
      slide({ id: "proposito", sortOrder: 2, sectionId: "sec-main" }),
      slide({ id: "refugo", sortOrder: 3, title: "Refugo e retrabalho", sectionId: "sec-main" }),
      slide({ id: "ppm", sortOrder: 4, title: "PPM", sectionId: "sec-main" }),
    ];
    const ordered = listPresentationOrderedSlides(slides, sections);
    expect(ordered.map((item) => item.id)).toEqual(["proposito", "refugo", "ppm"]);

    const indexById = buildPresentationOrderIndexBySlideId(slides, sections);
    expect(indexById.get("refugo")).toBe(1); // 2/N na TV
    expect(indexById.get("ppm")).toBe(2);
    expect(indexById.has("paused-1")).toBe(false);
  });
});
