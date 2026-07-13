import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createKpiViewBlock } from "./comunicadoHelpers";
import { KpiViewBlockView } from "./kpiViewBlockView";
import type { ComunicadoKpiViewBlock } from "./comunicadoTypes";

function kpiWithResolved(block: ReturnType<typeof createKpiViewBlock>): ComunicadoKpiViewBlock {
  if (block.type !== "kpi_view") throw new Error("expected kpi_view");
  return {
    ...block,
    resolved: { kpi: { value: 10, label: "Consumo" }, label: "Consumo" },
  };
}

describe("KpiViewBlockView icon visibility", () => {
  it("não renderiza ícone Gauge por padrão (opt-in)", () => {
    const block = kpiWithResolved(createKpiViewBlock({ title: "Consumo" }));
    const { container } = render(<KpiViewBlockView block={block} />);
    expect(container.querySelector(".delpi-kpi-icon")).toBeNull();
    expect(screen.getByText("10")).toBeTruthy();
  });

  it("não renderiza ícone quando parts.icon.visible=false mesmo com showIcon true legado", () => {
    const base = kpiWithResolved(
      createKpiViewBlock({ title: "Consumo", iconName: "Gauge", showIcon: true }),
    );
    const block: ComunicadoKpiViewBlock = {
      ...base,
      kpiOptions: { ...base.kpiOptions, showIcon: true, iconName: "Gauge" },
      kpiParts: {
        ...base.kpiParts,
        icon: { visible: false, style: { fill: "#ffffff" } },
      },
    };
    const { container } = render(<KpiViewBlockView block={block} />);
    expect(container.querySelector(".delpi-kpi-icon")).toBeNull();
  });

  it("renderiza ícone quando showIcon e parts permitem", () => {
    const block = kpiWithResolved(
      createKpiViewBlock({ title: "Consumo", iconName: "Gauge", showIcon: true }),
    );
    const { container } = render(<KpiViewBlockView block={block} />);
    expect(container.querySelector(".delpi-kpi-icon")).toBeTruthy();
  });
});
