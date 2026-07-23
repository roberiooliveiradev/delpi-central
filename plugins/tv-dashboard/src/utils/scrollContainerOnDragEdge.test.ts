import { describe, expect, it } from "vitest";

import { scrollContainerOnDragEdge } from "./scrollContainerOnDragEdge";

function mockScrollContainer(overrides: {
  top: number;
  height: number;
  scrollTop?: number;
  scrollHeight?: number;
  clientHeight?: number;
}): HTMLElement {
  const scrollHeight = overrides.scrollHeight ?? 800;
  const clientHeight = overrides.clientHeight ?? 200;
  let scrollTop = overrides.scrollTop ?? 0;
  return {
    get scrollTop() {
      return scrollTop;
    },
    set scrollTop(value: number) {
      scrollTop = value;
    },
    scrollHeight,
    clientHeight,
    getBoundingClientRect: () =>
      ({
        top: overrides.top,
        bottom: overrides.top + overrides.height,
        left: 0,
        right: 100,
        width: 100,
        height: overrides.height,
        x: 0,
        y: overrides.top,
        toJSON: () => ({}),
      }) as DOMRect,
  } as HTMLElement;
}

describe("scrollContainerOnDragEdge", () => {
  it("rola para cima quando o ponteiro está na borda superior", () => {
    const el = mockScrollContainer({ top: 100, height: 200, scrollTop: 120 });
    const delta = scrollContainerOnDragEdge(el, 105, { edgePx: 40, maxStepPx: 20 });
    expect(delta).toBeLessThan(0);
    expect(el.scrollTop).toBeLessThan(120);
  });

  it("rola para baixo quando o ponteiro está na borda inferior", () => {
    const el = mockScrollContainer({ top: 100, height: 200, scrollTop: 40 });
    const delta = scrollContainerOnDragEdge(el, 290, { edgePx: 40, maxStepPx: 20 });
    expect(delta).toBeGreaterThan(0);
    expect(el.scrollTop).toBeGreaterThan(40);
  });

  it("não rola no centro nem sem overflow", () => {
    const el = mockScrollContainer({ top: 100, height: 200, scrollTop: 50 });
    expect(scrollContainerOnDragEdge(el, 200, { edgePx: 40 })).toBe(0);
    expect(el.scrollTop).toBe(50);

    const short = mockScrollContainer({
      top: 0,
      height: 200,
      scrollHeight: 200,
      clientHeight: 200,
      scrollTop: 0,
    });
    expect(scrollContainerOnDragEdge(short, 10)).toBe(0);
  });

  it("respeita limites 0 e maxScroll", () => {
    const atTop = mockScrollContainer({ top: 0, height: 200, scrollTop: 0 });
    scrollContainerOnDragEdge(atTop, 5, { edgePx: 40, maxStepPx: 30 });
    expect(atTop.scrollTop).toBe(0);

    const atBottom = mockScrollContainer({
      top: 0,
      height: 200,
      scrollTop: 600,
      scrollHeight: 800,
      clientHeight: 200,
    });
    scrollContainerOnDragEdge(atBottom, 195, { edgePx: 40, maxStepPx: 30 });
    expect(atBottom.scrollTop).toBe(600);
  });

  it("ignora clientY inválido", () => {
    const el = mockScrollContainer({ top: 0, height: 200, scrollTop: 40 });
    expect(scrollContainerOnDragEdge(el, Number.NaN)).toBe(0);
    expect(el.scrollTop).toBe(40);
  });
});
