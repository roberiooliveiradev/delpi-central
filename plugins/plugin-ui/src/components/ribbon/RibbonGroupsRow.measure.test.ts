import { describe, expect, it } from "vitest";

import {
  findRibbonWidthConstraint,
  measureElementContentWidth,
  measureRibbonAvailableWidth,
} from "./RibbonGroupsRow";

describe("measureElementContentWidth", () => {
  it("usa o maior entre bbox e scrollWidth", () => {
    const node = {
      getBoundingClientRect: () => ({ width: 120 }),
      scrollWidth: 200,
    } as unknown as HTMLElement;
    expect(measureElementContentWidth(node)).toBe(200);
  });
});

describe("measureRibbonAvailableWidth", () => {
  it("quando o row overflowa, limita pela largura do pai", () => {
    const parent = { clientWidth: 400 } as unknown as HTMLElement;
    const row = {
      clientWidth: 800,
      scrollWidth: 1200,
      parentElement: parent,
    } as unknown as HTMLElement;
    expect(measureRibbonAvailableWidth(row)).toBe(400);
  });

  it("sem overflow usa o menor entre row e pai", () => {
    const parent = { clientWidth: 500 } as unknown as HTMLElement;
    const row = {
      clientWidth: 480,
      scrollWidth: 480,
      parentElement: parent,
    } as unknown as HTMLElement;
    expect(measureRibbonAvailableWidth(row)).toBe(480);
  });

  it("usa o scrollport ancestral quando o row cresceu com o conteúdo", () => {
    const original = globalThis.getComputedStyle;
    globalThis.getComputedStyle = ((el: Element) => {
      const overflowX =
        (el as HTMLElement & { __ox?: string }).__ox ?? "visible";
      return { overflowX, maxWidth: "none" } as CSSStyleDeclaration;
    }) as typeof getComputedStyle;

    try {
      const scrollport = {
        clientWidth: 640,
        parentElement: null,
        __ox: "auto",
      } as unknown as HTMLElement & { __ox: string };
      const parent = {
        clientWidth: 1400,
        parentElement: scrollport,
        __ox: "visible",
      } as unknown as HTMLElement & { __ox: string };
      const row = {
        clientWidth: 1400,
        scrollWidth: 1400,
        parentElement: parent,
      } as unknown as HTMLElement;

      expect(findRibbonWidthConstraint(row)).toBe(scrollport);
      expect(measureRibbonAvailableWidth(row)).toBe(640);
    } finally {
      globalThis.getComputedStyle = original;
    }
  });
});
