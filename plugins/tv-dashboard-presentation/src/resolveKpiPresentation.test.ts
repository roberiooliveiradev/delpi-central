import { describe, expect, it } from "vitest";

import { createKpiViewBlock, parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";
import { isDataViewBlockType } from "./comunicadoDataArchitecture";
import { resolveKpiViewPresentation } from "./resolveKpiPresentation";

describe("kpi_view", () => {
  it("é data view e serializa kpiOptions", () => {
    expect(isDataViewBlockType("kpi_view")).toBe(true);
    const block = createKpiViewBlock({ title: "OEE", iconName: "Gauge" });
    expect(block.type).toBe("kpi_view");
    const serialized = serializeComunicadoConfig({ version: 5, blocks: [block] });
    const parsed = parseComunicadoConfig(serialized);
    const kpi = parsed.blocks?.[0];
    expect(kpi?.type).toBe("kpi_view");
    if (kpi?.type === "kpi_view") {
      expect(kpi.kpiOptions?.title).toBe("OEE");
      expect(kpi.kpiOptions?.iconName).toBe("Gauge");
    }
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
});
