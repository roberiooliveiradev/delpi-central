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

  it("caption da meta usa content e tipografia de gaugeGoalMarker", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        chartParts={{
          gaugeGoalMarker: {
            visible: true,
            content: "Alvo",
            style: { fontSize: 18, color: "rgb(1, 2, 3)" },
          },
        }}
      />,
    );
    const caption = container.querySelector(".delpi-ui-speedometer-gauge__goal") as HTMLElement;
    expect(caption.textContent).toMatch(/Alvo:\s*95/);
    expect(caption.style.fontSize).toBe("18px");
    expect(caption.style.color).toBe("rgb(1, 2, 3)");
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

  it("oculta marcador e caption quando gaugeGoalMarker.visible é false", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        label="OTD"
        chartParts={{ gaugeGoalMarker: { visible: false } }}
      />,
    );
    expect(container.querySelector(".delpi-ui-speedometer-gauge__goal")).toBeNull();
    expect(container.querySelector(".delpi-ui-speedometer-gauge__goal-marker")).toBeNull();
  });

  it("oculta legenda quando legend.visible é false", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        showZonesLegend
        chartParts={{ legend: { visible: false } }}
      />,
    );
    expect(container.querySelector(".delpi-ui-speedometer-gauge__legend")).toBeNull();
  });

  it("aplica frame % na legenda e handles quando selecionada", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        interaction={{
          selectedPart: { kind: "legend" },
          onPartPointerDown: () => undefined,
          onPartResizePointerDown: () => undefined,
        }}
        chartParts={{
          legend: { visible: true, frame: { x: 20, y: 40, w: 60, h: 25 } },
        }}
      />,
    );
    const legend = container.querySelector(".delpi-ui-speedometer-gauge__legend") as HTMLElement;
    expect(legend.style.left).toBe("20%");
    expect(legend.style.top).toBe("40%");
    expect(legend.style.width).toBe("60%");
    expect(legend.style.position).toBe("absolute");
    expect(
      container.querySelector('[aria-label="Redimensionar canto inferior direito"]'),
    ).toBeTruthy();
  });

  it("aplica frame % no rótulo e na caption da meta", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        label="OTD SC"
        interaction={{
          selectedPart: { kind: "gaugeLabel" },
          onPartPointerDown: () => undefined,
          onPartResizePointerDown: () => undefined,
        }}
        chartParts={{
          gaugeLabel: { visible: true, frame: { x: 15, y: 55, w: 70, h: 12 } },
          gaugeGoalMarker: {
            visible: true,
            frame: { x: 25, y: 68, w: 50, h: 10 },
          },
        }}
      />,
    );
    const label = container.querySelector(".delpi-ui-speedometer-gauge__label") as HTMLElement;
    expect(label.style.left).toBe("15%");
    expect(label.style.width).toBe("70%");
    expect(
      container.querySelector('[aria-label="Redimensionar canto inferior direito"]'),
    ).toBeTruthy();
    const caption = container.querySelector(".delpi-ui-speedometer-gauge__goal") as HTMLElement;
    expect(caption.style.left).toBe("25%");
    expect(caption.style.top).toBe("68%");
  });

  it("seleção HTML usa tokens da série (sem outline inline nas zonas)", () => {
    const { container } = render(
      <SpeedometerGauge
        value={98.5}
        goal={95}
        label="OTD"
        interaction={{
          selectedPart: { kind: "gaugeNeedle" },
          onPartPointerDown: () => undefined,
        }}
      />,
    );
    const needle = container.querySelector('[data-chart-part="gaugeNeedle"]')!;
    expect(needle.getAttribute("aria-selected")).toBe("true");
    const outlined = container.querySelector('[style*="outline"]');
    expect(outlined).toBeNull();
  });

  it("fillHost usa SVG 100%", () => {
    const { container } = render(
      <SpeedometerGauge value={90} label="Fluid" fillHost />,
    );
    const svg = container.querySelector(".delpi-ui-speedometer-gauge__svg");
    expect(svg?.getAttribute("width")).toBe("100%");
    expect(svg?.getAttribute("height")).toBe("100%");
    expect(container.querySelector('[data-fill-host="true"]')).toBeTruthy();
  });
});
