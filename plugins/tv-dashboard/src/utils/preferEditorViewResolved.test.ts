import { describe, expect, it } from "vitest";

import { preferEditorViewResolved } from "./preferEditorViewResolved";

describe("preferEditorViewResolved", () => {
  it("chart: usa linked quando tem pontos", () => {
    const out = preferEditorViewResolved({
      blockType: "chart_view",
      linked: {
        serverProjectionApplied: true,
        chart: { points: [{ label: "a", value: 1 }] },
      },
      source: { chart: { points: [{ label: "b", value: 99 }] } },
    });
    expect(out?.chart?.points?.[0]?.value).toBe(1);
  });

  it("chart: cai na fonte quando bake ligado veio vazio", () => {
    const out = preferEditorViewResolved({
      blockType: "chart_view",
      linked: {
        serverProjectionApplied: true,
        serverDisplayApplied: true,
        chart: { points: [] },
      },
      source: { chart: { points: [{ label: "dia", value: 10 }] } },
    });
    expect(out?.chart?.points?.[0]?.value).toBe(10);
  });

  it("text: prefere displayText do linked", () => {
    const out = preferEditorViewResolved({
      blockType: "text",
      linked: { displayText: "R$ 10,00", serverDisplayApplied: true },
      source: { kpi: { value: 10 } },
    });
    expect(out?.displayText).toBe("R$ 10,00");
  });

  it("kpi: prefere displayValue do linked", () => {
    const out = preferEditorViewResolved({
      blockType: "kpi_view",
      linked: { kpi: { value: 1, displayValue: "1,0%" }, serverDisplayApplied: true },
      source: { kpi: { value: 1 } },
    });
    expect(out?.kpi?.displayValue).toBe("1,0%");
  });
});
