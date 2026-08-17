import { describe, expect, it } from "vitest";

import { resolveSlideBatchRibbonTab } from "./resolveSlideBatchRibbonTab";

describe("resolveSlideBatchRibbonTab", () => {
  it("abre Tela quando a seleção passa de uma tela", () => {
    expect(
      resolveSlideBatchRibbonTab({ selectedSlideCount: 2, currentTab: "playlist" }),
    ).toBe("slide");
    expect(
      resolveSlideBatchRibbonTab({ selectedSlideCount: 3, currentTab: "insert" }),
    ).toBe("slide");
    expect(
      resolveSlideBatchRibbonTab({ selectedSlideCount: 2, currentTab: "element" }),
    ).toBe("slide");
  });

  it("não troca a aba se já está em Tela ou se há só uma tela", () => {
    expect(
      resolveSlideBatchRibbonTab({ selectedSlideCount: 2, currentTab: "slide" }),
    ).toBeNull();
    expect(
      resolveSlideBatchRibbonTab({ selectedSlideCount: 1, currentTab: "insert" }),
    ).toBeNull();
    expect(
      resolveSlideBatchRibbonTab({ selectedSlideCount: 0, currentTab: "playlist" }),
    ).toBeNull();
  });
});
