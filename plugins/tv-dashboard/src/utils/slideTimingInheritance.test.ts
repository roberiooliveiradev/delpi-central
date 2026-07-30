import { describe, expect, it } from "vitest";

import {
  formatSlideTransitionLabel,
  resolveSlideDurationSec,
  resolveSlideTransitionStyle,
  slideDurationIsOverride,
} from "./slideTimingInheritance";

describe("slideTimingInheritance", () => {
  it("resolve duração slide → seção → playlist", () => {
    expect(
      resolveSlideDurationSec({
        slideDuration: 12,
        sectionDefault: 20,
        playlistDefault: 30,
      }),
    ).toBe(12);
    expect(
      resolveSlideDurationSec({
        slideDuration: null,
        sectionDefault: 20,
        playlistDefault: 30,
      }),
    ).toBe(20);
    expect(
      resolveSlideDurationSec({
        slideDuration: null,
        sectionDefault: null,
        playlistDefault: 30,
      }),
    ).toBe(30);
  });

  it("resolve transição e marca override", () => {
    expect(
      resolveSlideTransitionStyle({
        slideTransition: null,
        sectionTransition: "slide",
        playlistTransition: "fade",
      }),
    ).toBe("slide");
    expect(slideDurationIsOverride(null)).toBe(false);
    expect(slideDurationIsOverride(10)).toBe(true);
    expect(formatSlideTransitionLabel("slide")).toBe("Deslizar");
  });
});
