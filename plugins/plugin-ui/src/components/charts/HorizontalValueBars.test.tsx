import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HorizontalValueBars } from "./HorizontalValueBars";

afterEach(() => {
  cleanup();
});

describe("HorizontalValueBars", () => {
  it("renderiza barras e dispara clique", () => {
    const onItemClick = vi.fn();
    render(
      <HorizontalValueBars
        aria-label="Ranking"
        onItemClick={onItemClick}
        items={[
          { id: "a", label: "AHT", value: 4, meta: "28 dias" },
          { id: "b", label: "WEG", value: 3, meta: "13 dias" },
        ]}
      />,
    );
    expect(screen.getByText("AHT")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /AHT/i }));
    expect(onItemClick).toHaveBeenCalledOnce();
    expect(onItemClick.mock.calls[0]?.[0]?.id).toBe("a");
  });

  it("mostra empty state", () => {
    render(<HorizontalValueBars items={[]} emptyMessage="Vazio" />);
    expect(screen.getByText("Vazio")).toBeTruthy();
  });

  it("expõe layout stacked e rank dos itens", () => {
    const { container } = render(
      <HorizontalValueBars
        layout="stacked"
        items={[
          { id: "a", label: "AHT", value: 4 },
          { id: "b", label: "WEG", value: 3 },
        ]}
      />,
    );
    const root = container.querySelector(".delpi-ui-horizontal-value-bars");
    expect(root?.getAttribute("data-layout")).toBe("stacked");
    expect(
      root?.className.includes("delpi-ui-horizontal-value-bars--stacked"),
    ).toBe(true);
    const rows = container.querySelectorAll("[data-rank]");
    expect(rows[0]?.getAttribute("data-rank")).toBe("1");
    expect(rows[1]?.getAttribute("data-rank")).toBe("2");
  });
});

/**
 * Characterization of the CURRENT behavior (before additive evolution).
 * Must remain identical when `tone`, `selectedId` and `itemAriaLabel` are absent.
 */
describe("HorizontalValueBars — characterization (no new props)", () => {
  const items = [
    { id: "a", label: "AHT", value: 4, meta: "28 dias" },
    { id: "b", label: "WEG", value: 2, valueLabel: "dois" },
  ];

  it("read-only mode renders list items without buttons", () => {
    const { container } = render(<HorizontalValueBars items={items} />);
    expect(container.querySelectorAll("button")).toHaveLength(0);
    expect(container.querySelectorAll("li.delpi-ui-horizontal-value-bars__row")).toHaveLength(2);
    expect(container.querySelectorAll("[aria-pressed]")).toHaveLength(0);
  });

  it("scales fill width against the max value and honors max override", () => {
    const { container, rerender } = render(<HorizontalValueBars items={items} />);
    const fills = () =>
      Array.from(container.querySelectorAll<HTMLElement>(".delpi-ui-horizontal-value-bars__fill")).map(
        (el) => el.style.width,
      );
    expect(fills()).toEqual(["100%", "50%"]);
    rerender(<HorizontalValueBars items={items} max={8} />);
    expect(fills()).toEqual(["50%", "25%"]);
  });

  it("shows valueLabel when provided, otherwise pt-BR formatted value", () => {
    render(<HorizontalValueBars items={items} />);
    expect(screen.getByText("dois")).toBeTruthy();
    expect(screen.getByText("4")).toBeTruthy();
    expect(screen.getByText("28 dias")).toBeTruthy();
  });

  it("clickable rows are plain buttons without aria-pressed or aria-label", () => {
    const { container } = render(<HorizontalValueBars items={items} onItemClick={() => undefined} />);
    const buttons = container.querySelectorAll("button");
    expect(buttons).toHaveLength(2);
    for (const button of Array.from(buttons)) {
      expect(button.hasAttribute("aria-pressed")).toBe(false);
      expect(button.hasAttribute("aria-label")).toBe(false);
      expect(button.getAttribute("type")).toBe("button");
    }
  });

  it("does not stamp tone or selection state on rows/fills", () => {
    const { container } = render(<HorizontalValueBars items={items} onItemClick={() => undefined} />);
    expect(container.querySelector("[data-tone]")).toBeNull();
    expect(container.querySelector("[data-selected]")).toBeNull();
    expect(container.querySelector("[data-dimmed]")).toBeNull();
  });

  it("default layout is columns and root forwards aria-label and prefix classes", () => {
    const { container } = render(
      <HorizontalValueBars prefix="itp" items={items} aria-label="Ranking" className="extra" />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.getAttribute("data-layout")).toBe("columns");
    expect(root.getAttribute("aria-label")).toBe("Ranking");
    expect(root.className).toContain("itp-horizontal-value-bars");
    expect(root.className).toContain("extra");
    expect(root.className).not.toContain("--stacked");
  });
});

