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
    function HostContainedModal({
      open,
      title,
      description,
      onClose,
      footer,
      children,
    }: {
      open: boolean;
      title: ReactNode;
      description?: ReactNode;
      onClose: () => void;
      footer?: ReactNode;
      children?: ReactNode;
    }) {
      if (!open) return null;
      return (
        <div role="dialog" aria-modal="true" aria-label={String(title)}>
          {description ? <p>{description}</p> : null}
          <button type="button" aria-label="Fechar" onClick={onClose}>
            Fechar
          </button>
          {children}
          {footer}
        </div>
      );
    },
}));

import { CapexPlanWorkflowPanel } from "./CapexPlanWorkflowPanel";
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
  updated_at: "2026-08-05T10:00:00Z",
};

const investment = {
  id: "inv-1",
  exercise_id: "ex-1",
  unit_id: "01",
  cost_center_id: "205",
  description: "Notebooks",
  estimated_amount: "1000.00",
  currency: "BRL",
  status: "draft",
  version: 1,
  is_complete: true,
  missing_fields: [],
};

beforeEach(() => {
  vi.mocked(budgetApi.resolveCapexPlan).mockResolvedValue(planDraft as never);
  vi.mocked(budgetApi.listCapexInvestments).mockResolvedValue({
    items: [investment as never],
    pagination: { page: 1, page_size: 500, total: 1, has_more: false },
  });
  vi.mocked(budgetApi.listCapexPlanHistory).mockResolvedValue({
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
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function waitSubmitButton() {
  return screen.findByRole("button", { name: /Enviar planejamento para aprovação/i });
}

async function confirmSubmitDialog() {
  expect(await screen.findByRole("dialog", { name: /Enviar para aprovação/i })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /Sim, enviar/i }));
}

describe("CapexPlanWorkflowPanel", () => {
  it("resolve plano e mostra resumo", async () => {
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        areaId="PROD"
        canSubmit
      />,
    );
    await waitSubmitButton();
    expect(budgetApi.resolveCapexPlan).toHaveBeenCalledWith(
      { exercise_id: "ex-1", cost_center_id: "205", unit_id: "01" },
      expect.anything(),
    );
    expect(screen.getByText("Planejamento do centro de custo")).toBeTruthy();
    expect(screen.getByText(/Histórico do workflow/i)).toBeTruthy();
    expect(screen.getByText(/Planejamento criado/i)).toBeTruthy();
  });

  it("variant cockpit: métricas e CTA sem grade de metadados", async () => {
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        unitId="01"
        canSubmit
        variant="cockpit"
        cockpitHero={{
          title: "DEPARTAMENTO DE RH",
          locationLabel: "Rio Bananal/ES",
          cycleYear: "2027",
        }}
      />,
    );
    await screen.findByRole("button", { name: /Enviar para aprovação/i });
    expect(screen.getByRole("heading", { name: "DEPARTAMENTO DE RH" })).toBeTruthy();
    expect(screen.getByText(/Elaboração · 2027/i)).toBeTruthy();
    expect(screen.getByText("Rio Bananal/ES")).toBeTruthy();
    expect(screen.getByText("Rascunho")).toBeTruthy();
    expect(screen.getByText("Incompletos")).toBeTruthy();
    expect(screen.getByText("Valor total")).toBeTruthy();
    expect(screen.queryByText("Tudo pronto para enviar")).toBeNull();
    expect(screen.queryByText("Planejamento do centro de custo")).toBeNull();
    expect(screen.queryByText(/Histórico do workflow/i)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Ver histórico/i }));
    expect(screen.getByText(/Planejamento criado/i)).toBeTruthy();
  });

  it("submissão válida atualiza status", async () => {
    vi.mocked(budgetApi.submitCapexPlan).mockResolvedValue({
      ...planDraft,
      status: "submitted",
      version: 2,
      submitted_at: "2026-08-05T12:00:00Z",
    } as never);
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        canSubmit
      />,
    );
    fireEvent.click(await waitSubmitButton());
    await confirmSubmitDialog();
    await waitFor(() => {
      expect(budgetApi.submitCapexPlan).toHaveBeenCalledWith("plan-1", { version: 1 });
    });
    await screen.findByText(/Edição bloqueada até a decisão/i);
  });

  it("cancelar no modal não envia o planejamento", async () => {
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        canSubmit
      />,
    );
    fireEvent.click(await waitSubmitButton());
    expect(await screen.findByRole("dialog", { name: /Enviar para aprovação/i })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /^Cancelar$/i }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: /Enviar para aprovação/i })).toBeNull();
    });
    expect(budgetApi.submitCapexPlan).not.toHaveBeenCalled();
  });

  it("plano incompleto lista links de pendências", async () => {
    vi.mocked(budgetApi.submitCapexPlan).mockRejectedValue(
      new HttpRequestError("incompleto", 422, {
        code: "budget_capex_plan_incomplete",
        meta: {
          incomplete_investments: [
            {
              id: "inv-1",
              description: "Notebooks",
              missing_fields: ["category_id"],
            },
          ],
        },
      }),
    );
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        canSubmit
      />,
    );
    fireEvent.click(await waitSubmitButton());
    await confirmSubmitDialog();
    await screen.findByRole("link", { name: /Notebooks/i });
    expect(screen.getByText(/pendências:/i)).toBeTruthy();
  });

  it("bloqueio visual após submissão (sem botão de envio)", async () => {
    vi.mocked(budgetApi.resolveCapexPlan).mockResolvedValue({
      ...planDraft,
      status: "submitted",
      version: 2,
    } as never);
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        canSubmit
      />,
    );
    await screen.findByText(/está em análise/i);
    expect(
      screen.queryByRole("button", { name: /Enviar planejamento para aprovação/i }),
    ).toBeNull();
  });

  it("ajustes solicitados destacam comentário e liberam reenvio", async () => {
    vi.mocked(budgetApi.resolveCapexPlan).mockResolvedValue({
      ...planDraft,
      status: "changes_requested",
      version: 3,
      decision_comment: "Revise os valores",
    } as never);
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        canSubmit
      />,
    );
    await screen.findByText(/Ajustes solicitados pelo aprovador/i);
    expect(screen.getAllByText("Revise os valores").length).toBeGreaterThan(0);
    expect(await waitSubmitButton()).toBeTruthy();
  });

  it("sem permissão submit oculta botão", async () => {
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        canSubmit={false}
      />,
    );
    await screen.findByText(/não possui permissão para submeter/i);
    expect(
      screen.queryByRole("button", { name: /Enviar planejamento para aprovação/i }),
    ).toBeNull();
  });

  it("conflito 409 oferece recarregar", async () => {
    vi.mocked(budgetApi.submitCapexPlan).mockRejectedValue(
      new HttpRequestError("conflito", 409, {
        code: "budget_capex_plan_version_conflict",
      }),
    );
    render(
      <CapexPlanWorkflowPanel
        exercise={exercise}
        costCenterId="205"
        canSubmit
      />,
    );
    fireEvent.click(await waitSubmitButton());
    await confirmSubmitDialog();
    await screen.findByRole("button", { name: /Recarregar dados/i });
  });
});
