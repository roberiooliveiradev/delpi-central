import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DISTRIBUTION_DONUT_CHART_TONES,
  DistributionDonut,
  createDashboardDistributionDonut,
  distributionDonutBemClasses,
  type DistributionDonutItem,
} from "./DistributionDonut";

afterEach(() => {
  cleanup();
});

const ITEMS: DistributionDonutItem[] = [
  { id: "a", label: "Alpha", value: 50 },
  { id: "b", label: "Beta", value: 30, tone: "danger", description: "Descrição de beta" },
  { id: "c", label: "Gamma", value: 20 },
  { id: "z", label: "Zero", value: 0 },
];

/** Sweep (rad) of an SVG slice path produced by buildPieSlicePath. */
function sliceSweeps(container: HTMLElement): number[] {
  const paths = Array.from(container.querySelectorAll<SVGPathElement>("path[data-slice-id]"));
  return paths.map((path) => {
    const d = path.getAttribute("d") ?? "";
    // Outer arc: "M ox oy A R R 0 large 1 x y ..." — recover angles from endpoints.
    const nums = d.match(/-?\d+(\.\d+)?(e-?\d+)?/g)!.map(Number);
    const [ox, oy] = nums;
    const arcIndex = d.indexOf("A ");
    const arcNums = d
      .slice(arcIndex)
      .match(/-?\d+(\.\d+)?(e-?\d+)?/g)!
      .map(Number);
    const ex = arcNums[5]!;
    const ey = arcNums[6]!;
    const a0 = Math.atan2(oy! - 50, ox! - 50);
    const a1 = Math.atan2(ey - 50, ex - 50);
    let sweep = a1 - a0;
    if (sweep <= 0) sweep += Math.PI * 2;
    return sweep;
  });
}

