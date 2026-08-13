import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SpeedometerGauge } from "./SpeedometerGauge";

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

  it("mostra traço quando valor é nulo", () => {
    render(<SpeedometerGauge value={null} label="Sem dados" unit="%" />);
    expect(screen.getByText("—")).toBeTruthy();
  });
});
