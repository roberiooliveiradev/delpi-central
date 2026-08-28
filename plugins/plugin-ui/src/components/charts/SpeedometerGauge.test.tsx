import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SpeedometerGauge } from "./SpeedometerGauge";

afterEach(() => {
  cleanup();
});

describe("SpeedometerGauge", () => {
  it("renderiza valor formatado e label", () => {
    render(<SpeedometerGauge value={98.8} label="OTD Espírito Santo" />);
    expect(screen.getByRole("img", { name: /OTD Espírito Santo/i })).toBeTruthy();
    expect(screen.getByText("98,8")).toBeTruthy();
    expect(screen.getByText("OTD Espírito Santo")).toBeTruthy();
  });

  it("aplica tom success para percentual alto", () => {
    const { container } = render(<SpeedometerGauge value={99.6} label="SC" />);
    expect(container.querySelector('[data-tone="success"]')).toBeTruthy();
  });

  it("aplica tom danger abaixo de 90%", () => {
    const { container } = render(<SpeedometerGauge value={85} label="Baixo" />);
    expect(container.querySelector('[data-tone="danger"]')).toBeTruthy();
  });

  it("mostra tooltip interativo no hover só com tip explícito", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        label="OTD Santa Catarina"
        tip="OTD SC no período"
      />,
    );
    const gauge = container.querySelector('[role="img"]')!;
    fireEvent.mouseEnter(gauge);
    expect(screen.getByRole("tooltip").textContent).toContain("OTD SC no período");
  });

  it("não mostra tooltip no hover sem tip explícito", () => {
    const { container } = render(<SpeedometerGauge value={98.5} label="Sem tip hover" />);
    const gauge = container.querySelector('[role="img"]')!;
    fireEvent.mouseEnter(gauge);
    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("expõe data-chart-part nas subpartes do velocímetro", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        label="OTD"
        interaction={{
          onPartPointerDown: () => undefined,
        }}
      />,
    );
    expect(container.querySelector('[data-chart-part="gaugeNeedle"]')).toBeTruthy();
    expect(container.querySelector('[data-chart-part="gaugeValue"]')).toBeTruthy();
    expect(container.querySelector('[data-chart-part="gaugeZone:2"]')).toBeTruthy();
    expect(container.querySelector('[data-chart-part="legend"]')).toBeTruthy();
  });

  it("mostra indicador e valor da meta", () => {
    const { container } = render(
      <SpeedometerGauge value={98.5} goal={95} label="OTD SC" />,
    );
    expect(container.querySelector(".delpi-ui-speedometer-gauge__goal")?.textContent).toMatch(
      /Meta:\s*95/,
    );
    expect(container.querySelector("[data-goal='95']")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-speedometer-gauge__goal-marker")).toBeTruthy();
    // texto da meta só no caption — não colado no arco
    expect(container.querySelector(".delpi-ui-speedometer-gauge__goal-marker text")).toBeNull();
  });

  it("com meta, faixas usam a meta como limiar de sucesso", () => {
    const { container } = render(<SpeedometerGauge value={96} goal={95} />);
    expect(container.querySelector("[data-zone-warning='0.95']")).toBeTruthy();
    const successLegend = container.querySelector(
      ".delpi-ui-speedometer-gauge__legend-item[data-tone='success']",
    );
    expect(successLegend?.textContent?.replace(/\s+/g, " ")).toMatch(/≥\s*95%/);
  });

  it("mostra traço quando valor é nulo", () => {
    render(<SpeedometerGauge value={null} label="Sem dados" unit="%" />);
    expect(screen.getByText("—")).toBeTruthy();
  });

  it("accentColor pinta agulha e hub", () => {
    const { container } = render(
      <SpeedometerGauge value={90} label="Accent" accentColor="#112233" />,
    );
    const needle = container.querySelector(".delpi-ui-speedometer-gauge__needle");
    const hub = container.querySelector(".delpi-ui-speedometer-gauge__hub");
    expect(needle?.getAttribute("stroke")).toBe("#112233");
    expect(hub?.getAttribute("fill")).toBe("#112233");
  });

  it("pointerDown/doubleClick nas partes disparam o ChartPartRef correto", () => {
    const onPartPointerDown = vi.fn();
    const onPartDoubleClick = vi.fn();
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        label="OTD"
        interaction={{ onPartPointerDown, onPartDoubleClick }}
      />,
    );

    fireEvent.pointerDown(container.querySelector('[data-chart-part="gaugeNeedle"]')!);
    expect(onPartPointerDown).toHaveBeenCalledWith(
      { kind: "gaugeNeedle" },
      expect.anything(),
    );

    fireEvent.doubleClick(container.querySelector('[data-chart-part="gaugeZone:0"]')!);
    expect(onPartDoubleClick).toHaveBeenCalledWith(
      { kind: "gaugeZone", zoneIndex: 0 },
      expect.anything(),
    );

    fireEvent.pointerDown(container.querySelector('[data-chart-part="gaugeGoalMarker"]')!);
    expect(onPartPointerDown).toHaveBeenCalledWith(
      { kind: "gaugeGoalMarker" },
      expect.anything(),
    );

    expect(container.querySelector('[data-interactive="true"]')).toBeTruthy();
    expect(
      container.querySelector('[data-chart-part="gaugeNeedle"] line[stroke="transparent"]'),
    ).toBeTruthy();
  });
});
