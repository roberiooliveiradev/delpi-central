import { render } from "@testing-library/react";
import { beforeAll, describe, expect, it } from "vitest";

import { AreaSeriesChart } from "../AreaSeriesChart";
import { LineSeriesChart } from "../LineSeriesChart";

beforeAll(() => {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
});

const POINTS = [
  { label: "A", value: 10 },
  { label: "B", value: 20 },
  { label: "C", value: 15 },
  { label: "D", value: 5 },
];

const BASE_OPTIONS = { showTitle: false, showLegend: false } as const;

describe("AreaSeriesChart", () => {
  it("pinta a área do primitivo de série", () => {
    const { container } = render(<AreaSeriesChart points={POINTS} options={BASE_OPTIONS} />);
    expect(container.querySelector(".delpi-ui-series-chart__series-area")).not.toBeNull();
  });
});

describe("areaFillGradient", () => {
  it("preenche com degradê e deixa a base transparente quando ligado", () => {
    const { container } = render(
      <AreaSeriesChart
        points={POINTS}
        options={{ ...BASE_OPTIONS, areaFillGradient: true, categoryColors: ["#1d4ed8"] }}
      />,
    );

    const gradient = container.querySelector("linearGradient");
    expect(gradient).not.toBeNull();

    const stops = Array.from(gradient!.querySelectorAll("stop"));
    expect(stops).toHaveLength(3);
    expect(stops.at(-1)?.getAttribute("stop-opacity")).toBe("0");
    // Degradê nasce da cor efetiva da série — a mesma que pinta o contorno.
    expect(stops[0]?.getAttribute("stop-color")).toBe("#1d4ed8");
    expect(
      container.querySelector(".delpi-ui-series-chart__series-area polyline")?.getAttribute("stroke"),
    ).toBe("#1d4ed8");

    const polygon = container.querySelector(".delpi-ui-series-chart__series-area polygon");
    expect(polygon?.getAttribute("fill")).toBe(`url(#${gradient!.id})`);
  });

  it("mantém preenchimento chapado por padrão", () => {
    const { container } = render(<AreaSeriesChart points={POINTS} options={BASE_OPTIONS} />);

    expect(container.querySelector("linearGradient")).toBeNull();
    const polygon = container.querySelector(".delpi-ui-series-chart__series-area polygon");
    expect(polygon?.getAttribute("fill")).not.toMatch(/^url\(/);
  });

  it("dá id próprio a cada gráfico, para dois degradês não colidirem na mesma página", () => {
    const { container } = render(
      <>
        <AreaSeriesChart points={POINTS} options={{ ...BASE_OPTIONS, areaFillGradient: true }} />
        <AreaSeriesChart points={POINTS} options={{ ...BASE_OPTIONS, areaFillGradient: true }} />
      </>,
    );

    const ids = Array.from(container.querySelectorAll("linearGradient")).map((node) => node.id);
    expect(ids).toHaveLength(2);
    expect(new Set(ids).size).toBe(2);
  });
});

describe("markerMode", () => {
  it("pinta um marcador por ponto por padrão", () => {
    const { container } = render(
      <LineSeriesChart points={POINTS} options={{ ...BASE_OPTIONS, showMarkers: true }} />,
    );
    expect(container.querySelectorAll(".delpi-ui-series-chart__series-marker")).toHaveLength(
      POINTS.length,
    );
  });

  it("pinta só o último ponto em modo last", () => {
    const { container } = render(
      <LineSeriesChart
        points={POINTS}
        options={{ ...BASE_OPTIONS, showMarkers: true, markerMode: "last" }}
      />,
    );
    expect(container.querySelectorAll(".delpi-ui-series-chart__series-marker")).toHaveLength(1);
  });

  it("em modo last ignora buraco no fim da série e marca o último valor real", () => {
    const { container } = render(
      <LineSeriesChart
        points={[...POINTS, { label: "E", value: null }]}
        options={{ ...BASE_OPTIONS, showMarkers: true, markerMode: "last" }}
      />,
    );

    const markers = container.querySelectorAll(".delpi-ui-series-chart__series-marker");
    expect(markers).toHaveLength(1);

    const allMarkers = render(
      <LineSeriesChart
        points={[...POINTS, { label: "E", value: null }]}
        options={{ ...BASE_OPTIONS, showMarkers: true }}
      />,
    ).container.querySelectorAll(".delpi-ui-series-chart__series-marker");
    const lastValued = allMarkers[POINTS.length - 1];
    expect(markers[0]?.getAttribute("cx")).toBe(lastValued?.getAttribute("cx"));
  });

  it("markerMode não ressuscita marcador com showMarkers desligado", () => {
    const { container } = render(
      <LineSeriesChart
        points={POINTS}
        options={{ ...BASE_OPTIONS, showMarkers: false, markerMode: "last" }}
      />,
    );
    expect(container.querySelectorAll(".delpi-ui-series-chart__series-marker")).toHaveLength(0);
  });
});
