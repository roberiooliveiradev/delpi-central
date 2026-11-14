import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ComparativeAreaChart,
  comparativeAreaChartBemClasses,
  type ComparativeAreaChartPoint,
  type ComparativeAreaChartSeries,
} from "./ComparativeAreaChart";

const SERIES: ComparativeAreaChartSeries[] = [
  { dataKey: "current", name: "Atual", color: "#089bdb" },
  { dataKey: "previous", name: "Anterior", color: "#64748b", fillOpacity: 0.2 },
];

const DATA: ComparativeAreaChartPoint[] = [
  { name: "01", current: 3, previous: 1 },
  { name: "02", current: 6, previous: 2 },
  { name: "03", current: 4, previous: 5 },
];

class StubResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeEach(() => {
  document.documentElement.setAttribute("data-theme", "light");
  vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(600);
  vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(240);
  vi.stubGlobal("ResizeObserver", StubResizeObserver);
  vi.stubGlobal(
    "matchMedia",
    (query: string) =>
      ({
        matches: false,
        media: query,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      }) as unknown as MediaQueryList,
  );
});

afterEach(() => {
  cleanup();
  document.documentElement.removeAttribute("data-theme");
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

/**
 * Baseline (characterization) for ComparativeAreaChart before additive evolution.
 * Created because no test existed for this component.
 */
describe("ComparativeAreaChart — characterization (no new props)", () => {
  it("emits dual-class names", () => {
    const cn = comparativeAreaChartBemClasses("itp");
    expect(cn.root).toBe("itp-comparative-area-chart delpi-ui-comparative-area-chart");
    expect(cn.canvas).toContain("delpi-ui-comparative-area-chart__canvas");
    expect(cn.tooltip).toContain("delpi-ui-comparative-area-chart__tooltip");
    expect(cn.empty).toContain("delpi-ui-comparative-area-chart__empty");
  });

  it("renders nothing when data is empty and no emptyMessage", () => {
    const { container } = render(<ComparativeAreaChart data={[]} series={SERIES} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the empty message when data is empty", () => {
    const { container } = render(
      <ComparativeAreaChart data={[]} series={SERIES} emptyMessage="Sem dados" prefix="itp" />,
    );
    const empty = container.querySelector(".delpi-ui-comparative-area-chart__empty");
    expect(empty?.textContent).toBe("Sem dados");
  });

  it("renders root with theme marker, canvas height and className", () => {
    const { container } = render(
      <ComparativeAreaChart
        data={DATA}
        series={SERIES}
        prefix="itp"
        className="extra"
        height={300}
      />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("itp-comparative-area-chart");
    expect(root.className).toContain("delpi-ui-comparative-area-chart");
    expect(root.className).toContain("extra");
    expect(root.getAttribute("data-theme")).toBe("light");
    const canvas = container.querySelector(".delpi-ui-comparative-area-chart__canvas") as HTMLElement;
    expect(canvas.style.height).toBe("300px");
  });

  it("uses default height 240 and follows dark theme", () => {
    document.documentElement.setAttribute("data-theme", "dark");
    const { container } = render(<ComparativeAreaChart data={DATA} series={SERIES} />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.getAttribute("data-theme")).toBe("dark");
    const canvas = container.querySelector(".delpi-ui-comparative-area-chart__canvas") as HTMLElement;
    expect(canvas.style.height).toBe("240px");
  });

  it("draws one area per series with the series stroke color", () => {
    const { container } = render(<ComparativeAreaChart data={DATA} series={SERIES} />);
    expect(container.querySelector("svg")).toBeTruthy();
    const strokes = Array.from(container.querySelectorAll("path.recharts-area-curve")).map((p) =>
      p.getAttribute("stroke"),
    );
    expect(strokes).toEqual(["#089bdb", "#64748b"]);
  });

  it("is not interactive without new props: no focusable point targets and no selection band", () => {
    const { container } = render(<ComparativeAreaChart data={DATA} series={SERIES} />);
    expect(container.querySelectorAll("button")).toHaveLength(0);
    expect(container.querySelector('[role="group"]')).toBeNull();
    expect(container.querySelector(".delpi-ui-comparative-area-chart__selection-band")).toBeNull();
  });
});

describe("ComparativeAreaChart — additive evolution (point selection)", () => {
  it("onPointSelect renders one keyboard target per point, named with series values", () => {
    render(<ComparativeAreaChart data={DATA} series={SERIES} onPointSelect={() => undefined} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(3);
    expect(buttons[0]?.getAttribute("aria-label")).toMatch(/^01: Atual: .*; Anterior: /);
  });

  it("pointAriaLabel overrides the default name", () => {
    render(
      <ComparativeAreaChart
        data={DATA}
        series={SERIES}
        onPointSelect={() => undefined}
        pointAriaLabel={(point) => `Dia ${point.name}`}
      />,
    );
    expect(screen.getByRole("button", { name: "Dia 02" })).toBeTruthy();
  });

  it("click selects the point with its index", () => {
    const onPointSelect = vi.fn();
    render(<ComparativeAreaChart data={DATA} series={SERIES} onPointSelect={onPointSelect} />);
    fireEvent.click(screen.getByRole("button", { name: /^03:/ }));
    expect(onPointSelect).toHaveBeenCalledTimes(1);
    expect(onPointSelect).toHaveBeenCalledWith(DATA[2], 2);
  });

  it("Enter selects exactly once (no duplicate native click)", () => {
    const onPointSelect = vi.fn();
    render(<ComparativeAreaChart data={DATA} series={SERIES} onPointSelect={onPointSelect} />);
    const first = screen.getAllByRole("button")[0]!;
    fireEvent.keyDown(first, { key: "Enter" });
    expect(onPointSelect).toHaveBeenCalledTimes(1);
    expect(onPointSelect).toHaveBeenCalledWith(DATA[0], 0);
  });

  it("ArrowRight / ArrowLeft / Home / End move focus across points with roving tabindex", () => {
    render(<ComparativeAreaChart data={DATA} series={SERIES} onPointSelect={() => undefined} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.map((b) => b.getAttribute("tabindex"))).toEqual(["0", "-1", "-1"]);
    buttons[0]!.focus();
    fireEvent.keyDown(buttons[0]!, { key: "ArrowRight" });
    expect(document.activeElement).toBe(buttons[1]);
    expect(buttons.map((b) => b.getAttribute("tabindex"))).toEqual(["-1", "0", "-1"]);
    fireEvent.keyDown(buttons[1]!, { key: "End" });
    expect(document.activeElement).toBe(buttons[2]);
    fireEvent.keyDown(buttons[2]!, { key: "ArrowRight" });
    expect(document.activeElement).toBe(buttons[2]);
    fireEvent.keyDown(buttons[2]!, { key: "ArrowLeft" });
    expect(document.activeElement).toBe(buttons[1]);
    fireEvent.keyDown(buttons[1]!, { key: "Home" });
    expect(document.activeElement).toBe(buttons[0]);
  });

  it("selectedName draws the selection band and marks the target aria-pressed", () => {
    const { container } = render(
      <ComparativeAreaChart
        data={DATA}
        series={SERIES}
        onPointSelect={() => undefined}
        selectedName="02"
      />,
    );
    expect(container.querySelector(".delpi-ui-comparative-area-chart__selection-band")).toBeTruthy();
    const pressed = screen.getAllByRole("button").map((b) => b.getAttribute("aria-pressed"));
    expect(pressed).toEqual(["false", "true", "false"]);
  });

  it("selectedName works without onPointSelect (band only, still no buttons)", () => {
    const { container } = render(
      <ComparativeAreaChart data={DATA} series={SERIES} selectedName="01" />,
    );
    expect(container.querySelector(".delpi-ui-comparative-area-chart__selection-band")).toBeTruthy();
    expect(container.querySelectorAll("button")).toHaveLength(0);
  });

  it("negative: unknown or null selectedName draws no band", () => {
    const { container, rerender } = render(
      <ComparativeAreaChart data={DATA} series={SERIES} selectedName="99" />,
    );
    expect(container.querySelector(".delpi-ui-comparative-area-chart__selection-band")).toBeNull();
    rerender(<ComparativeAreaChart data={DATA} series={SERIES} selectedName={null} />);
    expect(container.querySelector(".delpi-ui-comparative-area-chart__selection-band")).toBeNull();
  });

  it("negative: empty data stays empty even with onPointSelect", () => {
    const { container } = render(
      <ComparativeAreaChart data={[]} series={SERIES} onPointSelect={() => undefined} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("keyboard focus shows the focus band on a non-selected point", () => {
    const { container } = render(
      <ComparativeAreaChart
        data={DATA}
        series={SERIES}
        onPointSelect={() => undefined}
        selectedName="01"
      />,
    );
    act(() => {
      screen.getAllByRole("button")[2]!.focus();
    });
    expect(container.querySelector(".delpi-ui-comparative-area-chart__focus-band")).toBeTruthy();
  });
});
