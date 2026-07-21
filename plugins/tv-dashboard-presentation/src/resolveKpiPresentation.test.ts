import { describe, expect, it } from "vitest";

import { createKpiViewBlock, parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";
import { isDataViewBlockType } from "./comunicadoDataArchitecture";
import { resolveKpiViewPresentation } from "./resolveKpiPresentation";

describe("kpi_view", () => {
  it("é data view e serializa kpiOptions", () => {
    expect(isDataViewBlockType("kpi_view")).toBe(true);
    const block = createKpiViewBlock({ title: "OEE", iconName: "Gauge", showIcon: true });
    expect(block.type).toBe("kpi_view");
    const serialized = serializeComunicadoConfig({ version: 5, blocks: [block] });
    const parsed = parseComunicadoConfig(serialized);
    const kpi = parsed.blocks?.[0];
    expect(kpi?.type).toBe("kpi_view");
    if (kpi?.type === "kpi_view") {
      expect(kpi.kpiOptions?.title).toBe("OEE");
      expect(kpi.kpiOptions?.iconName).toBe("Gauge");
      expect(kpi.kpiParts?.title?.content).toBe("OEE");
      expect(kpi.kpiParts?.icon?.visible).not.toBe(false);
    }
  });

  it("sincroniza showIcon=false a partir de parts.icon.visible no parse", () => {
    const parsed = parseComunicadoConfig({
      version: 5,
      blocks: [
        {
          id: "k1",
          type: "kpi_view",
          frame: { x: 8, y: 28, w: 32, h: 24 },
          style: { zIndex: 2 },
          kpiOptions: { title: "Consumo", iconName: "Gauge", showIcon: true },
          kpiParts: {
            icon: { visible: false, style: { fill: "#ffffff" } },
          },
        },
      ],
    });
    const kpi = parsed.blocks?.[0];
    expect(kpi?.type).toBe("kpi_view");
    if (kpi?.type === "kpi_view") {
      expect(kpi.kpiOptions?.showIcon).toBe(false);
      expect(kpi.kpiParts?.icon?.visible).toBe(false);
    }
  });

  it("liga ícone Gauge por padrão ao criar kpi_view", () => {
    const block = createKpiViewBlock({ title: "Consumo" });
    if (block.type !== "kpi_view") throw new Error("kpi");
    expect(block.kpiOptions?.showIcon).toBe(true);
    expect(block.kpiOptions?.iconName).toBe("Gauge");
    expect(block.kpiParts?.icon?.visible).not.toBe(false);
    expect(block.frame).toEqual({ x: 8, y: 34, w: 18, h: 12 });
  });

  it("resolve apresentação com regras de cor", () => {
    const presentation = resolveKpiViewPresentation(
      { kpi: { value: 92, label: "OEE" }, label: "OEE" },
      {
        colorRules: [
          { op: "gte", value: 90, tone: "positive" },
          { op: "lt", value: 70, tone: "negative" },
        ],
      },
    );
    expect(presentation.label).toBe("OEE");
    expect(presentation.tone).toBe("positive");
    expect(presentation.valueText).toContain("92");
  });

  it("override por métrica sobrescreve formato e regras", () => {
    const presentation = resolveKpiViewPresentation(
      { kpi: { value: 0.85, label: "OTD" } },
      { valueFormat: "raw", colorRules: [{ op: "gte", value: 0.9, tone: "positive" }] },
      {
        format: "percent",
        label: "OTD médio",
        colorRules: [{ op: "gte", value: 0.8, tone: "positive" }],
      },
    );
    expect(presentation.label).toBe("OTD médio");
    expect(presentation.tone).toBe("positive");
    expect(presentation.valueText).toContain("%");
  });
});
