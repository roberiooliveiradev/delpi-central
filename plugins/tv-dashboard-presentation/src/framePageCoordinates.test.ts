import { describe, expect, it } from "vitest";

import {
  designYBottomLeftToTopLeft,
  designYTopLeftToBottomLeft,
  framePercentToPageBottomLeftPx,
  hostRelativeFrameToPageBottomLeftPx,
  patchComunicadoFramePageBottomLeftPx,
  patchHostRelativeFramePageBottomLeftPx,
} from "./framePageCoordinates";

const FULL_HD = { width: 1920, height: 1080 };

describe("framePageCoordinates", () => {
  it("converte Y top-left ↔ bottom-left", () => {
    // Box topo em y=200, h=100 → base do box em 1080-200-100=780 desde a base
    expect(designYTopLeftToBottomLeft(200, 1080, 100)).toBe(780);
    expect(designYBottomLeftToTopLeft(780, 1080, 100)).toBe(200);
    // Canto inferior esquerdo da página
    expect(designYTopLeftToBottomLeft(980, 1080, 100)).toBe(0);
  });

  it("frame do slide: Y UI com origem inferior esquerda", () => {
    const frame = { x: 10, y: 20, w: 30, h: 40 };
    // top 216, h 432 → yBottom = 1080 - 216 - 432 = 432
    const page = framePercentToPageBottomLeftPx(frame, FULL_HD);
    expect(page.x).toBeCloseTo(192);
    expect(page.y).toBeCloseTo(432);
    expect(page.w).toBeCloseTo(576);
    expect(page.h).toBeCloseTo(432);
  });

  it("patch Y em bottom-left move o elemento sem mudar altura", () => {
    const frame = { x: 10, y: 20, w: 30, h: 40 };
    const page = framePercentToPageBottomLeftPx(frame, FULL_HD);
    const next = patchComunicadoFramePageBottomLeftPx(frame, "y", 0, FULL_HD);
    const nextPage = framePercentToPageBottomLeftPx(next, FULL_HD);
    expect(nextPage.y).toBeCloseTo(0);
    expect(nextPage.h).toBeCloseTo(page.h);
    // Base na linha da página → top = 1080 - h
    expect(next.y + next.h).toBeCloseTo(100);
  });

  it("patch H em bottom-left mantém a base fixa", () => {
    const frame = { x: 10, y: 20, w: 30, h: 40 };
    const before = framePercentToPageBottomLeftPx(frame, FULL_HD);
    const next = patchComunicadoFramePageBottomLeftPx(frame, "h", before.h / 2, FULL_HD);
    const after = framePercentToPageBottomLeftPx(next, FULL_HD);
    expect(after.y).toBeCloseTo(before.y);
    expect(after.h).toBeCloseTo(before.h / 2);
  });

  it("parte relativa ao host vira px absoluto da página", () => {
    const host = { x: 10, y: 20, w: 50, h: 50 }; // host top-left 192,216 size 960x540
    const part = { x: 0, y: 0, w: 100, h: 100 }; // preenche o host
    const page = hostRelativeFrameToPageBottomLeftPx(part, host, FULL_HD);
    expect(page.x).toBeCloseTo(192);
    // abs top 216, h 540 → yBottom = 1080-216-540 = 324
    expect(page.y).toBeCloseTo(324);
    expect(page.w).toBeCloseTo(960);
    expect(page.h).toBeCloseTo(540);
  });

  it("patch parte em coords de página persiste % do host", () => {
    const host = { x: 10, y: 20, w: 50, h: 50 };
    const part = { x: 0, y: 0, w: 50, h: 50 };
    const page = hostRelativeFrameToPageBottomLeftPx(part, host, FULL_HD);
    // Move X absoluto para o mesmo canto do host (= parte x 0)
    const next = patchHostRelativeFramePageBottomLeftPx(part, host, "x", page.x + 96, FULL_HD);
    // 96px no host de 960 = 10%
    expect(next.x).toBeCloseTo(10);
    expect(next.y).toBeCloseTo(0);
  });
});
