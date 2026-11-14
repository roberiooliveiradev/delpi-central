import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  SemicircleProgressGauge,
  semicircleProgressGaugeBemClasses,
} from "./SemicircleProgressGauge";

afterEach(() => {
  cleanup();
});

describe("SemicircleProgressGauge", () => {
  it("emite dual-class e valor central", () => {
    const classNames = semicircleProgressGaugeBemClasses("itp");
    expect(classNames.root).toContain("delpi-ui-semicircle-gauge");
    render(<SemicircleProgressGauge prefix="itp" value={100} centerLabel="tudo certo" />);
    expect(screen.getByText("100")).toBeTruthy();
    expect(screen.getByText("tudo certo")).toBeTruthy();
    expect(document.querySelector(".itp-semicircle-gauge__fill")).toBeTruthy();
  });

  it("legenda de contagens entra no nome acessível", () => {
    render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        centerLabel="resumo"
        legend={[
          { id: "a", label: "Alta ou crítica", count: 1, tone: "danger" },
          { id: "b", label: "Baixa ou média", count: 3, tone: "success" },
        ]}
      />,
    );
    const gauge = screen.getByRole("img");
    expect(gauge.getAttribute("aria-label")).toContain("Alta ou crítica: 1");
    expect(screen.getByText("Alta ou crítica")).toBeTruthy();
    expect(screen.getByText("3")).toBeTruthy();
  });

  it("valor zero não desenha preenchimento e acima do máximo é limitado", () => {
    const { rerender } = render(<SemicircleProgressGauge prefix="itp" value={0} />);
    expect(document.querySelector(".delpi-ui-semicircle-gauge__fill")).toBeNull();
    rerender(<SemicircleProgressGauge prefix="itp" value={250} />);
    const gauge = screen.getByRole("img");
    expect(gauge.getAttribute("data-ratio")).toBe("1.0000");
  });

  it("valor nulo mostra traço sem percentual inventado", () => {
    render(<SemicircleProgressGauge prefix="itp" value={null} centerLabel="sem dados" />);
    expect(screen.getByText("—")).toBeTruthy();
  });
});

/**
 * Characterization of the CURRENT behavior (before additive evolution).
 * The legend must stay read-only when the new optional props are absent.
 */
describe("SemicircleProgressGauge — characterization (no new props)", () => {
  const legend = [
    { id: "a", label: "Alta", count: 1, tone: "danger" as const },
    { id: "b", label: "Baixa", count: 3 },
  ];

  it("legend renders as a read-only list: no buttons, no aria-pressed", () => {
    const { container } = render(
      <SemicircleProgressGauge prefix="itp" value={75} legend={legend} />,
    );
    expect(container.querySelectorAll("button")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-pressed]")).toHaveLength(0);
    const items = container.querySelectorAll("li.delpi-ui-semicircle-gauge__legend-item");
    expect(items).toHaveLength(2);
    expect(items[0]?.getAttribute("data-tone")).toBe("danger");
    expect(items[1]?.getAttribute("data-tone")).toBe("neutral");
    expect(items[0]?.querySelector(".delpi-ui-semicircle-gauge__legend-count")?.textContent).toBe(
      "1",
    );
  });

  it("root keeps role=img, tone modifier, data attributes and default aria-label", () => {
    render(<SemicircleProgressGauge prefix="itp" value={50} tone="warning" legend={legend} />);
    const gauge = screen.getByRole("img");
    expect(gauge.className).toContain("itp-semicircle-gauge--warning");
    expect(gauge.className).toContain("delpi-ui-semicircle-gauge--warning");
    expect(gauge.getAttribute("data-tone")).toBe("warning");
    expect(gauge.getAttribute("data-ratio")).toBe("0.5000");
    expect(gauge.getAttribute("aria-label")).toBe("50% · Alta: 1 · Baixa: 3");
  });

  it("explicit aria-label wins and no legend renders no list", () => {
    const { container } = render(
      <SemicircleProgressGauge prefix="itp" value={50} aria-label="Conformidade" />,
    );
    expect(screen.getByRole("img").getAttribute("aria-label")).toBe("Conformidade");
    expect(container.querySelector("ul")).toBeNull();
  });

  it("legend items are not exposed as a list role override", () => {
    const { container } = render(
      <SemicircleProgressGauge prefix="itp" value={75} legend={legend} />,
    );
    // Legend stays a plain <ul>/<li> inside the role=img root.
    expect(container.querySelector("ul.delpi-ui-semicircle-gauge__legend")).toBeTruthy();
  });
});

