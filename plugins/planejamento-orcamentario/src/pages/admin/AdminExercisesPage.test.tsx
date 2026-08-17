import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

vi.mock("../../hooks/usePermissions", () => ({
  usePermissions: () => ({
    profile: {
      permissions: [
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.admin",
      ],
    },
    loading: false,
    error: null,
  }),
}));

import { AdminExercisesPage } from "./AdminExercisesPage";
import * as budgetApi from "../../api/budgetPlanningApi";

vi.mock("../../api/budgetPlanningApi");

const exercise = {
  id: "ex-1",
  year: 2027,
  name: "Planejamento Orçamentário Delpi - 2027",
  status: "open" as const,
  is_active: true,
  filling_starts_at: "2026-09-01",
  deadline_at: "2026-12-15",
};

describe("AdminExercisesPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    vi.mocked(budgetApi.listAdminExercises).mockResolvedValue([exercise]);
    vi.mocked(budgetApi.createAdminExercise).mockResolvedValue({
      ...exercise,
      id: "ex-2",
      year: 2028,
      status: "draft",
      is_active: false,
      name: "PO 2028",
    });
    vi.mocked(budgetApi.transitionAdminExercise).mockResolvedValue(exercise);
    vi.mocked(budgetApi.updateAdminExercise).mockResolvedValue(exercise);
  });

  it("exibe hero do ciclo ativo e lista com ações", async () => {
    render(<AdminExercisesPage />);
    expect(
      await screen.findByRole("button", { name: /Iniciar encerramento/i }),
    ).toBeTruthy();
    expect(screen.getByRole("heading", { level: 2, name: "2027" })).toBeTruthy();
    expect(screen.getAllByText("Planejamento Orçamentário Delpi - 2027").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText("Aberto")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Novo exercício/i })).toBeTruthy();
  });

  it("abre formulário e cria rascunho", async () => {
    render(<AdminExercisesPage />);
    await screen.findByRole("button", { name: /Iniciar encerramento/i });
    fireEvent.click(screen.getByRole("button", { name: /Novo exercício/i }));
    const form = await screen.findByTestId("section-Novo exercício");
    fireEvent.change(within(form).getByLabelText("Ano"), { target: { value: "2028" } });
    fireEvent.change(within(form).getByLabelText("Nome"), {
      target: { value: "PO 2028" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /Criar rascunho/i }));
    await waitFor(() => {
      expect(budgetApi.createAdminExercise).toHaveBeenCalledWith(
        expect.objectContaining({ year: 2028, name: "PO 2028" }),
      );
    });
  });
});
