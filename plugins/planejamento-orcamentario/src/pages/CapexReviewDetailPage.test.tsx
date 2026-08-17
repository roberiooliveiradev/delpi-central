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
    function StateBox({ children }: { title?: string; children: ReactNode }) {
      return <div role="alert">{children}</div>;
    },
  createHostContainedModalShell:
    () =>
    function HostContainedDialog({
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
      justification: "Substituir equipamentos fora de garantia.",
      observations: "Priorizar a filial 02 no segundo semestre.",
      application: "TI / escritório",
      status: "draft",
      review_status: "pending",
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
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("CapexReviewDetailPage", () => {
  it("mostra grade gerencial com observações e decisão por investimento", async () => {
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByText(/Notebooks/);
    expect(screen.getAllByText(/Priorizar a filial 02/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Substituir equipamentos fora de garantia/i)).toBeTruthy();
    expect(screen.getByText(/Fornecedor X/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /^Aprovar$/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /^Reprovar$/i })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^Aprovar orçamento$/i })).toBeNull();
  });

  it("aprovação do investimento", async () => {
    vi.mocked(budgetApi.approveCapexInvestment).mockResolvedValue({
      ...plan,
      status: "approved",
      version: 3,
      investments: [{ ...plan.investments[0], review_status: "approved" }],
    } as never);
    render(<CapexReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /^Aprovar$/i }));
    await waitFor(() => {
      expect(budgetApi.approveCapexInvestment).toHaveBeenCalledWith("plan-1", "inv-1", {
        version: 2,
      });
    });
    await screen.findByText(/Investimento aprovado/i);
    expect(budgetApi.approveCapexPlan).not.toHaveBeenCalled();
  });

  it("reprovação sem justificativa", async () => {
    render(<CapexReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /^Reprovar$/i }));
    fireEvent.click(await screen.findByRole("button", { name: /Confirmar reprovação/i }));
    await screen.findByText(/Justificativa obrigatória/i);
    expect(budgetApi.rejectCapexInvestment).not.toHaveBeenCalled();
  });

  it("reprovação com justificativa", async () => {
    vi.mocked(budgetApi.rejectCapexInvestment).mockResolvedValue({
      ...plan,
      status: "rejected",
      version: 3,
      investments: [
        {
          ...plan.investments[0],
          review_status: "rejected",
          review_comment: "Fora do teto",
        },
      ],
    } as never);
    render(<CapexReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /^Reprovar$/i }));
    fireEvent.change(await screen.findByPlaceholderText(/Explique o motivo/i), {
      target: { value: "Fora do teto" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Confirmar reprovação/i }));
    await waitFor(() => {
      expect(budgetApi.rejectCapexInvestment).toHaveBeenCalledWith("plan-1", "inv-1", {
        version: 2,
        comment: "Fora do teto",
      });
    });
  });

  it("ajustes sem comentário", async () => {
    render(<CapexReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /Solicitar ajustes/i }));
    await screen.findByText(/Comentário obrigatório/i);
    expect(budgetApi.requestCapexPlanChanges).not.toHaveBeenCalled();
  });

  it("conflito 409", async () => {
    vi.mocked(budgetApi.approveCapexInvestment).mockRejectedValue(
      new HttpRequestError("conflito", 409, {
        code: "budget_capex_plan_version_conflict",
      }),
    );
    render(<CapexReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /^Aprovar$/i }));
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
      investments: [{ ...plan.investments[0], review_status: "approved" }],
    } as never);
    render(<CapexReviewDetailPage planId="plan-1" />);
    await screen.findByText(/não está aguardando decisão|Novas decisões só são aceitas/i);
    expect(screen.queryByRole("button", { name: /^Aprovar$/i })).toBeNull();
  });
});
