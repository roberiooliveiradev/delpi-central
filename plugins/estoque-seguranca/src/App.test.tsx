import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("./pages/SafetyStockPage", () => ({
  SafetyStockPage: () => <div>Página monitoramento</div>,
}));

vi.mock("./pages/ConsumptionAnalysisPage", () => ({
  ConsumptionAnalysisPage: () => <div>Página análise de consumo</div>,
}));

describe("App routing", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/apps/estoque-seguranca");
  });

  it("renderiza monitoramento na rota base", () => {
    render(<App pathname="/apps/estoque-seguranca" />);
    expect(screen.getByText("Página monitoramento")).toBeTruthy();
  });

  it("renderiza análise de consumo na rota dedicada", () => {
    render(<App pathname="/apps/estoque-seguranca/analise-consumo" />);
    expect(screen.getByText("Página análise de consumo")).toBeTruthy();
  });
});
