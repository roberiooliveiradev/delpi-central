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

import { PersonnelPlanWorkflowPanel } from "./PersonnelPlanWorkflowPanel";
import * as budgetApi from "../api/budgetPlanningApi";
import { HttpRequestError } from "../api/httpClient";

vi.mock("../api/budgetPlanningApi");

const exercise = {
  id: "ex-1",
  year: 2027,
  name: "PO 2027",
  status: "open" as const,
};

const planDraft = {
  id: "plan-1",
  exercise_id: "ex-1",
  unit_id: "01",
  area_id: "PROD",
  cost_center_id: "205",
  status: "draft",
  version: 1,
  position_count: 1,
  incomplete_line_count: 0,
  is_complete: true,
  totals: {
    headcount_dec_2025: 1,
    headcount_oct_2026: 2,
    headcount_forecast: 2,
    headcount_dec_2027: 3,
  },
  lines: [],
};

beforeEach(() => {
  vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue(planDraft as never);
  vi.mocked(budgetApi.listPersonnelPlanHistory).mockResolvedValue({
    items: [
      {
        id: "h1",
        plan_id: "plan-1",
        action: "created",
        previous_status: null,
        new_status: "draft",
        comment: null,
        actor_sub: "u1",
        actor_name: "User",
        created_at: "2026-08-05T09:00:00Z",
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

async function waitSubmitButton() {
  return screen.findByRole("button", { name: /Enviar para aprovação/i });
}

describe("PersonnelPlanWorkflowPanel", () => {
  it("mostra status, totais e histórico", async () => {
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        areaId="PROD"
        canSubmit
      />,
    );
    await waitSubmitButton();
    expect(screen.getAllByText("Rascunho").length).toBeGreaterThan(0);
    expect(screen.getByText(/Histórico do workflow/i)).toBeTruthy();
    expect(screen.getByText(/Planejamento criado/i)).toBeTruthy();
  });

  it("submissão válida com confirmação", async () => {
    vi.mocked(budgetApi.submitPersonnelPlan).mockResolvedValue({
      ...planDraft,
      status: "submitted",
      version: 2,
      submitted_by: "u1",
      submitted_at: "2026-08-05T12:00:00Z",
    } as never);
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit
      />,
    );
    fireEvent.click(await waitSubmitButton());
    expect(window.confirm).toHaveBeenCalled();
    await waitFor(() => {
      expect(budgetApi.submitPersonnelPlan).toHaveBeenCalledWith("plan-1", {
        version: 1,
      });
    });
    await screen.findByText(/grade está em somente leitura/i);
  });

  it("plano incompleto lista cargos e campos pendentes", async () => {
    vi.mocked(budgetApi.submitPersonnelPlan).mockRejectedValue(
      new HttpRequestError("incompleto", 422, {
        code: "budget_personnel_plan_incomplete",
        meta: {
          incomplete_lines: [
            {
              id: "line-1",
              position_name: "Analista",
              missing_fields: ["headcount_oct_2026", "headcount_forecast"],
            },
          ],
        },
      }),
    );
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit
        onFocusLine={vi.fn()}
      />,
    );
    fireEvent.click(await waitSubmitButton());
    await screen.findByText(/Linhas incompletas/i);
    expect(screen.getByText(/Analista/i)).toBeTruthy();
    expect(screen.getByText(/pendências: Out\/2026, Previsto/i)).toBeTruthy();
  });

  it("bloqueio visual após envio", async () => {
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...planDraft,
      status: "submitted",
      version: 2,
    } as never);
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit
      />,
    );
    await screen.findByText(/está em análise/i);
    expect(screen.queryByRole("button", { name: /Enviar para aprovação/i })).toBeNull();
  });

  it("ajustes solicitados e reenvio", async () => {
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...planDraft,
      status: "changes_requested",
      version: 3,
      decision_comment: "Ajustar headcount",
      reviewed_by: "approver",
      reviewed_at: "2026-08-05T13:00:00Z",
    } as never);
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit
      />,
    );
    await screen.findByText(/Ajustes solicitados pelo aprovador/i);
    expect(screen.getAllByText(/Ajustar headcount/i).length).toBeGreaterThan(0);
    expect(await waitSubmitButton()).toBeTruthy();
  });

  it("sem permissão submit", async () => {
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit={false}
      />,
    );
    await screen.findByText(/não possui permissão para submeter/i);
    expect(screen.queryByRole("button", { name: /Enviar para aprovação/i })).toBeNull();
  });

  it("conflito de versão preserva opção de recarregar", async () => {
    vi.mocked(budgetApi.submitPersonnelPlan).mockRejectedValue(
      new HttpRequestError("conflito", 409, {
        code: "budget_personnel_plan_version_conflict",
      }),
    );
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit
      />,
    );
    fireEvent.click(await waitSubmitButton());
    await screen.findByRole("button", { name: /Recarregar dados/i });
  });

  it("bloqueia envio com autosave pendente", async () => {
    render(
      <PersonnelPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit
        hasPendingLineWork
      />,
    );
    await screen.findByText(/Aguarde o salvamento/i);
    expect(screen.queryByRole("button", { name: /Enviar para aprovação/i })).toBeNull();
  });
});
