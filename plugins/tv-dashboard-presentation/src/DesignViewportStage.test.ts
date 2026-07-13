import { describe, expect, it } from "vitest";

import { computeDesignViewportScale } from "./DesignViewportStage";

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

  it("retorna 0 para dimensões inválidas", () => {
    expect(computeDesignViewportScale(0, 900, 1920, 1080)).toBe(0);
  });
});
