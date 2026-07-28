import { describe, expect, it } from "vitest";

import {
  computeDesignViewportBleedSize,
  computeDesignViewportLayoutBox,
  computeDesignViewportScale,
  DESIGN_VIEWPORT_BLEED_RATIO,
} from "./DesignViewportStage";

describe("computeDesignViewportBleedSize", () => {
  it("apresentação/prévia: bleed zero — stage = moldura de design", () => {
    const { bleedX, bleedY, outerW, outerH } = computeDesignViewportBleedSize(1920, 1080);
    expect(DESIGN_VIEWPORT_BLEED_RATIO).toBe(0);
    expect(bleedX).toBe(0);
    expect(bleedY).toBe(0);
    expect(outerW).toBe(1920);
    expect(outerH).toBe(1080);
  });

  it("aceita bleed explícito só sob demanda (não é o default da TV)", () => {
    const { bleedX, outerW } = computeDesignViewportBleedSize(1920, 1080, 0.5);
    expect(bleedX).toBe(960);
    expect(outerW).toBe(1920 + 2 * 960);
  });
});

describe("computeDesignViewportScale", () => {
  it("contain preenche a dimensão limitante (pillarbox em viewport mais larga)", () => {
    expect(computeDesignViewportScale(1600, 900, 1920, 1080, "contain")).toBeCloseTo(900 / 1080);
  });

  it("contain preenche a largura quando o container é mais baixo que 16:9", () => {
    expect(computeDesignViewportScale(1920, 800, 1920, 1080, "contain")).toBeCloseTo(800 / 1080);
  });

  it("contain em área exatamente 16:9 usa escala 1 quando o design é 1080p", () => {
    expect(computeDesignViewportScale(1920, 1080, 1920, 1080, "contain")).toBe(1);
  });

  it("cover em viewport mais larga que 16:9 preenche a largura (sem pillarbox)", () => {
    expect(computeDesignViewportScale(1920, 900, 1920, 1080, "cover")).toBeCloseTo(1);
    expect(computeDesignViewportScale(1920, 900, 1920, 1080, "contain")).toBeCloseTo(900 / 1080);
  });

  it("contain em browser típico (mais largo que 16:9) não corta altura do slide", () => {
    const scale = computeDesignViewportScale(1600, 900, 1920, 1080, "contain");
    expect(scale).toBeCloseTo(900 / 1080);
    expect(1920 * scale).toBeLessThanOrEqual(1600 + 0.01);
    expect(1080 * scale).toBeLessThanOrEqual(900 + 0.01);
  });

  it("cover em browser mais baixo que 16:9 corta o topo/base (documenta o trade-off)", () => {
    const cover = computeDesignViewportScale(1920, 900, 1920, 1080, "cover");
    expect(1080 * cover).toBeGreaterThan(900);
  });

  it("cover em viewport mais alta que 16:9 preenche altura (sem letterbox — TV kiosk)", () => {
    // Ex.: WebView 1920×1200 (barras pretas com contain).
    const cover = computeDesignViewportScale(1920, 1200, 1920, 1080, "cover");
    expect(cover).toBeCloseTo(1200 / 1080);
    expect(1080 * cover).toBeCloseTo(1200);
    expect(1920 * cover).toBeGreaterThan(1920);
    const contain = computeDesignViewportScale(1920, 1200, 1920, 1080, "contain");
    expect(1080 * contain).toBeLessThan(1200);
  });

  it("retorna 0 para dimensões inválidas", () => {
    expect(computeDesignViewportScale(0, 900, 1920, 1080)).toBe(0);
  });
});

describe("computeDesignViewportLayoutBox", () => {
  it("caixa de layout = design × scale (webview mede o visual, não 1920 pré-scale)", () => {
    const scale = computeDesignViewportScale(1600, 900, 1920, 1080, "contain");
    const box = computeDesignViewportLayoutBox(1920, 1080, scale);
    expect(box.width).toBeCloseTo(1920 * scale);
    expect(box.height).toBeCloseTo(900);
    expect(box.width).toBeLessThanOrEqual(1600 + 0.01);
  });

  it("retorna 0 com scale inválido", () => {
    expect(computeDesignViewportLayoutBox(1920, 1080, 0)).toEqual({ width: 0, height: 0 });
  });
});
