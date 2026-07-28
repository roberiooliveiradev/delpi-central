import { describe, expect, it } from "vitest";

import type { PlaylistSection } from "../api/tvDashboardApi";
import {
  sectionsVisibleInJump,
  shouldShowSectionChrome,
  shouldShowSectionInFilmstrip,
} from "./sectionChromeVisibility";

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

describe("sectionChromeVisibility", () => {
  it("oculta quando vazio ou só main", () => {
    expect(shouldShowSectionChrome([])).toBe(false);
    expect(shouldShowSectionChrome([section({ id: "m", sortOrder: 0, isMain: true })])).toBe(
      false,
    );
  });

  it("mostra com main + user", () => {
    const sections = [
      section({ id: "m", sortOrder: 0, isMain: true }),
      section({ id: "u", sortOrder: 1 }),
    ];
    expect(shouldShowSectionChrome(sections)).toBe(true);
    expect(sectionsVisibleInJump(sections).map((s) => s.id)).toEqual(["m", "u"]);
  });

  it("oculta Principal no filmstrip quando não há slides", () => {
    const main = section({ id: "m", sortOrder: 0, isMain: true });
    expect(shouldShowSectionInFilmstrip(main, 0)).toBe(false);
    expect(shouldShowSectionInFilmstrip(main, 1)).toBe(true);
    expect(shouldShowSectionInFilmstrip(section({ id: "u", sortOrder: 1 }), 0)).toBe(true);
  });
});