describe("DistributionDonut — render", () => {
  it("emits dual-class names and role=img with a summary aria-label (read-only)", () => {
    const cn = distributionDonutBemClasses("itp");
    expect(cn.root).toBe("itp-distribution-donut delpi-ui-distribution-donut");
    const { container } = render(
      <DistributionDonut prefix="itp" items={ITEMS} ariaLabel="Temas" />,
    );
    const svg = container.querySelector("svg")!;
    expect(svg.getAttribute("role")).toBe("img");
    expect(svg.getAttribute("aria-label")).toBe("Temas: Alpha 50%, Beta 30%, Gamma 20%");
    expect(container.querySelector(".itp-distribution-donut.delpi-ui-distribution-donut")).toBeTruthy();
  });

  it("arcs sum to 360° and are proportional to values", () => {
    const { container } = render(<DistributionDonut items={ITEMS} ariaLabel="Temas" />);
    const sweeps = sliceSweeps(container);
    expect(sweeps).toHaveLength(3);
    const total = sweeps.reduce((a, b) => a + b, 0);
    expect((total * 180) / Math.PI).toBeCloseTo(360, 3);
    expect((sweeps[0]! * 180) / Math.PI).toBeCloseTo(180, 3);
    expect((sweeps[1]! * 180) / Math.PI).toBeCloseTo(108, 3);
    expect((sweeps[2]! * 180) / Math.PI).toBeCloseTo(72, 3);
  });

  it("a single item still draws a full ring", () => {
    const { container } = render(
      <DistributionDonut items={[{ id: "a", label: "Só", value: 5 }]} ariaLabel="Um" />,
    );
    const d = container.querySelector("path[data-slice-id]")!.getAttribute("d")!;
    expect(d.match(/A /g)).toHaveLength(4); // two outer + two inner semicircles
  });

  it("zero-valued item is not a slice but is listed with 0", () => {
    const { container } = render(<DistributionDonut items={ITEMS} ariaLabel="Temas" />);
    expect(container.querySelector('path[data-slice-id="z"]')).toBeNull();
    const zero = screen.getByText("Zero").closest("li")!;
    expect(zero.textContent).toContain("0");
    expect(zero.textContent).toContain("0%");
  });

  it("showPercent=false hides percentages", () => {
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" showPercent={false} />,
    );
    expect(container.querySelector(".delpi-ui-distribution-donut__legend-percent")).toBeNull();
  });

  it("default tones follow chart-n order; explicit tone wins", () => {
    const { container } = render(<DistributionDonut items={ITEMS} ariaLabel="Temas" />);
    const slices = container.querySelectorAll("path[data-slice-id]");
    expect(slices[0]?.getAttribute("class")).toContain("delpi-ui-distribution-donut__slice--tone-chart-1");
    expect(slices[1]?.getAttribute("class")).toContain("delpi-ui-distribution-donut__slice--tone-danger");
    expect(slices[2]?.getAttribute("class")).toContain("delpi-ui-distribution-donut__slice--tone-chart-3");
    expect(DISTRIBUTION_DONUT_CHART_TONES).toHaveLength(8);
  });

  it("center shows the formatted total with the default PT-BR caption; labels are overridable", () => {
    const { container, rerender } = render(<DistributionDonut items={ITEMS} ariaLabel="Temas" />);
    expect(container.querySelector(".delpi-ui-distribution-donut__center-value")?.textContent).toBe("100");
    expect(container.querySelector(".delpi-ui-distribution-donut__center-label")?.textContent).toBe("Total");
    rerender(
      <DistributionDonut
        items={ITEMS}
        ariaLabel="Temas"
        labels={{ total: "Notas" }}
        centerValue="100 notas"
        centerLabel="no período"
      />,
    );
    expect(container.querySelector(".delpi-ui-distribution-donut__center-value")?.textContent).toBe(
      "100 notas",
    );
    expect(container.querySelector(".delpi-ui-distribution-donut__center-label")?.textContent).toBe(
      "no período",
    );
  });

  it("valueFormatter is used by center and list", () => {
    render(
      <DistributionDonut
        items={[{ id: "a", label: "Alpha", value: 1500 }]}
        ariaLabel="Valores"
        valueFormatter={(v) => `R$ ${v}`}
      />,
    );
    expect(screen.getAllByText("R$ 1500")).toHaveLength(2);
  });

  it("empty items and zero total render the empty message", () => {
    const { container, rerender } = render(
      <DistributionDonut items={[]} ariaLabel="Vazio" emptyMessage="Nada aqui" />,
    );
    expect(container.querySelector(".delpi-ui-distribution-donut__empty")?.textContent).toBe("Nada aqui");
    expect(container.querySelector("svg")).toBeNull();
    rerender(
      <DistributionDonut items={[{ id: "a", label: "A", value: 0 }]} ariaLabel="Vazio" />,
    );
    expect(container.querySelector(".delpi-ui-distribution-donut__empty")?.textContent).toBe("Sem dados.");
  });

  it("size and thickness drive geometry; thickness is clamped to 0.1–0.5", () => {
    const { container, rerender } = render(
      <DistributionDonut
        items={[{ id: "a", label: "Só", value: 1 }]}
        ariaLabel="Um"
        size={120}
        thickness={0.9}
      />,
    );
    const chart = container.querySelector<HTMLElement>(".delpi-ui-distribution-donut__chart")!;
    expect(chart.style.width).toBe("120px");
    const innerRadius = (d: string) => {
      // inner arc is the last "A r r"
      const arcs = d.match(/A (\d+(\.\d+)?) /g)!;
      return Number(arcs[arcs.length - 1]!.replace("A ", ""));
    };
    const dMax = container.querySelector("path[data-slice-id]")!.getAttribute("d")!;
    expect(innerRadius(dMax)).toBeCloseTo(48 * 0.5, 5);
    rerender(
      <DistributionDonut items={[{ id: "a", label: "Só", value: 1 }]} ariaLabel="Um" thickness={0.01} />,
    );
    const dMin = container.querySelector("path[data-slice-id]")!.getAttribute("d")!;
    expect(innerRadius(dMin)).toBeCloseTo(48 * 0.9, 5);
  });

  it("legendPlacement drives a modifier and 'none' removes the list", () => {
    const { container, rerender } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" legendPlacement="below" />,
    );
    expect(container.firstElementChild?.className).toContain("delpi-ui-distribution-donut--legend-below");
    expect(container.querySelector("ul")).toBeTruthy();
    rerender(<DistributionDonut items={ITEMS} ariaLabel="Temas" legendPlacement="none" />);
    expect(container.querySelector("ul")).toBeNull();
    rerender(<DistributionDonut items={ITEMS} ariaLabel="Temas" />);
    expect(container.firstElementChild?.className).toContain("delpi-ui-distribution-donut--legend-side");
  });

  it("factory binds the prefix", () => {
    const Donut = createDashboardDistributionDonut({ prefix: "fx" });
    const { container } = render(<Donut items={ITEMS} ariaLabel="Temas" />);
    expect(container.querySelector(".fx-distribution-donut.delpi-ui-distribution-donut")).toBeTruthy();
  });

  it("dark theme: colors come from tokens only (no inline fill/background)", () => {
    document.documentElement.setAttribute("data-theme", "dark");
    const { container } = render(<DistributionDonut items={ITEMS} ariaLabel="Temas" />);
    for (const path of Array.from(container.querySelectorAll("path[data-slice-id]"))) {
      expect(path.getAttribute("fill")).toBeNull();
      expect(path.getAttribute("style")).toBeNull();
    }
    document.documentElement.removeAttribute("data-theme");
  });
});

