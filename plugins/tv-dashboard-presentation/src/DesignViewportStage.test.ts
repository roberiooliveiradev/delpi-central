import { describe, expect, it } from "vitest";

import {
  computeDesignViewportBleedSize,
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
    // 1920×1080 em container 1600×900 → altura limita
    expect(computeDesignViewportScale(1600, 900, 1920, 1080, "contain")).toBeCloseTo(900 / 1080);
  });

  it("contain preenche a largura quando o container é mais baixo que 16:9", () => {
    expect(computeDesignViewportScale(1920, 800, 1920, 1080, "contain")).toBeCloseTo(800 / 1080);
  });

  it("contain em área exatamente 16:9 usa escala 1 quando o design é 1080p", () => {
    expect(computeDesignViewportScale(1920, 1080, 1920, 1080, "contain")).toBe(1);
  });

  it("cover em viewport mais larga que 16:9 preenche a largura (sem pillarbox)", () => {
    // 1920×900 (browser com chrome) × design 1920×1080 → cover usa sx=1
    expect(computeDesignViewportScale(1920, 900, 1920, 1080, "cover")).toBeCloseTo(1);
    expect(computeDesignViewportScale(1920, 900, 1920, 1080, "contain")).toBeCloseTo(900 / 1080);
  });

  it("contain em browser típico (mais largo que 16:9) não corta altura do slide", () => {
    // Viewport 1600×900 vs 1920×1080: contain escala pela altura — KPI no topo permanece no quadro.
    const scale = computeDesignViewportScale(1600, 900, 1920, 1080, "contain");
    expect(scale).toBeCloseTo(900 / 1080);
    expect(1920 * scale).toBeLessThanOrEqual(1600 + 0.01);
    expect(1080 * scale).toBeLessThanOrEqual(900 + 0.01);
  });

  it("cover em browser mais baixo que 16:9 corta o topo/base (documenta o trade-off)", () => {
    const cover = computeDesignViewportScale(1920, 900, 1920, 1080, "cover");
    expect(1080 * cover).toBeGreaterThan(900);
  });

  it("retorna 0 para dimensões inválidas", () => {
    expect(computeDesignViewportScale(0, 900, 1920, 1080)).toBe(0);
  });
});
