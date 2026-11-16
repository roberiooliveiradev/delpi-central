/**
 * U15 P1 — CfBarSeriesChart propaga theme do Portal e background transparente.
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../test/pluginUiMock"));

import { CfBarSeriesChart } from "./controllershipFinanceUi";

afterEach(() => {
  cleanup();
  document.documentElement.removeAttribute("data-theme");
});

describe("CfBarSeriesChart theme (U15 P1)", () => {
  it("tema escuro → options.theme=dark e backgroundColor transparente", () => {
    document.documentElement.setAttribute("data-theme", "dark");
    const { container } = render(
      <CfBarSeriesChart
        points={[{ label: "10/11", value: 3 }]}
        emptyMessage="vazio"
        options={{ showLegend: false }}
      />,
    );
    const root = container.querySelector("[data-testid='bar-series-chart']");
    expect(root).toBeTruthy();
    expect(root?.getAttribute("data-theme")).toBe("dark");
    expect(root?.getAttribute("data-bg")).toBe("transparent");
  });

  it("tema claro → options.theme=light", () => {
    document.documentElement.setAttribute("data-theme", "light");
    const { container } = render(
      <CfBarSeriesChart
        points={[{ label: "10/11", value: 1 }]}
        emptyMessage="vazio"
        options={{ showLegend: false }}
      />,
    );
    const root = container.querySelector("[data-testid='bar-series-chart']");
    expect(root?.getAttribute("data-theme")).toBe("light");
    expect(root?.getAttribute("data-bg")).toBe("transparent");
  });
});
