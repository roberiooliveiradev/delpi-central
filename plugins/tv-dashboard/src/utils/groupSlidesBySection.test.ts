import { describe, expect, it } from "vitest";

import type { PlaylistSection, Slide } from "../api/tvDashboardApi";
import { groupSlidesBySection } from "./groupSlidesBySection";

function slide(partial: Partial<Slide> & Pick<Slide, "id" | "sortOrder">): Slide {
  return {
    playlistId: "p1",
    slideType: "native",
    title: partial.id,
    isActive: true,
    ...partial,
  };
}

describe("groupSlidesBySection", () => {
  it("separa unsectioned e ordena seções", () => {
    const sections: PlaylistSection[] = [
      { id: "s2", playlistId: "p1", name: "B", sortOrder: 1 },
      { id: "s1", playlistId: "p1", name: "A", sortOrder: 0 },
    ];
    const slides = [
      slide({ id: "a", sortOrder: 0, sectionId: "s1" }),
      slide({ id: "b", sortOrder: 1 }),
      slide({ id: "c", sortOrder: 2, sectionId: "s2" }),
    ];
    const grouped = groupSlidesBySection(slides, sections);
    expect(grouped.unsectioned.map((s) => s.id)).toEqual(["b"]);
    expect(grouped.sections.map((g) => g.section.id)).toEqual(["s1", "s2"]);
    expect(grouped.sections[0]!.slides.map((s) => s.id)).toEqual(["a"]);
    expect(grouped.sections[1]!.slides.map((s) => s.id)).toEqual(["c"]);
  });
});
