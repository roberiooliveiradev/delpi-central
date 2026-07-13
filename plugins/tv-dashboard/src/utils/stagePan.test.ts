import { describe, expect, it } from "vitest";

import {
  applyStagePanScrollDelta,
  centerStageScroll,
  resolveStagePanGutterPx,
  stageScrollAfterZoomTowardPoint,
} from "./stagePan";

describe("applyStagePanScrollDelta", () => {
  it("arrastar para a direita revela conteúdo à esquerda (scrollLeft diminui)", () => {
    expect(applyStagePanScrollDelta({ scrollLeft: 40, scrollTop: 10 }, 12, -4)).toEqual({
      scrollLeft: 28,
      scrollTop: 14,
    });
  });
});

describe("stageScrollAfterZoomTowardPoint", () => {
  it("reancora o ponto sob o cursor após zoom in", () => {
    expect(
      stageScrollAfterZoomTowardPoint({
        prevZoom: 1,
        nextZoom: 2,
        scrollLeft: 100,
        scrollTop: 50,
        pointerOffsetX: 200,
        pointerOffsetY: 100,
      }),
    ).toEqual({ scrollLeft: 400, scrollTop: 200 });
  });

  it("no-op quando o zoom não muda", () => {
    expect(
      stageScrollAfterZoomTowardPoint({
        prevZoom: 1,
        nextZoom: 1,
        scrollLeft: 10,
        scrollTop: 20,
        pointerOffsetX: 5,
        pointerOffsetY: 5,
      }),
    ).toEqual({ scrollLeft: 10, scrollTop: 20 });
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