describe("HorizontalValueBars — additive evolution (tone / selection / aria)", () => {
  const items = [
    { id: "a", label: "AHT", value: 4, tone: "danger" as const },
    { id: "b", label: "WEG", value: 2, tone: "default" as const },
    { id: "c", label: "ABC", value: 1 },
  ];

  it("tone adds a modifier on the fill; default/undefined keep the base fill class", () => {
    const { container } = render(<HorizontalValueBars items={items} />);
    const fills = Array.from(container.querySelectorAll(".delpi-ui-horizontal-value-bars__fill"));
    expect(fills[0]?.className).toContain("delpi-ui-horizontal-value-bars__fill--tone-danger");
    expect(fills[1]?.className).not.toContain("--tone-");
    expect(fills[2]?.className).not.toContain("--tone-");
  });

  it("tone also emits the prefix-scoped modifier (dual-class)", () => {
    const { container } = render(<HorizontalValueBars prefix="itp" items={items} />);
    expect(container.querySelector(".itp-horizontal-value-bars__fill--tone-danger")).toBeTruthy();
  });

  it("selectedId highlights the row, dims others and sets aria-pressed on buttons", () => {
    const { container } = render(
      <HorizontalValueBars items={items} onItemClick={() => undefined} selectedId="b" />,
    );
    const rows = container.querySelectorAll("li");
    expect(rows[1]?.className).toContain("delpi-ui-horizontal-value-bars__row--selected");
    expect(rows[0]?.className).toContain("delpi-ui-horizontal-value-bars__row--dimmed");
    expect(rows[2]?.className).toContain("delpi-ui-horizontal-value-bars__row--dimmed");
    const pressed = Array.from(container.querySelectorAll("button")).map((b) =>
      b.getAttribute("aria-pressed"),
    );
    expect(pressed).toEqual(["false", "true", "false"]);
  });

  it("selectedId=null exposes aria-pressed=false everywhere without dimming", () => {
    const { container } = render(
      <HorizontalValueBars items={items} onItemClick={() => undefined} selectedId={null} />,
    );
    const pressed = Array.from(container.querySelectorAll("button")).map((b) =>
      b.getAttribute("aria-pressed"),
    );
    expect(pressed).toEqual(["false", "false", "false"]);
    expect(container.querySelector("[data-dimmed]")).toBeNull();
  });

  it("selecting still invokes onItemClick with the item", () => {
    const onItemClick = vi.fn();
    render(<HorizontalValueBars items={items} onItemClick={onItemClick} selectedId="a" />);
    fireEvent.click(screen.getByRole("button", { name: /WEG/ }));
    expect(onItemClick.mock.calls[0]?.[0]?.id).toBe("b");
  });

  it("itemAriaLabel names buttons when clickable and list items when read-only", () => {
    const label = (item: { label: string }) => `Filtrar ${item.label}`;
    const { rerender } = render(
      <HorizontalValueBars items={items} onItemClick={() => undefined} itemAriaLabel={label} />,
    );
    expect(screen.getByRole("button", { name: "Filtrar AHT" })).toBeTruthy();
    rerender(<HorizontalValueBars items={items} itemAriaLabel={label} />);
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.getAllByRole("listitem")[0]?.getAttribute("aria-label")).toBe("Filtrar AHT");
  });

  it("negative: read-only rows never get aria-pressed even with selectedId", () => {
    const { container } = render(<HorizontalValueBars items={items} selectedId="a" />);
    expect(container.querySelectorAll("[aria-pressed]")).toHaveLength(0);
    expect(container.querySelector("li")?.className).toContain("--selected");
  });

  it("negative: unknown selectedId dims everything but selects nothing", () => {
    const { container } = render(
      <HorizontalValueBars items={items} onItemClick={() => undefined} selectedId="zzz" />,
    );
    expect(container.querySelectorAll("li[data-selected]")).toHaveLength(0);
    expect(container.querySelectorAll("li[data-dimmed]")).toHaveLength(3);
  });
});