describe("DistributionDonut — maxItems grouping", () => {
  const MANY: DistributionDonutItem[] = [
    { id: "1", label: "Um", value: 40 },
    { id: "2", label: "Dois", value: 30 },
    { id: "3", label: "Três", value: 20 },
    { id: "4", label: "Quatro", value: 6 },
    { id: "5", label: "Cinco", value: 4 },
  ];

  it("groups the remainder into a non-selectable 'Outros' entry", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <DistributionDonut items={MANY} ariaLabel="Muitos" maxItems={3} onSelect={onSelect} />,
    );
    expect(screen.queryByText("Quatro")).toBeNull();
    const others = screen.getByText("Outros").closest("li")!;
    expect(others.textContent).toContain("10");
    expect(others.querySelector("button")).toBeNull();
    const othersSlice = container.querySelector('path[data-slice-id="__others__"]')!;
    expect(othersSlice.getAttribute("role")).toBeNull();
    fireEvent.click(othersSlice);
    expect(onSelect).not.toHaveBeenCalled();
    expect(container.querySelectorAll("path[data-slice-id]")).toHaveLength(4);
  });

  it("negative: no grouping when item count does not exceed maxItems", () => {
    render(<DistributionDonut items={MANY} ariaLabel="Muitos" maxItems={5} />);
    expect(screen.queryByText("Outros")).toBeNull();
    expect(screen.getByText("Cinco")).toBeTruthy();
  });

  it("'Outros' label is overridable", () => {
    render(
      <DistributionDonut items={MANY} ariaLabel="Muitos" maxItems={2} labels={{ others: "Demais" }} />,
    );
    expect(screen.getByText("Demais")).toBeTruthy();
  });
});

