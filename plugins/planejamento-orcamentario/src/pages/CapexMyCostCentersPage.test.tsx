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
  createHostContainedModalShell:
    () =>
    function HostContainedModal({
      open,
      title,
      onClose,
      children,
    }: {
      open: boolean;
      title: ReactNode;
      onClose: () => void;
      children?: ReactNode;
    }) {
      if (!open) return null;
      return (
        <div role="dialog" aria-modal="true" aria-label={String(title)}>
          <button type="button" aria-label="Fechar" onClick={onClose}>
            Fechar
          </button>
          {children}
        </div>
      );
    },
}));

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: () => ({
    profile: {
      permissions: [
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.capex.submit",
      ],
    },
    loading: false,
    error: null,
  }),
}));

import { CapexMyCostCentersPage } from "./CapexMyCostCentersPage";
import * as budgetApi from "../api/budgetPlanningApi";
import { HttpRequestError } from "../api/httpClient";

vi.mock("../api/budgetPlanningApi");

const exercise = {
  id: "ex-2027",
  year: 2027,
  name: "PO 2027",
  status: "open" as const,
  is_active: true,
};

const responsibility = {
  id: "r1",
  exercise_id: "ex-2027",
  module: "capex",
  user_sub: "user-1",
  unit_id: "01",
  area_id: "PROD",
  cost_center_id: "205",
  responsibility_type: "owner" as const,
  is_active: true,
};

const investment = {
  id: "inv-1",
  exercise_id: "ex-2027",
  unit_id: "01",
  area_id: "PROD",
  cost_center_id: "205",
  category_id: "cat-1",
  description: "Notebooks",
  estimated_amount: "15000.00",
  currency: "BRL",
  required_date: "2027-06-01",
  priority: "2",
  origin: "national",
  status: "draft",
  version: 1,
  is_complete: false,
  missing_fields: ["category_id"],
  updated_at: "2026-08-05T12:00:00Z",
};

function mockContext(overrides: Record<string, unknown> = {}) {
  vi.mocked(budgetApi.fetchBudgetContext).mockResolvedValue({
    exercise,
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
    ...overrides,
  } as never);
}

