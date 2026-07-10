import { describe, expect, it } from "vitest";

import { resolveSlideTransitionStyle } from "./presentationTransition";

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

  it("cai em fade para valores inválidos", () => {
    expect(
      resolveSlideTransitionStyle({ transitionStyle: "zoom" }, { transitionStyle: "invalid" }),
    ).toBe("fade");
  });
});
