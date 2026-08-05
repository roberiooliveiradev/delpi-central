import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  createDashboardSectionCard:
    () =>
    function SectionCard({ title, children }: { title: string; children: ReactNode }) {
      return (
        <section>
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

const permissionsState = {
  profile: { permissions: ["planejamento-orcamentario.capex.approve"] } as {
    permissions: string[];
  } | null,
  loading: false,
  error: null as string | null,
};

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: () => permissionsState,
}));

import { CapexReviewDetailPage } from "./CapexReviewDetailPage";
import * as budgetApi from "../api/budgetPlanningApi";
import { HttpRequestError } from "../api/httpClient";

vi.mock("../api/budgetPlanningApi");

const plan = {
  id: "plan-1",
  exercise_id: "ex-1",
  unit_id: "01",
  area_id: "PROD",
  cost_center_id: "205",
  status: "submitted",
  version: 2,
  submitted_by: "owner-1",
  submitted_at: "2026-08-05T12:00:00Z",
  investments: [
    {
      id: "inv-1",
      exercise_id: "ex-1",
      unit_id: "01",
      cost_center_id: "205",
      description: "Notebooks",
      category_id: "cat-1",
      estimated_amount: "1500.00",
      currency: "BRL",
      priority: "2",
      origin: "national",
      required_date: "2027-06-01",
      probable_supplier_name: "Fornecedor X",
      status: "draft",
      version: 1,
      is_complete: true,
      missing_fields: [],
    },
  ],
};

beforeEach(() => {
  permissionsState.profile = {
    permissions: ["planejamento-orcamentario.capex.approve"],
  };
  permissionsState.loading = false;
  permissionsState.error = null;
  vi.mocked(budgetApi.getCapexReviewDetail).mockResolvedValue(plan as never);
  vi.mocked(budgetApi.listCapexPlanHistory).mockResolvedValue({
    items: [
      {
        id: "h1",
        plan_id: "plan-1",
        action: "submitted",
        previous_status: "draft",
        new_status: "submitted",
        actor_sub: "owner-1",
        actor_name: "Owner",
        created_at: "2026-08-05T12:00:00Z",
      },
    ],
  });
  vi.mocked(budgetApi.listActiveCapexCategories).mockResolvedValue({
    items: [
      {
        id: "cat-1",
        code: "FERR",
        name: "Ferramentas",
        display_order: 1,
        is_active: true,
        is_system_default: true,
      },
    ],
  });
  vi.mocked(budgetApi.listCapexInvestmentAttachments).mockResolvedValue([]);
  vi.stubGlobal(
    "confirm",
    vi.fn(() => true),
  );
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("CapexReviewDetailPage", () => {
  it("tela de análise somente leitura com investimentos", async () => {
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByText(/Notebooks/);
    expect(screen.getByText(/Fornecedor X/)).toBeTruthy();
    expect(screen.getByText(/Somente leitura/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Aprovar/i })).toBeTruthy();
  });

  it("aprovação válida", async () => {
    vi.mocked(budgetApi.approveCapexPlan).mockResolvedValue({
      ...plan,
      status: "approved",
      version: 3,
    } as never);
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByRole("button", { name: /Aprovar/i });
    fireEvent.click(screen.getByRole("button", { name: /Aprovar/i }));
    await waitFor(() => {
      expect(budgetApi.approveCapexPlan).toHaveBeenCalledWith("plan-1", {
        version: 2,
        comment: null,
      });
    });
    await screen.findByText(/Planejamento aprovado/i);
  });

  it("reprovação sem comentário", async () => {
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByRole("button", { name: /Reprovar/i });
    fireEvent.click(screen.getByRole("button", { name: /Reprovar/i }));
    await screen.findByText(/Justificativa obrigatória/i);
    expect(budgetApi.rejectCapexPlan).not.toHaveBeenCalled();
  });

  it("ajustes sem comentário", async () => {
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByRole("button", { name: /Solicitar ajustes/i });
    fireEvent.click(screen.getByRole("button", { name: /Solicitar ajustes/i }));
    await screen.findByText(/Comentário obrigatório/i);
    expect(budgetApi.requestCapexPlanChanges).not.toHaveBeenCalled();
  });

  it("conflito 409", async () => {
    vi.mocked(budgetApi.approveCapexPlan).mockRejectedValue(
      new HttpRequestError("conflito", 409, {
        code: "budget_capex_plan_version_conflict",
      }),
    );
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByRole("button", { name: /Aprovar/i });
    fireEvent.click(screen.getByRole("button", { name: /Aprovar/i }));
    await screen.findByText(/Recarregar dados/i);
  });

  it("403 sem permissão approve", async () => {
    permissionsState.profile = { permissions: [] };
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByText(/Acesso negado \(403\)/i);
  });

  it("modo somente leitura após decisão", async () => {
    vi.mocked(budgetApi.getCapexReviewDetail).mockResolvedValue({
      ...plan,
      status: "approved",
      version: 3,
    } as never);
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByText(/não está aguardando decisão|Novas decisões só são aceitas/i);
    expect(screen.queryByRole("button", { name: /^Aprovar$/i })).toBeNull();
  });
});
