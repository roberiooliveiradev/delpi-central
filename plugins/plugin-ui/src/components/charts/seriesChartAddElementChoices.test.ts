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

  it("axes:x desliga só o horizontal e preserva o vertical", () => {
    const base = mergeSeriesChartOptions({
      showAxes: true,
      showXAxisLabels: true,
      showYAxisLabels: true,
    });
    const next = applyChartAddElementChoice("axes:x", base);
    expect(next.showXAxisLabels).toBe(false);
    expect(next.showYAxisLabels).toBe(true);
    expect(next.showAxes).toBe(true);
  });

  it("axes:y desliga só o vertical e preserva o horizontal", () => {
    const base = mergeSeriesChartOptions({
      showAxes: true,
      showXAxisLabels: true,
      showYAxisLabels: true,
    });
    const next = applyChartAddElementChoice("axes:y", base);
    expect(next.showYAxisLabels).toBe(false);
    expect(next.showXAxisLabels).toBe(true);
    expect(next.showAxes).toBe(true);
  });

  it("axes:x WithParts não apaga axis:y no round-trip", () => {
    const base = mergeSeriesChartOptions({});
    const offX = applyChartAddElementChoiceWithParts("axes:x", base, null);
    expect(offX.options.showXAxisLabels).toBe(false);
    expect(offX.options.showYAxisLabels).toBe(true);
    expect(offX.options.showAxes).toBe(true);
    expect(offX.parts["axis:x"]?.visible).toBe(false);
    expect(offX.parts["axis:y"]?.visible).toBe(true);
    expect(offX.parts.axes?.visible).toBe(true);
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

  it("goalLine:show liga linha de meta", () => {
    const next = applyChartAddElementChoice("goalLine:show", { showGoalLine: false });
    expect(next.showGoalLine).toBe(true);
    expect(isChartAddElementChoiceActive("goalLine:show", next)).toBe(true);
    const off = applyChartAddElementChoice("goalLine:none", next);
    expect(off.showGoalLine).toBe(false);
  });

  it("goalLine:none/show sincroniza gaugeGoalMarker nas parts", () => {
    const shown = applyChartAddElementChoiceWithParts("goalLine:show", { showGoalLine: false }, null);
    expect(shown.options.showGoalLine).toBe(true);
    expect(shown.parts.gaugeGoalMarker?.visible).toBe(true);
    const hidden = applyChartAddElementChoiceWithParts(
      "goalLine:none",
      shown.options,
      shown.parts,
    );
    expect(hidden.options.showGoalLine).toBe(false);
    expect(hidden.parts.gaugeGoalMarker?.visible).toBe(false);
  });

  it("gaugeLabel:none/show liga o rótulo do velocímetro", () => {
    const off = applyChartAddElementChoiceWithParts("gaugeLabel:none", {}, null);
    expect(off.options.showGaugeLabel).toBe(false);
    expect(off.parts.gaugeLabel?.visible).toBe(false);
    expect(isChartAddElementChoiceActive("gaugeLabel:none", off.options)).toBe(true);
    const on = applyChartAddElementChoiceWithParts(
      "gaugeLabel:show",
      { showGaugeLabel: false },
      null,
    );
    expect(on.options.showGaugeLabel).toBe(true);
    expect(on.parts.gaugeLabel?.visible).toBe(true);
    expect(isChartAddElementChoiceActive("gaugeLabel:show", on.options)).toBe(true);
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
