import { describe, expect, it } from "vitest";

import type { PlaylistSection, Slide } from "../api/tvDashboardApi";
import { claimSlidesForNewSection } from "./claimSlidesForNewSection";

function slide(partial: Partial<Slide> & Pick<Slide, "id" | "sortOrder">): Slide {
  return {
    id: partial.id,
    sortOrder: partial.sortOrder,
    title: partial.title ?? partial.id,
    slideType: "native",
    durationSec: 30,
    isActive: true,
    sectionId: partial.sectionId ?? null,
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
    isMain: partial.isMain,
  };
}

describe("claimSlidesForNewSection", () => {
  it("flat 1..5 âncora 2 → claim 2..5", () => {
    const slides = [
      slide({ id: "1", sortOrder: 0 }),
      slide({ id: "2", sortOrder: 1 }),
      slide({ id: "3", sortOrder: 2 }),
      slide({ id: "4", sortOrder: 3 }),
      slide({ id: "5", sortOrder: 4 }),
    ];
    const result = claimSlidesForNewSection(slides, [], "2");
    expect(result.beforeIds).toEqual(["1"]);
    expect(result.claimIds).toEqual(["2", "3", "4", "5"]);
    expect(result.anchorSectionId).toBeNull();
  });

  it("âncora no meio de A antes de B → claim até B", () => {
    const sections = [
      section({ id: "A", sortOrder: 0 }),
      section({ id: "B", sortOrder: 1 }),
    ];
    const slides = [
      slide({ id: "a1", sortOrder: 0, sectionId: "A" }),
      slide({ id: "a2", sortOrder: 1, sectionId: "A" }),
      slide({ id: "a3", sortOrder: 2, sectionId: "A" }),
      slide({ id: "b1", sortOrder: 3, sectionId: "B" }),
    ];
    const result = claimSlidesForNewSection(slides, sections, "a2");
    expect(result.beforeIds).toEqual(["a1"]);
    expect(result.claimIds).toEqual(["a2", "a3"]);
    expect(result.anchorSectionId).toBe("A");
  });

  it("âncora último → só ele", () => {
    const slides = [
      slide({ id: "1", sortOrder: 0 }),
      slide({ id: "2", sortOrder: 1 }),
    ];
    const result = claimSlidesForNewSection(slides, [], "2");
    expect(result.beforeIds).toEqual(["1"]);
    expect(result.claimIds).toEqual(["2"]);
  });

  it("âncora inexistente → vazio", () => {
    const result = claimSlidesForNewSection([slide({ id: "1", sortOrder: 0 })], [], "x");
    expect(result).toEqual({ beforeIds: [], claimIds: [], anchorSectionId: null });
  });
});