describe("DistributionDonut — selection", () => {
  it("read-only without onSelect: no buttons, no aria-pressed, no focusable slices", () => {
    const { container } = render(<DistributionDonut items={ITEMS} ariaLabel="Temas" />);
    expect(container.querySelectorAll("button")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-pressed]")).toHaveLength(0);
    expect(container.querySelectorAll("[tabindex]")).toHaveLength(0);
  });

  it("with onSelect slices and list items are toggle buttons", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={onSelect} />,
    );
    expect(container.querySelector("svg")?.getAttribute("role")).toBe("group");
    const slices = container.querySelectorAll('path[role="button"]');
    expect(slices).toHaveLength(3);
    expect(slices[0]?.getAttribute("aria-pressed")).toBe("false");
    expect(screen.getAllByRole("button", { hidden: false }).filter((b) => b.tagName === "BUTTON")).toHaveLength(4);

    fireEvent.click(slices[1]!);
    expect(onSelect).toHaveBeenLastCalledWith(ITEMS[1]);
    fireEvent.click(screen.getByText("Gamma").closest("button")!);
    expect(onSelect).toHaveBeenLastCalledWith(ITEMS[2]);
  });

  it("selected item: aria-pressed, selected/dimmed modifiers and center follows the selection", () => {
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={() => undefined} selectedId="b" />,
    );
    const slices = container.querySelectorAll('path[role="button"]');
    expect(slices[1]?.getAttribute("aria-pressed")).toBe("true");
    expect(slices[1]?.getAttribute("class")).toContain("delpi-ui-distribution-donut__slice--selected");
    expect(slices[0]?.getAttribute("class")).toContain("delpi-ui-distribution-donut__slice--dimmed");
    const listPressed = Array.from(container.querySelectorAll("li > button")).map((b) =>
      b.getAttribute("aria-pressed"),
    );
    expect(listPressed).toEqual(["false", "true", "false", "false"]);
    expect(container.querySelector(".delpi-ui-distribution-donut__center-value")?.textContent).toBe("30");
    expect(container.querySelector(".delpi-ui-distribution-donut__center-label")?.textContent).toBe("Beta");
  });

  it("clicking the selected slice or item sends null (deselect)", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={onSelect} selectedId="a" />,
    );
    fireEvent.click(container.querySelector('path[data-slice-id="a"]')!);
    expect(onSelect).toHaveBeenLastCalledWith(null);
    fireEvent.click(container.querySelector("li > button")!);
    expect(onSelect).toHaveBeenLastCalledWith(null);
  });

  it("clear-selection button appears only with a selection and uses the overridable label", () => {
    const onSelect = vi.fn();
    const { rerender } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={onSelect} />,
    );
    expect(screen.queryByText("Limpar seleção")).toBeNull();
    rerender(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={onSelect} selectedId="a" />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Limpar seleção" }));
    expect(onSelect).toHaveBeenLastCalledWith(null);
    rerender(
      <DistributionDonut
        items={ITEMS}
        ariaLabel="Temas"
        onSelect={onSelect}
        selectedId="a"
        labels={{ clearSelection: "Tirar filtro" }}
      />,
    );
    expect(screen.getByRole("button", { name: "Tirar filtro" })).toBeTruthy();
  });

  it("keyboard: Enter and Space on a slice select; other keys do nothing", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={onSelect} />,
    );
    const slice = container.querySelector('path[data-slice-id="c"]')!;
    expect(slice.getAttribute("tabindex")).toBe("0");
    fireEvent.keyDown(slice, { key: "Enter" });
    fireEvent.keyDown(slice, { key: " " });
    fireEvent.keyDown(slice, { key: "a" });
    expect(onSelect).toHaveBeenCalledTimes(2);
    expect(onSelect).toHaveBeenCalledWith(ITEMS[2]);
  });

  it("description reaches the slice tooltip and the accessible names", () => {
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={() => undefined} />,
    );
    const slice = container.querySelector('path[data-slice-id="b"]')!;
    expect(slice.querySelector("title")?.textContent).toContain("Descrição de beta");
    expect(slice.getAttribute("aria-label")).toBe("Beta: 30, 30%. Descrição de beta");
    // Slice and list button share the same description-aware name.
    expect(screen.getAllByRole("button", { name: "Beta: 30, 30%. Descrição de beta" })).toHaveLength(2);
  });

  it("negative: unknown selectedId selects nothing and dims nothing", () => {
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" onSelect={() => undefined} selectedId="nope" />,
    );
    expect(container.querySelectorAll("[class*='--dimmed']")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-pressed='true']")).toHaveLength(0);
  });

  it("negative: selectedId alone (no onSelect) does not make anything interactive", () => {
    const { container } = render(
      <DistributionDonut items={ITEMS} ariaLabel="Temas" selectedId="a" />,
    );
    expect(container.querySelectorAll("button")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-pressed]")).toHaveLength(0);
    expect(container.querySelector(".delpi-ui-distribution-donut__slice--selected")).toBeTruthy();
  });
});

describe("DistributionDonut — styles contract", () => {
  it("styles.css imports the donut stylesheet", async () => {
    const { readFileSync } = await import("node:fs");
    const { resolve } = await import("node:path");
    const entry = readFileSync(resolve(__dirname, "../../styles.css"), "utf8");
    expect(entry).toContain('@import "./styles/distribution-donut.css"');
    const css = readFileSync(resolve(__dirname, "../../styles/distribution-donut.css"), "utf8");
    expect(css).toContain("@container delpi-ui-distribution-donut (max-width: 480px)");
    expect(css).not.toMatch(/#[0-9a-f]{3,8}\s*;(?![^{]*var\()/i);
  });
});
