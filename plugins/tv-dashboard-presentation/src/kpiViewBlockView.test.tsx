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
  it("renderiza ícone Gauge por padrão no padrão visual do KPI", () => {
    const block = kpiWithResolved(createKpiViewBlock({ title: "Consumo" }));
    const { container } = render(<KpiViewBlockView block={block} />);
    expect(container.querySelector(".delpi-kpi-icon")).toBeTruthy();
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

  it("não renderiza ícone quando showIcon=false", () => {
    const block = kpiWithResolved(
      createKpiViewBlock({ title: "Consumo", showIcon: false }),
    );
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

  it("renderiza grade quando há várias kpiMetrics", () => {
    const base = createKpiViewBlock();
    if (base.type !== "kpi_view") throw new Error("expected kpi_view");
    const block: ComunicadoKpiViewBlock = {
      ...base,
      dataSourceId: "src-1",
      resolved: {
        kpi: { value: 42, label: "Total de LMPs" },
        kpiMetrics: [
          { field: "total_lmps", value: 42, label: "Total de LMPs" },
          { field: "avg_lead_time", value: 3.2, label: "Lead time médio" },
        ],
      },
    };
    const { container } = render(<KpiViewBlockView block={block} />);
    expect(container.querySelector(".tdp-kpi-view--multi")).toBeTruthy();
    expect(screen.getByText("Total de LMPs")).toBeTruthy();
    expect(screen.getByText("Lead time médio")).toBeTruthy();
    expect(screen.getByText("42")).toBeTruthy();
    expect(screen.getByText("3.2")).toBeTruthy();
  });

  it("cai na tabela anexada quando não há valor numérico", () => {
    const base = createKpiViewBlock({ title: "Travamento" });
    if (base.type !== "kpi_view") throw new Error("expected kpi_view");
    const block: ComunicadoKpiViewBlock = {
      ...base,
      dataSourceId: "src-1",
      resolved: {
        kpi: { value: null, label: "Travamento" },
        table: {
          rows: [
            { branch: "02", component_code: "1001" },
            { branch: "02", component_code: "1002" },
          ],
          columns: [
            { key: "branch", label: "Filial" },
            { key: "component_code", label: "Componente" },
          ],
        },
      },
    };
    const { container } = render(<KpiViewBlockView block={block} />);
    expect(container.querySelector(".tdp-data-block--table")).toBeTruthy();
    expect(screen.getByText("1001")).toBeTruthy();
    expect(screen.queryByText("Fonte sem valor numérico")).toBeNull();
  });
});
