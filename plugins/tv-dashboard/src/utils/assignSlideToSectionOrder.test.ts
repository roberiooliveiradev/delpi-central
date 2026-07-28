import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { assignSlideToSectionOrder } from "./assignSlideToSectionOrder";

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

describe("assignSlideToSectionOrder", () => {
  it("move slide para o fim da seção alvo", () => {
    const slides = [
      slide({ id: "a", sortOrder: 0, sectionId: null }),
      slide({ id: "b", sortOrder: 1, sectionId: "s1" }),
      slide({ id: "c", sortOrder: 2, sectionId: "s1" }),
      slide({ id: "d", sortOrder: 3, sectionId: null }),
    ];
    const next = assignSlideToSectionOrder(slides, "a", "s1");
    expect(next.map((item) => item.id)).toEqual(["b", "c", "a", "d"]);
    expect(next.find((item) => item.id === "a")?.sectionId).toBe("s1");
    expect(next.map((item) => item.sortOrder)).toEqual([0, 1, 2, 3]);
  });

  it("move para bucket sem seção", () => {
    const slides = [
      slide({ id: "a", sortOrder: 0, sectionId: "s1" }),
      slide({ id: "b", sortOrder: 1, sectionId: null }),
    ];
    const next = assignSlideToSectionOrder(slides, "a", null);
    expect(next.find((item) => item.id === "a")?.sectionId).toBeNull();
    expect(next.map((item) => item.id)).toEqual(["b", "a"]);
  });

  it("seção vazia coloca no fim da playlist", () => {
    const slides = [
      slide({ id: "a", sortOrder: 0, sectionId: null }),
      slide({ id: "b", sortOrder: 1, sectionId: null }),
    ];
    const next = assignSlideToSectionOrder(slides, "a", "s-new");
    expect(next.map((item) => item.id)).toEqual(["b", "a"]);
    expect(next.find((item) => item.id === "a")?.sectionId).toBe("s-new");
  });
});
