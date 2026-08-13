import { fireEvent, render, screen } from "@testing-library/react";
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

  it("aplica tom danger abaixo de 90%", () => {
    const { container } = render(<SpeedometerGauge value={85} label="Baixo" />);
    expect(container.querySelector('[data-tone="danger"]')).toBeTruthy();
  });

  it("mostra tooltip interativo no hover", () => {
    render(
      <SpeedometerGauge
        value={98.5}
        label="OTD Santa Catarina"
        tip="OTD SC no período"
      />,
    );
    const gauge = screen.getByRole("img", { name: /OTD Santa Catarina/i });
    fireEvent.mouseEnter(gauge);
    expect(screen.getByRole("tooltip").textContent).toContain("OTD SC no período");
  });

  it("mostra indicador e valor da meta", () => {
    const { container } = render(
      <SpeedometerGauge value={98.5} goal={95} label="OTD SC" />,
    );
    expect(screen.getByText(/Meta:\s*95/)).toBeTruthy();
    expect(container.querySelector("[data-goal='95']")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-speedometer-gauge__goal-marker")).toBeTruthy();
  });

  it("mostra traço quando valor é nulo", () => {
    render(<SpeedometerGauge value={null} label="Sem dados" unit="%" />);
    expect(screen.getByText("—")).toBeTruthy();
  });
});
