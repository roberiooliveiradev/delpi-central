import { describe, expect, it } from "vitest";

import {
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
});
