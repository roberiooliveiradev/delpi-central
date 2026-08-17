import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("../utils/routing", async () => {
  const actual = await vi.importActual<typeof import("../utils/routing")>("../utils/routing");
  return {
    ...actual,
    readQueryParam: vi.fn((key: string) => {
      if (key === "tab") return "";
      return "";
    }),
    readCostCenterTab: vi.fn(() => "investimentos"),
  };
});

import { CostCenterCockpit } from "./CostCenterCockpit";
import { readCostCenterTab } from "../utils/routing";

describe("CostCenterCockpit", () => {
  afterEach(() => cleanup());

  it("na aba Investimentos oculta hero separado e mostra abas", () => {
    render(
      <CostCenterCockpit
        title="DEPARTAMENTO DE RH"
        locationLabel="Rio Bananal/ES"
        cycleYear="2027"
        costCenterId="0203"
        unitId="02"
        showInvestimentos
        showEquipe
        investimentos={<div data-testid="inv">lista</div>}
        equipe={<div data-testid="eq">equipe</div>}
      />,
    );
    expect(screen.getByTestId("cost-center-cockpit")).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "DEPARTAMENTO DE RH" })).toBeNull();
    expect(screen.getByRole("link", { name: /Investimentos/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Equipe/i })).toBeTruthy();
    expect(screen.getByTestId("inv")).toBeTruthy();
    expect(screen.queryByTestId("eq")).toBeNull();
  });

  it("na aba Equipe mostra hero do centro", () => {
    vi.mocked(readCostCenterTab).mockReturnValue("equipe");
    render(
      <CostCenterCockpit
        title="DEPARTAMENTO DE RH"
        locationLabel="Rio Bananal/ES"
        cycleYear="2027"
        costCenterId="0203"
        unitId="02"
        showInvestimentos
        showEquipe
        investimentos={<div data-testid="inv">lista</div>}
        equipe={<div data-testid="eq">equipe</div>}
      />,
    );
    expect(screen.getByRole("heading", { name: "DEPARTAMENTO DE RH" })).toBeTruthy();
    expect(screen.getByText(/Elaboração · 2027/i)).toBeTruthy();
    expect(screen.getByText("Rio Bananal/ES")).toBeTruthy();
    expect(screen.getByTestId("eq")).toBeTruthy();
  });
});
