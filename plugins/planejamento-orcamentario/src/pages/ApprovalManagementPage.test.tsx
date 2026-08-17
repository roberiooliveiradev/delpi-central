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
  createHostContainedModalShell:
    () =>
    function HostContainedModal({
      open,
      title,
      children,
    }: {
      open: boolean;
      title: ReactNode;
      children?: ReactNode;
    }) {
      if (!open) return null;
      return (
        <div role="dialog" aria-label={String(title)}>
          {children}
        </div>
      );
    },
  createSimpleKpiCard:
    () =>
    function KpiCard({
      title,
      value,
      subtitle,
    }: {
      title: string;
      value: string;
      subtitle?: string;
    }) {
      return (
        <div data-testid={`kpi-${title}`}>
          {title}: {value}
          {subtitle ? ` (${subtitle})` : ""}
        </div>
      );
    },
}));

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: () => ({
    profile: {
      permissions: [
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.capex.approve",
        "planejamento-orcamentario.personnel.approve",
        "planejamento-orcamentario.capex.consolidation.view",
      ],
    },
    loading: false,
    error: null,
  }),
}));

vi.mock("../utils/routing", async () => {
  const actual = await vi.importActual<typeof import("../utils/routing")>("../utils/routing");
  return {
    ...actual,
    readQueryParam: vi.fn(() => ""),
  };
});

vi.mock("../components/CapexConsolidationBarChart", () => ({
  CapexConsolidationBarChart: () => <div data-testid="chart">chart</div>,
}));

import { ApprovalManagementPage } from "./ApprovalManagementPage";
import * as budgetApi from "../api/budgetPlanningApi";
import * as portfolio from "../utils/approvalPortfolio";

vi.mock("../api/budgetPlanningApi");
vi.mock("../utils/approvalPortfolio", async () => {
  const actual = await vi.importActual<typeof import("../utils/approvalPortfolio")>(
    "../utils/approvalPortfolio",
  );
  return {
    ...actual,
    fetchApprovalPortfolio: vi.fn(),
    fetchApprovalPlansForCostCenter: vi.fn(),
  };
});

describe("ApprovalManagementPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  beforeEach(() => {
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

    vi.mocked(portfolio.fetchApprovalPortfolio).mockResolvedValue([
      {
        key: "02::0205",
        unit_id: "02",
        cost_center_id: "0205",
        area_id: "PROD",
        branch: "02",
        cost_center_name: "Produção",
        icon_key: null,
        owner_name: null,
        capexPlan: {
          id: "plan-c",
          exercise_id: "ex-1",
          unit_id: "02",
          cost_center_id: "0205",
          status: "submitted",
          version: 1,
          total_amount: "15000",
          investment_count: 2,
        },
        personnelPlan: {
          id: "plan-p",
          exercise_id: "ex-1",
          unit_id: "02",
          cost_center_id: "0205",
          status: "draft",
          version: 1,
          position_count: 1,
          lines: [],
          totals: { headcount_dec_2027: 3 },
        },
        capexPending: true,
        personnelPending: false,
        capexInProgress: false,
        personnelInProgress: true,
        capexAmount: 15000,
        personnelHeadcount: 3,
        urgency: 100,
      },
    ] as never);

    vi.mocked(budgetApi.fetchCapexConsolidationSummary).mockResolvedValue({
      exercise: { id: "ex-1", year: 2027 },
      filters: {},
      summary: {
        currency: "BRL",
        total_estimated_amount: "100000",
        investment_count: 10,
        cost_center_count: 4,
        plans_draft_count: 1,
        plans_submitted_count: 2,
        plans_changes_requested_count: 0,
        plans_rejected_count: 0,
        plans_approved_count: 1,
        approved_amount: "40000",
        in_review_amount: "15000",
        incomplete_investment_count: 0,
      },
    });

    vi.mocked(budgetApi.fetchCapexConsolidationByCostCenter).mockResolvedValue({
      exercise: { id: "ex-1" },
      filters: {},
      items: [
        {
          code: "0205",
          description: "Produção",
          investment_count: 2,
          total_amount: "15000",
          unit_id: "02",
          cost_center_id: "0205",
        },
      ],
    } as never);

    vi.mocked(budgetApi.fetchCapexConsolidationByPlanStatus).mockResolvedValue({
      exercise: { id: "ex-1" },
      filters: {},
      items: [
        {
          code: "draft",
          description: "Rascunho",
          investment_count: 3,
          total_amount: "45000",
        },
        {
          code: "submitted",
          description: "Enviado",
          investment_count: 2,
          total_amount: "15000",
        },
        {
          code: "approved",
          description: "Aprovado",
          investment_count: 1,
          total_amount: "40000",
        },
      ],
    } as never);
  });

  it("exibe overview com centros e KPIs distintos", async () => {
    render(<ApprovalManagementPage />);
    await waitFor(() => {
      expect(screen.getByText("Centros de custo")).toBeTruthy();
    });
    expect(screen.getByText("Decidir")).toBeTruthy();
    expect(screen.getByText("Produção")).toBeTruthy();
    expect(screen.getByText(/Filial 02 · Rio Bananal/)).toBeTruthy();
    expect(screen.getByText("Aguardando aprovação")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Produção.*decidir/i })).toBeTruthy();
    expect(screen.getByTestId("kpi-Aguardando aprovação").textContent).toContain("15.000");
    expect(screen.getByTestId("kpi-Em elaboração").textContent).toContain("45.000");
    expect(screen.getByTestId("kpi-Já aprovado").textContent).toContain("40.000");
    expect(screen.getByTestId("kpi-Total do ciclo").textContent).toContain("100.000");
    expect(screen.getByText("Maiores valores aguardando aprovação")).toBeTruthy();
  });
});
