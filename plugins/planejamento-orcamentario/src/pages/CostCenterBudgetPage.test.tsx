import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  createDashboardSectionCard:
    () =>
    function SectionCard({ title, children }: { title: string; children: ReactNode }) {
      return (
        <section data-testid={`section-${title}`}>
          <h2>{title}</h2>
          {children}
        </section>
      );
    },
  createDashboardLoadingActivityCard:
    () =>
    function LoadingActivityCard({ title }: { title: string }) {
      return <div>{title}</div>;
    },
  createDashboardStateBox:
    () =>
    function StateBox({ children }: { children: ReactNode }) {
      return <div role="alert">{children}</div>;
    },
}));

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: () => ({
    profile: {
      permissions: [
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.capex.submit",
        "planejamento-orcamentario.personnel.view",
        "planejamento-orcamentario.personnel.edit",
      ],
    },
    loading: false,
    error: null,
  }),
}));

vi.mock("./CapexMyCostCentersPage", () => ({
  CapexMyCostCentersPage: ({ embedded }: { embedded?: boolean }) => (
    <div data-testid="capex-section">{embedded ? "capex-embedded" : "capex"}</div>
  ),
}));

vi.mock("./PersonnelBudgetPage", () => ({
  PersonnelBudgetPage: ({
    embedded,
    hideSectionChrome,
  }: {
    embedded?: boolean;
    hideSectionChrome?: boolean;
  }) => (
    <div data-testid="personnel-section">
      {embedded ? "personnel-embedded" : "personnel"}
      {hideSectionChrome ? "-chrome-off" : ""}
    </div>
  ),
}));

const queryParams: Record<string, string | null> = {
  cost_center_id: "0205",
  unit_id: "02",
};

vi.mock("../utils/routing", async () => {
  const actual = await vi.importActual<typeof import("../utils/routing")>("../utils/routing");
  return {
    ...actual,
    readQueryParam: vi.fn((key: string) => queryParams[key] ?? null),
  };
});

import { CostCenterBudgetPage } from "./CostCenterBudgetPage";
import * as budgetApi from "../api/budgetPlanningApi";
import * as portfolio from "../utils/costCenterPortfolio";

vi.mock("../api/budgetPlanningApi");
vi.mock("../utils/costCenterPortfolio", async () => {
  const actual = await vi.importActual<typeof import("../utils/costCenterPortfolio")>(
    "../utils/costCenterPortfolio",
  );
  return {
    ...actual,
    fetchMyCostCenterPortfolio: vi.fn(),
  };
});

describe("CostCenterBudgetPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    queryParams.cost_center_id = "0205";
    queryParams.unit_id = "02";

    vi.mocked(budgetApi.fetchBudgetContext).mockResolvedValue({
      exercise: {
        id: "ex-1",
        year: 2027,
        name: "PO 2027",
        status: "open",
        is_active: true,
      },
      guidance: { current_version: 1, acknowledged: true },
      scopes: [],
      capabilities: {
        access: true,
        guidance_view: true,
        guidance_manage: false,
        scopes_manage: false,
        admin: false,
      },
      modules_unlocked: true,
      reason: null,
    } as never);

    vi.mocked(portfolio.fetchMyCostCenterPortfolio).mockResolvedValue([
      {
        key: "02::0205",
        unit_id: "02",
        cost_center_id: "0205",
        cost_center_name: "Manutenção ES",
        icon_key: "wrench",
        area_id: "PROD",
        branch: "02",
        exercise_id: "ex-1",
        responsibility_type: "owner",
        canCapex: true,
        canPersonnel: true,
        capexResponsibility: null,
        personnelResponsibility: null,
      },
    ]);
  });

  it("lista centros em cards sem jargão CAPEX/Pessoal", async () => {
    queryParams.cost_center_id = null;
    queryParams.unit_id = null;
    render(<CostCenterBudgetPage />);
    await waitFor(() => {
      expect(screen.getByText("Seus centros")).toBeTruthy();
    });
    expect(screen.getByRole("link", { name: /Manutenção ES/i })).toBeTruthy();
    expect(screen.getByText("Rio Bananal/ES")).toBeTruthy();
    expect(screen.queryByText("0205")).toBeNull();
    expect(screen.queryByText(/02 \(/)).toBeNull();
    expect(screen.queryByText(/CAPEX/i)).toBeNull();
    expect(screen.queryByText(/headcount/i)).toBeNull();
    expect(screen.queryByText(/Módulos/i)).toBeNull();
  });

  it("com CC selecionado renderiza cockpit com abas", async () => {
    render(<CostCenterBudgetPage />);
    await waitFor(() => {
      expect(screen.getByTestId("cost-center-cockpit")).toBeTruthy();
    });
    expect(screen.getByRole("heading", { level: 2, name: /Manutenção ES/i })).toBeTruthy();
    expect(screen.getByRole("navigation", { name: /Áreas do orçamento/i })).toBeTruthy();
    expect(screen.getByTestId("capex-section").textContent).toBe("capex-embedded");
    // Aba padrão = investimentos; equipe só com ?tab=equipe
    expect(screen.queryByTestId("personnel-section")).toBeNull();
    expect(screen.queryByText(/CAPEX e Pessoal/i)).toBeNull();
  });
});