beforeEach(() => {
  mockContext();
  vi.mocked(budgetApi.fetchMyCapexResponsibilities).mockResolvedValue({
    user_sub: "user-1",
    module: "capex",
    items: [responsibility],
  });
  vi.mocked(budgetApi.listActiveCapexCategories).mockResolvedValue({
    items: [{ id: "cat-1", code: "FERRAMENTAS", name: "Ferramentas", display_order: 20, is_active: true, is_system_default: true }],
  });
  vi.mocked(budgetApi.listCapexInvestments).mockResolvedValue({
    items: [investment],
    pagination: { page: 1, page_size: 20, total: 1, has_more: false },
  });
  vi.mocked(budgetApi.deleteCapexInvestment).mockResolvedValue({
    ...investment,
    status: "archived",
  });
  vi.mocked(budgetApi.resolveCapexPlan).mockResolvedValue({
    id: "plan-1",
    exercise_id: "ex-2027",
    unit_id: "01",
    area_id: "PROD",
    cost_center_id: "205",
    status: "draft",
    version: 1,
  } as never);
  vi.mocked(budgetApi.listCapexPlanHistory).mockResolvedValue({ items: [] });
  window.history.pushState({}, "", "/apps/planejamento-orcamentario/capex");
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("CapexMyCostCentersPage", () => {
  it("lista centros autorizados", async () => {
    render(<CapexMyCostCentersPage />);
    await screen.findByText(/autorizado a elaborar/i);
    expect(screen.getByText(/Filial 01 · 205/)).toBeTruthy();
  });

  it("mostra loading inicial", () => {
    vi.mocked(budgetApi.fetchBudgetContext).mockImplementation(
      () => new Promise(() => undefined) as never,
    );
    render(<CapexMyCostCentersPage />);
    expect(screen.getByText(/Carregando módulo CAPEX/i)).toBeTruthy();
  });

  it("lista vazia de centros", async () => {
    vi.mocked(budgetApi.fetchMyCapexResponsibilities).mockResolvedValue({
      user_sub: "user-1",
      module: "capex",
      items: [],
    });
    render(<CapexMyCostCentersPage />);
    await screen.findByText(/ainda não foi vinculado/i);
  });

  it("orientação pendente", async () => {
    mockContext({ modules_unlocked: false, guidance: { current_version: 1, acknowledged: false } });
    render(<CapexMyCostCentersPage />);
    await screen.findByText(/Confirme a leitura das orientações/i);
  });

  it("erro 401", async () => {
    vi.mocked(budgetApi.fetchBudgetContext).mockRejectedValue(
      new HttpRequestError("unauthorized", 401),
    );
    render(<CapexMyCostCentersPage />);
    await screen.findByText(/Sessão expirada \(401\)/i);
  });

  it("erro 403", async () => {
    vi.mocked(budgetApi.fetchBudgetContext).mockRejectedValue(
      new HttpRequestError("forbidden", 403),
    );
    render(<CapexMyCostCentersPage />);
    await screen.findByText(/Acesso negado \(403\)/i);
  });

  it("carrega investimentos ao selecionar centro e aplica filtro", async () => {
    window.history.pushState(
      {},
      "",
      "/apps/planejamento-orcamentario/capex?cost_center_id=205&unit_id=01",
    );
    render(<CapexMyCostCentersPage />);
    await screen.findByText("Notebooks");
    expect(budgetApi.listCapexInvestments).toHaveBeenCalledWith(
      expect.objectContaining({ cost_center_id: "205", unit_id: "01", page: 1 }),
      expect.anything(),
    );
    const section = screen.getByTestId("section-Investimentos — Filial 01 · 205");
    fireEvent.change(within(section).getByLabelText("Prioridade"), {
      target: { value: "2" },
    });
    await waitFor(() => {
      expect(budgetApi.listCapexInvestments).toHaveBeenCalledWith(
        expect.objectContaining({ priority: "2" }),
        expect.anything(),
      );
    });
  });

  it("exibe campos pendentes do rascunho incompleto", async () => {
    window.history.pushState(
      {},
      "",
      "/apps/planejamento-orcamentario/capex?cost_center_id=205",
    );
    render(<CapexMyCostCentersPage />);
    await screen.findByText("Notebooks");
    expect(screen.getByText(/Pendências:.*Categoria/i)).toBeTruthy();
  });

  it("estado vazio da listagem de investimentos", async () => {
    window.history.pushState(
      {},
      "",
      "/apps/planejamento-orcamentario/capex?cost_center_id=205",
    );
    vi.mocked(budgetApi.listCapexInvestments).mockResolvedValue({
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, has_more: false },
    });
    render(<CapexMyCostCentersPage />);
    await screen.findByText(/Nenhum investimento ainda/i);
  });

  it("abre modal de novo investimento sem sair do centro", async () => {
    window.history.pushState(
      {},
      "",
      "/apps/planejamento-orcamentario/capex?cost_center_id=205&unit_id=01",
    );
    vi.mocked(budgetApi.listCapexInvestments).mockResolvedValue({
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, has_more: false },
    });
    render(<CapexMyCostCentersPage />);
    await screen.findByText(/Nenhum investimento ainda/i);
    const createButtons = screen.getAllByRole("button", { name: /Novo investimento/i });
    fireEvent.click(createButtons[0]!);
    const dialog = await screen.findByRole("dialog", { name: /Novo investimento/i });
    expect(dialog).toBeTruthy();
    await within(dialog).findByLabelText(/Categoria de investimento/i);
    expect(window.location.pathname).toContain("/capex");
    expect(window.location.pathname).not.toContain("/investimentos/novo");
  });

  it("exclui investimento com confirmação", async () => {
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
    window.history.pushState(
      {},
      "",
      "/apps/planejamento-orcamentario/capex?cost_center_id=205",
    );
    render(<CapexMyCostCentersPage />);
    await screen.findByText("Notebooks");
    fireEvent.click(screen.getByRole("button", { name: /Excluir/i }));
    await waitFor(() => {
      expect(budgetApi.deleteCapexInvestment).toHaveBeenCalledWith("inv-1");
    });
  });
});
