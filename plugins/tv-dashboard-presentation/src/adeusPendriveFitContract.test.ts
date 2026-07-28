import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  computeDesignViewportLayoutBox,
  computeDesignViewportScale,
} from "./DesignViewportStage";
import {
  hostFitPaintedSize,
  isHostFitMeasurementSafe,
  resolvePresentationScaleMethod,
} from "./presentationFitPolicy";

/**
 * Regressão Adeus Pendrive — espaço acima + corte abaixo.
 *
 * Causa raiz: host «ajustar à tela» mede scrollWidth/Height.
 * `transform: scale` mantém layout 1920×1080; o host reescala e desloca.
 * `zoom` faz medida = caixa visual → fit seguro.
 */
describe("Adeus Pendrive / host-fit — sem corte", () => {
  const tv = { width: 1280, height: 720 };
  const design = { width: 1920, height: 1080 };

  it("contain: caixa visual cabe no container (slide não é cortado pelo nosso scale)", () => {
    const scale = computeDesignViewportScale(
      tv.width,
      tv.height,
      design.width,
      design.height,
      "contain",
    );
    const visual = computeDesignViewportLayoutBox(design.width, design.height, scale);
    expect(visual.width).toBeLessThanOrEqual(tv.width + 0.01);
    expect(visual.height).toBeLessThanOrEqual(tv.height + 0.01);
    expect(visual.width / visual.height).toBeCloseTo(design.width / design.height, 5);
  });

  it("transform (bug): medida = design → host-fit desloca/corta", () => {
    const scale = computeDesignViewportScale(
      tv.width,
      tv.height,
      design.width,
      design.height,
      "contain",
    );
    const visual = computeDesignViewportLayoutBox(design.width, design.height, scale);

    // O que WebView mede com transform:scale (layout pré-scale).
    const measured = { width: design.width, height: design.height };
    expect(
      isHostFitMeasurementSafe({
        measuredWidth: measured.width,
        measuredHeight: measured.height,
        visualWidth: visual.width,
        visualHeight: visual.height,
      }),
    ).toBe(false);

    const painted = hostFitPaintedSize({
      tvWidth: tv.width,
      tvHeight: tv.height,
      measuredWidth: measured.width,
      measuredHeight: measured.height,
      visualWidth: design.width,
      visualHeight: design.height,
    });
    // Documento 1920×1080 contain na TV 1280×720 → ok geometricamente,
    // mas a medida ≠ visual do nosso stage (já escalado) — contrato de segurança falha.
    expect(painted.fitsWithoutCrop).toBe(true);
    expect(measured.width).toBeGreaterThan(visual.width + 1);
  });

  it("zoom (fix): medida = visual → host-fit seguro", () => {
    const scale = computeDesignViewportScale(
      tv.width,
      tv.height,
      design.width,
      design.height,
      "contain",
    );
    const visual = computeDesignViewportLayoutBox(design.width, design.height, scale);

    expect(
      isHostFitMeasurementSafe({
        measuredWidth: visual.width,
        measuredHeight: visual.height,
        visualWidth: visual.width,
        visualHeight: visual.height,
      }),
    ).toBe(true);

    const painted = hostFitPaintedSize({
      tvWidth: tv.width,
      tvHeight: tv.height,
      measuredWidth: visual.width,
      measuredHeight: visual.height,
      visualWidth: visual.width,
      visualHeight: visual.height,
    });
    expect(painted.fitsWithoutCrop).toBe(true);
    expect(painted.width).toBeLessThanOrEqual(tv.width + 0.5);
    expect(painted.height).toBeLessThanOrEqual(tv.height + 0.5);
  });

  it("política kiosk escolhe zoom (não transform)", () => {
    expect(resolvePresentationScaleMethod("kiosk")).toBe("zoom");
    expect(resolvePresentationScaleMethod("preview")).toBe("transform");
  });

  it("código: kiosk usa zoom + pin top 0 (contrato fonte)", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const stageSrc = readFileSync(join(here, "DesignViewportStage.tsx"), "utf8");
    const pinSrc = readFileSync(join(here, "usePresentationViewportPin.ts"), "utf8");
    const policySrc = readFileSync(join(here, "presentationFitPolicy.ts"), "utf8");

    expect(policySrc).toMatch(/surface === "kiosk"\s*\?\s*"zoom"/);
    expect(stageSrc).toMatch(/zoom:\s*scale/);
    expect(stageSrc).toMatch(/resolvePresentationScaleMethod/);
    expect(stageSrc).toMatch(/contain:\s*"strict"/);
    expect(pinSrc).toMatch(/el\.style\.top\s*=\s*"0"/);
    // Proíbe atribuição runtime height+top (comentário histórico pode citar o anti-padrão).
    expect(pinSrc).not.toMatch(/style\.height\s*=\s*`\$\{[^}]*\+\s*top/);
    expect(pinSrc).not.toMatch(/Math\.max\([^)]*height\s*\+\s*top/);
  });
});
