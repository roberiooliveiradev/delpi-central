import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HorizontalValueBars } from "./HorizontalValueBars";

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
