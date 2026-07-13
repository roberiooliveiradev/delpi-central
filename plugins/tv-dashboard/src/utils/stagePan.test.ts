import { describe, expect, it } from "vitest";

import {
  applyStagePanScrollDelta,
  centerStageScroll,
  resolveStagePanGutterPx,
} from "./stagePan";

describe("applyStagePanScrollDelta", () => {
  it("arrastar para a direita revela conteúdo à esquerda (scrollLeft diminui)", () => {
    expect(applyStagePanScrollDelta({ scrollLeft: 40, scrollTop: 10 }, 12, -4)).toEqual({
      scrollLeft: 28,
      scrollTop: 14,
    });
  });
});

describe("resolveStagePanGutterPx", () => {
  it("usa metade da viewport com piso de 48px", () => {
    expect(resolveStagePanGutterPx(800, 600)).toEqual({ x: 400, y: 300 });
    expect(resolveStagePanGutterPx(40, 40)).toEqual({ x: 48, y: 48 });
  });
});

describe("centerStageScroll", () => {
  it("centraliza quando há overflow nos dois eixos", () => {
    expect(
      centerStageScroll({
        scrollWidth: 1000,
        scrollHeight: 800,
        clientWidth: 400,
        clientHeight: 200,
      }),
    ).toEqual({ scrollLeft: 300, scrollTop: 300 });
  });

  it("não gera scroll negativo quando o conteúdo cabe", () => {
    expect(
      centerStageScroll({
        scrollWidth: 200,
        scrollHeight: 100,
        clientWidth: 400,
        clientHeight: 300,
      }),
    ).toEqual({ scrollLeft: 0, scrollTop: 0 });
  });
});
