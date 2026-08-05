import { cleanup, render, screen } from "@testing-library/react";
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

import { PersonnelReviewQueuePage } from "./PersonnelReviewQueuePage";
import * as budgetApi from "../api/budgetPlanningApi";

vi.mock("../api/budgetPlanningApi");

beforeEach(() => {
  permissionsState.profile = {
    permissions: ["planejamento-orcamentario.personnel.approve"],
  };
  permissionsState.loading = false;
  permissionsState.error = null;
  vi.mocked(budgetApi.fetchBudgetContext).mockResolvedValue({
    exercise: { id: "ex-1", year: 2027, name: "PO 2027", status: "open" },
    guidance: { current_version: 1, acknowledged: true },
    scopes: [],
    capabilities: {},
    modules_unlocked: true,
  } as never);
  vi.mocked(budgetApi.listPersonnelReviewQueue).mockResolvedValue({
    items: [],
    pagination: { page: 1, page_size: 20, total: 0, has_more: false },
  });
  window.history.pushState({}, "", "/apps/planejamento-orcamentario/pessoal/aprovacoes");
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("PersonnelReviewQueuePage", () => {
  it("403 sem approve", async () => {
    permissionsState.profile = { permissions: ["planejamento-orcamentario.personnel.view"] };
    render(<PersonnelReviewQueuePage />);
    expect(await screen.findByText(/Acesso negado/i)).toBeTruthy();
  });

  it("fila vazia", async () => {
    render(<PersonnelReviewQueuePage />);
    expect(await screen.findByText(/Nenhum orçamento na fila/i)).toBeTruthy();
  });

  it("lista item e link analisar", async () => {
    vi.mocked(budgetApi.listPersonnelReviewQueue).mockResolvedValue({
      items: [
        {
          id: "plan-1",
          exercise_id: "ex-1",
          unit_id: "01",
          area_id: "PROD",
          cost_center_id: "205",
          status: "submitted",
          version: 2,
          submitted_by: "u1",
          submitted_at: "2026-08-05T12:00:00Z",
          position_count: 2,
          totals: {
            headcount_dec_2025: 1,
            headcount_oct_2026: 2,
            headcount_forecast: 2,
            headcount_dec_2027: 4,
          },
          lines: [],
          incomplete_line_count: 0,
          is_complete: true,
        },
      ] as never[],
      pagination: { page: 1, page_size: 20, total: 1, has_more: false },
    });
    render(<PersonnelReviewQueuePage />);
    expect(await screen.findByText(/Filial 01 · 205/i)).toBeTruthy();
    const link = screen.getByRole("link", { name: /Analisar/i });
    expect(link.getAttribute("href")).toContain("/pessoal/aprovacoes/plan-1");
  });
});
