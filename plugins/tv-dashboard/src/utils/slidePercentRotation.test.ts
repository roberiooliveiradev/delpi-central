import { describe, expect, it } from "vitest";

import {
  applyGroupRotationDelta,
  applyGroupScaleFromUnionDelta,
  resolveFramesGroupCenter,
  resolveGroupSelectionChrome,
  resolveRotatedFrameCorners,
  rotatePointPercentAround,
} from "./slidePercentRotation";

describe("rotatePointPercentAround", () => {
  it("com aspect 1, 90° mapeia eixo X→Y como antes", () => {
    const next = rotatePointPercentAround({ x: 10, y: 50 }, { x: 50, y: 50 }, 90, 1);
    expect(next.x).toBeCloseTo(50, 5);
    expect(next.y).toBeCloseTo(10, 5);
  });

  it("com aspect 16/9, 90° preserva distância visual (px)", () => {
    const aspect = 16 / 9;
    const next = rotatePointPercentAround({ x: 10, y: 50 }, { x: 50, y: 50 }, 90, aspect);
    expect(next.x).toBeCloseTo(50, 5);
    expect(next.y).toBeCloseTo(50 - 40 * aspect, 5);
  });
});

describe("applyGroupRotationDelta", () => {
  it("orbita membros em torno do centro e soma rotação (aspect 1)", () => {
    const startFrames = new Map([
      ["a", { x: 0, y: 40, w: 20, h: 20 }],
      ["b", { x: 80, y: 40, w: 20, h: 20 }],
    ]);
    const startRotations = new Map([
      ["a", 0],
      ["b", 10],
    ]);
    const center = resolveFramesGroupCenter(startFrames.values());
    expect(center).toEqual({ x: 50, y: 50 });

    const next = applyGroupRotationDelta({
      startFrames,
      startRotations,
      center,
      deltaDeg: 90,
      slideAspect: 1,
    });
    const a = next.get("a")!;
    const b = next.get("b")!;
    expect(a.rotation).toBe(90);
    expect(b.rotation).toBe(100);
    expect(a.frame.x + a.frame.w / 2).toBeCloseTo(50, 5);
    expect(a.frame.y + a.frame.h / 2).toBeCloseTo(10, 5);
    expect(b.frame.x + b.frame.w / 2).toBeCloseTo(50, 5);
    expect(b.frame.y + b.frame.h / 2).toBeCloseTo(90, 5);
  });

  it("com aspect 16/9 não usa y% isotrópico (evita membros ‘saindo’)", () => {
    const aspect = 16 / 9;
    const startFrames = new Map([
      ["a", { x: 0, y: 40, w: 20, h: 20 }],
      ["b", { x: 80, y: 40, w: 20, h: 20 }],
    ]);
    const startRotations = new Map([
      ["a", 0],
      ["b", 0],
    ]);
    const center = resolveFramesGroupCenter(startFrames.values());
    const next = applyGroupRotationDelta({
      startFrames,
      startRotations,
      center,
      deltaDeg: 90,
      slideAspect: aspect,
    });
    const aY = next.get("a")!.frame.y + next.get("a")!.frame.h / 2;
    expect(aY).toBeCloseTo(50 - 40 * aspect, 5);
  });
});

describe("resolveGroupSelectionChrome", () => {
  it("membro único sem rotação: frame = layout", () => {
    const chrome = resolveGroupSelectionChrome({
      members: [{ frame: { x: 20, y: 30, w: 40, h: 40 }, rotation: 0 }],
    });
    expect(chrome.rotation).toBe(0);
    expect(chrome.frame).toEqual({ x: 20, y: 30, w: 40, h: 40 });
  });

  it("membro rotacionado: AABB visual dos cantos (sem CSS rotate no chrome)", () => {
    const frame = { x: 40, y: 40, w: 20, h: 20 };
    const chrome = resolveGroupSelectionChrome({
      members: [{ frame, rotation: 45 }],
      slideAspect: 1,
    });
    expect(chrome.rotation).toBe(0);
    const corners = resolveRotatedFrameCorners(frame, 45, 1);
    const xs = corners.map((p) => p.x);
    const ys = corners.map((p) => p.y);
    expect(chrome.frame.x).toBeCloseTo(Math.min(...xs), 5);
    expect(chrome.frame.y).toBeCloseTo(Math.min(...ys), 5);
    expect(chrome.frame.w).toBeCloseTo(Math.max(...xs) - Math.min(...xs), 5);
    expect(chrome.frame.h).toBeCloseTo(Math.max(...ys) - Math.min(...ys), 5);
    // 45° em quadrado: AABB maior que o frame layout
    expect(chrome.frame.w).toBeGreaterThan(20);
    expect(chrome.frame.h).toBeGreaterThan(20);
  });
});

describe("applyGroupScaleFromUnionDelta", () => {
  it("canto SE com lock escala membros de forma uniforme a partir do NW", () => {
    const startFrames = new Map([
      ["a", { x: 10, y: 10, w: 20, h: 20 }],
      ["b", { x: 40, y: 10, w: 10, h: 10 }],
    ]);
    const startUnion = { x: 10, y: 10, w: 40, h: 20 };
    const nextUnion = { x: 10, y: 10, w: 80, h: 40 };
    const next = applyGroupScaleFromUnionDelta({
      startFrames,
      startUnion,
      nextUnion,
      handle: "se",
      lockAspect: true,
    });
    const a = next.get("a")!;
    const b = next.get("b")!;
    expect(a.w).toBeCloseTo(40, 5);
    expect(a.h).toBeCloseTo(40, 5);
    expect(b.w).toBeCloseTo(20, 5);
    expect(b.h).toBeCloseTo(20, 5);
    expect(a.x).toBeCloseTo(10, 5);
    expect(b.x).toBeCloseTo(70, 5);
  });

  it("mantém proporção relativa entre membros (não dw/dh absoluto)", () => {
    const startFrames = new Map([
      ["small", { x: 0, y: 0, w: 10, h: 10 }],
      ["big", { x: 20, y: 0, w: 30, h: 30 }],
    ]);
    const startUnion = { x: 0, y: 0, w: 50, h: 30 };
    const nextUnion = { x: 0, y: 0, w: 100, h: 60 };
    const next = applyGroupScaleFromUnionDelta({
      startFrames,
      startUnion,
      nextUnion,
      handle: "se",
      lockAspect: true,
    });
    expect(next.get("small")!.w / next.get("big")!.w).toBeCloseTo(10 / 30, 5);
  });
});
