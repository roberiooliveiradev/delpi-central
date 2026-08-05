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
  profile: { permissions: ["planejamento-orcamentario.personnel.approve"] } as {
    permissions: string[];
  } | null,
  loading: false,
  error: null as string | null,
};

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: () => permissionsState,
}));

import { PersonnelReviewDetailPage } from "./PersonnelReviewDetailPage";
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
  position_count: 1,
  incomplete_line_count: 0,
  is_complete: true,
  totals: {
    headcount_dec_2025: 1,
    headcount_oct_2026: 1,
    headcount_forecast: 1,
    headcount_dec_2027: 2,
  },
  lines: [
    {
      id: "line-1",
      plan_id: "plan-1",
      position_name: "Analista",
      headcount_dec_2025: 1,
      headcount_oct_2026: 1,
      headcount_forecast: 1,
      headcount_dec_2027: 2,
      observations: "Obs",
      version: 1,
      is_active: true,
    },
  ],
};

beforeEach(() => {
  permissionsState.profile = {
    permissions: ["planejamento-orcamentario.personnel.approve"],
  };
  permissionsState.loading = false;
  permissionsState.error = null;
  vi.mocked(budgetApi.getPersonnelReviewDetail).mockResolvedValue(plan as never);
  vi.mocked(budgetApi.listPersonnelPlanHistory).mockResolvedValue({
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

describe("PersonnelReviewDetailPage", () => {
  it("detalhe somente leitura com linhas", async () => {
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    expect(await screen.findByText("Analista")).toBeTruthy();
    expect(screen.getByText("Obs")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Aprovar orçamento/i })).toBeTruthy();
  });

  it("comentário obrigatório em solicitar ajustes", async () => {
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    await screen.findByRole("button", { name: /Solicitar ajustes/i });
    fireEvent.click(screen.getByRole("button", { name: /Solicitar ajustes/i }));
    expect(await screen.findByText(/Comentário obrigatório/i)).toBeTruthy();
    expect(budgetApi.requestPersonnelPlanChanges).not.toHaveBeenCalled();
  });

  it("solicitar ajustes com comentário", async () => {
    vi.mocked(budgetApi.requestPersonnelPlanChanges).mockResolvedValue({
      ...plan,
      status: "changes_requested",
      version: 3,
      decision_comment: "Revise",
    } as never);
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    await screen.findByRole("button", { name: /Solicitar ajustes/i });
    fireEvent.change(screen.getByPlaceholderText(/Obrigatório/i), {
      target: { value: "Revise os totais" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Solicitar ajustes/i }));
    await waitFor(() => {
      expect(budgetApi.requestPersonnelPlanChanges).toHaveBeenCalledWith("plan-1", {
        version: 2,
        comment: "Revise os totais",
      });
    });
  });

  it("reprovação", async () => {
    vi.mocked(budgetApi.rejectPersonnelPlan).mockResolvedValue({
      ...plan,
      status: "rejected",
      version: 3,
    } as never);
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    await screen.findByRole("button", { name: /^Reprovar$/i });
    fireEvent.change(screen.getByPlaceholderText(/Obrigatório/i), {
      target: { value: "Fora do escopo" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^Reprovar$/i }));
    await waitFor(() => {
      expect(budgetApi.rejectPersonnelPlan).toHaveBeenCalled();
    });
    await screen.findByText(/Orçamento reprovado/i);
  });

  it("aprovação", async () => {
    vi.mocked(budgetApi.approvePersonnelPlan).mockResolvedValue({
      ...plan,
      status: "approved",
      version: 3,
    } as never);
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /Aprovar orçamento/i }));
    await waitFor(() => {
      expect(budgetApi.approvePersonnelPlan).toHaveBeenCalledWith("plan-1", {
        version: 2,
        comment: null,
      });
    });
  });

  it("segregação de funções", async () => {
    vi.mocked(budgetApi.approvePersonnelPlan).mockRejectedValue(
      new HttpRequestError("forbidden", 403, {
        code: "budget_personnel_approval_forbidden",
      }),
    );
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /Aprovar orçamento/i }));
    await screen.findByText(/não pode decidir sobre o próprio orçamento/i);
  });

  it("conflito de versão", async () => {
    vi.mocked(budgetApi.approvePersonnelPlan).mockRejectedValue(
      new HttpRequestError("conflito", 409, {
        code: "budget_personnel_plan_version_conflict",
      }),
    );
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    fireEvent.click(await screen.findByRole("button", { name: /Aprovar orçamento/i }));
    await screen.findByRole("button", { name: /Recarregar dados/i });
  });

  it("403 sem approve", async () => {
    permissionsState.profile = { permissions: [] };
    render(<PersonnelReviewDetailPage planId="plan-1" />);
    expect(await screen.findByText(/Acesso negado \(403\)/i)).toBeTruthy();
  });
});
