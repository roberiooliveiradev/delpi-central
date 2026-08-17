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

import { CapexReviewQueuePage } from "./CapexReviewQueuePage";
import * as budgetApi from "../api/budgetPlanningApi";

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
  submitted_by_name: "Owner",
  submitted_at: "2026-08-05T12:00:00Z",
};

beforeEach(() => {
  permissionsState.profile = {
    permissions: ["planejamento-orcamentario.capex.approve"],
  };
  permissionsState.loading = false;
  permissionsState.error = null;
  vi.mocked(budgetApi.fetchBudgetContext).mockResolvedValue({
    exercise: { id: "ex-1", year: 2027, name: "PO 2027", status: "open" },
    modules_unlocked: true,
    guidance: { current_version: 1, acknowledged: true },
    scopes: [],
    capabilities: {
      access: true,
      guidance_view: true,
      guidance_manage: false,
      scopes_manage: false,
      admin: false,
    },
  } as never);
  vi.mocked(budgetApi.listCapexReviewQueue).mockResolvedValue({
    items: [plan as never],
    pagination: { page: 1, page_size: 20, total: 1, has_more: false },
  });
  vi.mocked(budgetApi.getCapexReviewDetail).mockResolvedValue({
    ...plan,
    investments: [
      {
        id: "inv-1",
        status: "draft",
        estimated_amount: "1500.00",
        currency: "BRL",
        is_complete: true,
        missing_fields: [],
      },
    ],
  } as never);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("CapexReviewQueuePage", () => {
  it("nega acesso sem permissão approve", async () => {
    permissionsState.profile = { permissions: ["planejamento-orcamentario.access"] };
    render(<CapexReviewQueuePage />);
    await screen.findByText(/Acesso negado/i);
  });

  it(
    "lista fila paginada com ação analisar",
    async () => {
      render(<CapexReviewQueuePage />);
      await screen.findByText(/Filial 01 · 205/);
      expect(screen.getByText(/Owner/)).toBeTruthy();
      expect(screen.getByRole("link", { name: /Analisar/i })).toBeTruthy();
    },
    15000,
  );

  it(
    "aplica filtros",
    async () => {
      render(<CapexReviewQueuePage />);
      await screen.findByText(/Filial 01 · 205/);
      fireEvent.change(screen.getByPlaceholderText("Ex.: 205"), {
        target: { value: "210" },
      });
      await waitFor(() => {
        expect(budgetApi.listCapexReviewQueue).toHaveBeenCalled();
      });
      const lastCall = vi.mocked(budgetApi.listCapexReviewQueue).mock.calls.at(-1)?.[0];
      expect(lastCall?.cost_center_id).toBe("210");
    },
    15000,
  );
});
