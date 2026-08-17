import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MetricStrip, createDashboardMetricStrip, metricStripBemClasses } from "./MetricStrip";

describe("MetricStrip", () => {
  it("emite dual-class BEM", () => {
    const cn = metricStripBemClasses("cm");
    expect(cn.root).toContain("cm-metric-strip");
    expect(cn.root).toContain("delpi-ui-metric-strip");
    expect(cn.item).toContain("delpi-ui-metric-strip__item");
  });

  it("renderiza itens em densidade compact", () => {
    const cn = metricStripBemClasses("cm");
    const { container } = render(
      <MetricStrip
        classNames={cn}
        density="compact"
        aria-label="Resumo"
        items={[
          { id: "a", label: "Carteiras", value: "3" },
          { id: "b", label: "Ativas", value: "2" },
        ]}
      />,
    );
    expect(container.querySelector(".delpi-ui-metric-strip--compact")).toBeTruthy();
    expect(screen.getByText("Carteiras")).toBeTruthy();
    expect(screen.getByText("3")).toBeTruthy();
  });

  it("createDashboardMetricStrip monta strip sem classNames manuais", () => {
    const Strip = createDashboardMetricStrip({ prefix: "cm" });
    const { container } = render(<Strip items={[{ id: "x", label: "X", value: "1" }]} />);
    expect(container.querySelector(".cm-metric-strip")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-metric-strip--compact")).toBeTruthy();
  });
});