describe("SemicircleProgressGauge — additive evolution (selectable legend)", () => {
  const legend = [
    { id: "a", label: "Alta", count: 1, tone: "danger" as const },
    { id: "b", label: "Baixa", count: 3, tone: "success" as const },
  ];

  it("onLegendSelect turns legend items into buttons that report the item", () => {
    const onLegendSelect = vi.fn();
    render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        legend={legend}
        onLegendSelect={onLegendSelect}
      />,
    );
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(2);
    expect(buttons[0]?.className).toContain("delpi-ui-semicircle-gauge__legend-button");
    expect(buttons[0]?.className).toContain("itp-semicircle-gauge__legend-button");
    fireEvent.click(buttons[1]!);
    expect(onLegendSelect).toHaveBeenCalledWith(legend[1]);
  });

  it("selectedLegendId sets aria-pressed + selected modifier only on that item", () => {
    render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        legend={legend}
        onLegendSelect={() => undefined}
        selectedLegendId="a"
      />,
    );
    const [first, second] = screen.getAllByRole("button");
    expect(first?.getAttribute("aria-pressed")).toBe("true");
    expect(first?.className).toContain("delpi-ui-semicircle-gauge__legend-button--selected");
    expect(second?.getAttribute("aria-pressed")).toBe("false");
    expect(second?.className).not.toContain("--selected");
  });

  it("selectedLegendId null leaves every button unpressed", () => {
    render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        legend={legend}
        onLegendSelect={() => undefined}
        selectedLegendId={null}
      />,
    );
    for (const button of screen.getAllByRole("button")) {
      expect(button.getAttribute("aria-pressed")).toBe("false");
    }
  });

  it("legendItemAriaLabel names each button", () => {
    render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        legend={legend}
        onLegendSelect={() => undefined}
        legendItemAriaLabel={(item) => `Filtrar por ${item.label}`}
      />,
    );
    expect(screen.getByRole("button", { name: "Filtrar por Alta" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Filtrar por Baixa" })).toBeTruthy();
  });

  it("buttons stay reachable: the image role moves to the chart, not the root", () => {
    const { container } = render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        centerLabel="resumo"
        legend={legend}
        onLegendSelect={() => undefined}
      />,
    );
    const img = screen.getByRole("img");
    expect(img.className).toContain("delpi-ui-semicircle-gauge__chart");
    expect(img.getAttribute("aria-label")).toBe("resumo · 75%");
    expect(container.firstElementChild?.getAttribute("role")).toBe("group");
    expect(container.firstElementChild?.getAttribute("data-ratio")).toBe("0.7500");
  });

  it("negative: onLegendSelect without legend items renders as the read-only gauge", () => {
    const { container } = render(
      <SemicircleProgressGauge prefix="itp" value={75} onLegendSelect={() => undefined} />,
    );
    expect(container.querySelectorAll("button")).toHaveLength(0);
    expect(container.firstElementChild?.getAttribute("role")).toBe("img");
  });

  it("negative: selectedLegendId / legendItemAriaLabel alone do not make the legend interactive", () => {
    const { container } = render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        legend={legend}
        selectedLegendId="a"
        legendItemAriaLabel={(item) => item.label}
      />,
    );
    expect(container.querySelectorAll("button")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-pressed]")).toHaveLength(0);
  });
});
