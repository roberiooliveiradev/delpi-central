import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/budgetPlanningApi", () => ({
  fetchBudgetContext: vi.fn(),
}));

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: vi.fn(),
}));

vi.mock("@delpi/plugin-ui/index", () => ({
  createDashboardSectionCard: () =>
    function MockSectionCard({
      title,
      children,
    }: {
      title?: string;
      children?: React.ReactNode;
    }) {
      return (
        <section>
          {title ? <h2>{title}</h2> : null}
          {children}
        </section>
      );
    },
  createDashboardLoadingActivityCard: () =>
    function MockLoading({ title }: { title?: string }) {
      return <div>{title ?? "loading"}</div>;
    },
  createDashboardStateBox: () =>
    function MockStateBox({ children }: { children?: React.ReactNode }) {
      return <div role="alert">{children}</div>;
    },
  sectionCardPacBemClasses: () => ({}),
}));

import { fetchBudgetContext } from "../api/budgetPlanningApi";
import { usePermissions } from "../hooks/usePermissions";
import { HomePage } from "./HomePage";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  vi.mocked(usePermissions).mockReturnValue({
    profile: {
      id: "u1",
      name: "Michael Silva",
      email: "michael@example.com",
      permissions: [
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.capex.submit",
        "planejamento-orcamentario.personnel.view",
        "planejamento-orcamentario.personnel.edit",
      ],
    },
    loading: false,
    error: null,
    reload: vi.fn(),
  } as never);
});

describe("HomePage", () => {
  it("exibe launchpad liberado com orçamento por centro", async () => {
    vi.mocked(fetchBudgetContext).mockResolvedValue({
      exercise: {
        id: "ex-1",
        name: "Planejamento Orçamentário Delpi - 2027",
        year: 2027,
        status: "open",
        filling_starts_at: "2026-09-01",
        deadline_at: "2026-12-15",
      },
      guidance: {
        current_version: 1,
        acknowledged: true,
      },
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

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText("2027")).toBeTruthy();
    });
    const greetingName = document.querySelector(".po-home__greeting-name");
    expect(greetingName?.textContent).toBe("Michael");
    expect(screen.getByText("Elaboração liberada")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Abrir orçamento do centro/i })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 3, name: "Apps" })).toBeTruthy();
    expect(screen.getByText("Orçamento")).toBeTruthy();
    expect(screen.getByText("Receita")).toBeTruthy();
    expect(screen.getByText("Em breve")).toBeTruthy();
    expect(screen.getByLabelText("Aplicativos do planejamento")).toBeTruthy();
  });

  it("prioriza leitura das orientações quando pendente", async () => {
    vi.mocked(fetchBudgetContext).mockResolvedValue({
      exercise: {
        id: "ex-1",
        name: "Ciclo 2027",
        year: 2027,
        status: "open",
        filling_starts_at: "2026-09-01",
        deadline_at: "2026-12-15",
      },
      guidance: {
        current_version: 1,
        acknowledged: false,
      },
      scopes: [],
      capabilities: {
        access: true,
        guidance_view: true,
        guidance_manage: false,
        scopes_manage: false,
        admin: false,
      },
      modules_unlocked: false,
      reason: null,
    } as never);

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText("Leitura pendente")).toBeTruthy();
    });
    expect(screen.getByRole("link", { name: /Ler orientações/i })).toBeTruthy();
    expect(screen.getAllByText("Bloqueado").length).toBeGreaterThanOrEqual(1);
  });
});
