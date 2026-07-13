import { describe, expect, it } from "vitest";
import { mergeComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

import {
  CHART_QUICK_LAYOUTS,
  applyChartQuickLayout,
} from "./chartQuickLayouts";

describe("chartQuickLayouts", () => {
  it("expõe presets com toggles de elementos", () => {
    expect(CHART_QUICK_LAYOUTS.length).toBeGreaterThanOrEqual(4);
    for (const layout of CHART_QUICK_LAYOUTS) {
      expect(layout.elements).toBeTruthy();
      expect(layout.label.length).toBeGreaterThan(0);
    }
  });

  it("applyChartQuickLayout — mínimo desliga título e legenda", () => {
    const layout = CHART_QUICK_LAYOUTS.find((item) => item.id === "minimal");
    expect(layout).toBeTruthy();
    const base = mergeComunicadoChartOptions({
      showTitle: true,
      showLegend: true,
      legendPosition: "bottom",
    });
    const next = applyChartQuickLayout(layout!, base, null);
    expect(next.options.showTitle).toBe(false);
    expect(next.options.showLegend === false || next.options.legendPosition === "hidden").toBe(
      true,
    );
  });

  it("applyChartQuickLayout — completo liga tabela e legenda bottom", () => {
    const layout = CHART_QUICK_LAYOUTS.find((item) => item.id === "full_with_table");
    expect(layout).toBeTruthy();
    const base = mergeComunicadoChartOptions({ showDataTable: false });
    const next = applyChartQuickLayout(layout!, base, null);
    expect(next.options.showDataTable).toBe(true);
    expect(next.options.legendPosition).toBe("bottom");
  });
});
