import { describe, expect, it } from "vitest";

import {
  applyChartAddElementChoice,
  applyChartAddElementChoiceWithParts,
  isChartAddElementChoiceActive,
} from "./seriesChartAddElementChoices";
import { mergeSeriesChartOptions } from "./seriesChartOptions";

describe("applyChartAddElementChoice", () => {
  it("axes:x liga só o eixo horizontal sem forçar Y off", () => {
    const base = mergeSeriesChartOptions({
      showAxes: true,
      showXAxisLabels: false,
      showYAxisLabels: true,
    });
    const next = applyChartAddElementChoice("axes:x", base);
    expect(next.showXAxisLabels).toBe(true);
    expect(next.showYAxisLabels).toBe(true);
    expect(next.showAxes).toBe(true);
  });

  it("axes:none desliga ambos os eixos", () => {
    const next = applyChartAddElementChoice("axes:none", {});
    expect(next.showAxes).toBe(false);
    expect(next.showXAxisLabels).toBe(false);
    expect(next.showYAxisLabels).toBe(false);
  });

  it("legend:left posiciona legenda à esquerda", () => {
    const next = applyChartAddElementChoice("legend:left", { showLegend: false });
    expect(next.showLegend).toBe(true);
    expect(next.legendPosition).toBe("left");
  });

  it("grid:vertical alterna grade vertical preservando horizontal", () => {
    const base = mergeSeriesChartOptions({ showGrid: true, showVerticalGrid: false });
    const on = applyChartAddElementChoice("grid:vertical", base);
    expect(on.showVerticalGrid).toBe(true);
    expect(on.showGrid).toBe(true);
    const off = applyChartAddElementChoice("grid:vertical", on);
    expect(off.showVerticalGrid).toBe(false);
    expect(off.showGrid).toBe(true);
  });

  it("dataLabels:none desliga rótulos", () => {
    const next = applyChartAddElementChoice("dataLabels:none", { showDataLabels: true });
    expect(next.showDataLabels).toBe(false);
  });

  it("dataLabels:none preserva config detalhada ao desligar", () => {
    const next = applyChartAddElementChoice("dataLabels:none", {
      showDataLabels: true,
      dataLabels: {
        showCategoryName: true,
        showPercentage: true,
        position: "outsideEnd",
      },
    });
    expect(next.showDataLabels).toBe(false);
    expect(next.dataLabels).toMatchObject({
      showCategoryName: true,
      showPercentage: true,
      position: "outsideEnd",
    });
  });

  it("legend:none não apaga legendPosition", () => {
    const next = applyChartAddElementChoice("legend:none", {
      showLegend: true,
      legendPosition: "right",
    });
    expect(next.showLegend).toBe(false);
    expect(next.legendPosition).toBe("right");
  });

  it("dataLabels:categoryPercent aplica Label Contains PPT", () => {
    const next = applyChartAddElementChoice("dataLabels:categoryPercent", {});
    expect(next.showDataLabels).toBe(true);
    expect(next.dataLabels).toMatchObject({
      showCategoryName: true,
      showPercentage: true,
      showValue: false,
      position: "outsideEnd",
      showLeaderLines: true,
    });
    expect(isChartAddElementChoiceActive("dataLabels:categoryPercent", next)).toBe(true);
  });

  it("dataLabels:outsideEnd posiciona fora com linhas guia", () => {
    const next = applyChartAddElementChoice("dataLabels:outsideEnd", {});
    expect(next.dataLabels?.position).toBe("outsideEnd");
    expect(next.dataLabels?.showLeaderLines).toBe(true);
  });

  it("WithParts sincroniza chartParts com options", () => {
    const result = applyChartAddElementChoiceWithParts("legend:bottom", {}, null);
    expect(result.options.legendPosition).toBe("bottom");
    expect(result.parts.legend?.visible).toBe(true);
  });
});

describe("isChartAddElementChoiceActive", () => {
  it("marca Inferior quando legendPosition é bottom", () => {
    const opts = mergeSeriesChartOptions({ showLegend: true, legendPosition: "bottom" });
    expect(isChartAddElementChoiceActive("legend:bottom", opts)).toBe(true);
    expect(isChartAddElementChoiceActive("legend:left", opts)).toBe(false);
  });

  it("marca Nenhum quando ambos eixos off", () => {
    const opts = mergeSeriesChartOptions({
      showAxes: false,
      showXAxisLabels: false,
      showYAxisLabels: false,
    });
    expect(isChartAddElementChoiceActive("axes:none", opts)).toBe(true);
    expect(isChartAddElementChoiceActive("axes:x", opts)).toBe(false);
  });

  it("marca legenda left", () => {
    const opts = mergeSeriesChartOptions({ showLegend: true, legendPosition: "left" });
    expect(isChartAddElementChoiceActive("legend:left", opts)).toBe(true);
    expect(isChartAddElementChoiceActive("legend:none", opts)).toBe(false);
  });
});
