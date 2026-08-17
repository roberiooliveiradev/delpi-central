import { describe, expect, it } from "vitest";

import {
  formatPresentationTransitionLabel,
  isPresentationTransitionStyle,
  PRESENTATION_TRANSITION_STYLES,
  resolveSlideTransitionStyle,
} from "./presentationTransition";

describe("resolveSlideTransitionStyle", () => {
  it("usa override do slide quando definido", () => {
    expect(
      resolveSlideTransitionStyle(
        { transitionStyle: "slide" },
        { transitionStyle: "fade" },
      ),
    ).toBe("slide");
  });

  it("herda da playlist quando slide não tem override", () => {
    expect(resolveSlideTransitionStyle({ transitionStyle: null }, { transitionStyle: "none" })).toBe(
      "none",
    );
    expect(resolveSlideTransitionStyle({}, { transitionStyle: "slide" })).toBe("slide");
  });

  it("aceita o catálogo sutil e cai em fade apenas para valores inválidos", () => {
    expect(PRESENTATION_TRANSITION_STYLES).toEqual([
      "fade",
      "dissolve",
      "slide",
      "push",
      "wipe",
      "zoom",
      "none",
    ]);
    expect(isPresentationTransitionStyle("wipe")).toBe(true);
    expect(formatPresentationTransitionLabel("zoom")).toBe("Zoom suave");
    expect(
      resolveSlideTransitionStyle({ transitionStyle: "zoom" }, { transitionStyle: "fade" }),
    ).toBe("zoom");
    expect(
      resolveSlideTransitionStyle({ transitionStyle: "origami" }, { transitionStyle: "invalid" }),
    ).toBe("fade");
  });
});
